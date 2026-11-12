"""Uploaders + stats readers for YouTube Shorts, Instagram Reels, Facebook Page Reels and TikTok (inbox draft)."""
import json
import math
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "05_Work" / "autopost"
STATE.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- config
def env():
    vals = dict(os.environ)
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def set_env(key, value):
    p = ROOT / ".env"
    lines = p.read_text(encoding="utf-8-sig").splitlines() if p.exists() else []
    lines = [l for l in lines if not l.strip().startswith(key + "=")] + [f"{key}={value}"]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


GV = lambda: env().get("GRAPH_VERSION", "v24.0")  # noqa: E731


class Skip(Exception):
    """Platform not configured - skip without failing the run."""


# ---------------------------------------------------------------- YouTube
YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly",
             "https://www.googleapis.com/auth/youtube.force-ssl"]
YT_TOKEN = STATE / "youtube_token.json"


def yt_client(interactive=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    secret = ROOT / env().get("YT_CLIENT_SECRET", "client_secret.json")
    creds = Credentials.from_authorized_user_file(str(YT_TOKEN), YT_SCOPES) if YT_TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        YT_TOKEN.write_text(creds.to_json())
    if not creds or not creds.valid:
        if not interactive:
            raise Skip("YouTube not authorised - run: python Tools/autopost/post.py --auth youtube")
        if not secret.exists():
            raise Skip(f"missing {secret.name} (Google Cloud OAuth desktop client)")
        from google_auth_oauthlib.flow import InstalledAppFlow
        creds = InstalledAppFlow.from_client_secrets_file(str(secret), YT_SCOPES).run_local_server(port=0)
        YT_TOKEN.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def yt_upload(path, title, description, tags, comment=None):
    from googleapiclient.http import MediaFileUpload
    yt = yt_client()
    body = {"snippet": {"title": title[:100], "description": description[:4900], "tags": tags, "categoryId": "19",
                        "defaultLanguage": "ur", "defaultAudioLanguage": "ur"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(path), chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    if comment:
        try:
            yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {
                "snippet": {"textOriginal": comment}}}}).execute()
        except Exception as e:  # comments can be disabled on fresh Shorts for a few minutes
            print("   (pinned comment skipped:", str(e)[:120], ")")
    return {"id": vid, "url": f"https://youtube.com/shorts/{vid}"}


def yt_stats(ids):
    if not ids:
        return {}
    yt = yt_client()
    out = {}
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute()
        for it in r.get("items", []):
            s = it["statistics"]
            out[it["id"]] = {"views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                             "comments": int(s.get("commentCount", 0))}
    return out


# ---------------------------------------------------------------- Meta (Instagram + Facebook)
META_CACHE = STATE / "meta_ids.json"


def meta():
    """Returns (page_token, ig_user_id, page_id). Accepts either META_PAGE_TOKEN or a never-expiring
    META_SYSTEM_TOKEN (Business portfolio system user); Page/IG ids and the Page token are discovered automatically."""
    e = env()
    tok = e.get("META_PAGE_TOKEN") or e.get("META_SYSTEM_TOKEN")
    if not tok:
        raise Skip("META_SYSTEM_TOKEN missing in .env")
    cache = json.loads(META_CACHE.read_text()) if META_CACHE.exists() else {}
    if cache.get("src") == tok[-12:] and cache.get("page_token"):
        return cache["page_token"], e.get("IG_USER_ID") or cache.get("ig"), e.get("FB_PAGE_ID") or cache.get("page")
    g = f"https://graph.facebook.com/{GV()}"
    pages = _g("GET", f"{g}/me/accounts", params={"fields": "id,name,access_token,instagram_business_account{id,username}",
                                                   "access_token": tok}).get("data", [])
    want = e.get("FB_PAGE_ID")
    page = next((p for p in pages if p["id"] == want), None) or \
        next((p for p in pages if "nomad" in p["name"].lower()), None) or (pages[0] if pages else None)
    if not page:   # token is already a Page token
        me = _g("GET", f"{g}/me", params={"fields": "id,name,instagram_business_account{id,username}", "access_token": tok})
        page = dict(me, access_token=tok)
    ig = (page.get("instagram_business_account") or {}).get("id")
    cache = {"src": tok[-12:], "page_token": page["access_token"], "page": page["id"], "page_name": page.get("name"),
             "ig": ig, "ig_username": (page.get("instagram_business_account") or {}).get("username")}
    META_CACHE.write_text(json.dumps(cache, indent=1))
    return cache["page_token"], e.get("IG_USER_ID") or ig, e.get("FB_PAGE_ID") or page["id"]


def _g(method, url, **kw):
    r = requests.request(method, url, timeout=600, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code} {r.text[:400]}")
    return r.json()


def ig_upload(path, caption):
    """Instagram's upload server sometimes answers ProcessingFailedError at random; retry with a fresh container."""
    last = None
    for attempt in range(3):
        try:
            return _ig_upload_once(path, caption)
        except RuntimeError as e:
            last = e
            if "ProcessingFailedError" not in str(e) and "processing error" not in str(e):
                raise
            time.sleep(20 * (attempt + 1))
    raise last


def _ig_upload_once(path, caption):
    tok, ig, _ = meta()
    if not ig:
        raise Skip("IG_USER_ID missing in .env")
    g = f"https://graph.facebook.com/{GV()}"
    c = _g("POST", f"{g}/{ig}/media", data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                            "share_to_feed": "true", "access_token": tok})
    cid = c["id"]
    data = Path(path).read_bytes()                # whole body with an exact Content-Length (streamed uploads fail more often)
    _g("POST", f"https://rupload.facebook.com/ig-api-upload/{GV()}/{cid}",
       headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(len(data)),
                "Content-Type": "application/octet-stream"}, data=data)
    for _ in range(90):                          # wait for Instagram to process (up to ~15 min)
        st = _g("GET", f"{g}/{cid}", params={"fields": "status_code,status", "access_token": tok})
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"IG processing error: {st}")
        time.sleep(10)
    m = _g("POST", f"{g}/{ig}/media_publish", data={"creation_id": cid, "access_token": tok})
    link = _g("GET", f"{g}/{m['id']}", params={"fields": "permalink", "access_token": tok}).get("permalink")
    return {"id": m["id"], "url": link}


def ig_story(path=None, image_url=None):
    """Instagram Story: a reel video (resumable upload) or a carousel cover image (public URL)."""
    tok, ig, _ = meta()
    g = f"https://graph.facebook.com/{GV()}"
    if image_url:
        c = _g("POST", f"{g}/{ig}/media", data={"media_type": "STORIES", "image_url": image_url, "access_token": tok})
    else:
        c = _g("POST", f"{g}/{ig}/media", data={"media_type": "STORIES", "upload_type": "resumable", "access_token": tok})
        with open(path, "rb") as fh:
            _g("POST", f"https://rupload.facebook.com/ig-api-upload/{GV()}/{c['id']}",
               headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(Path(path).stat().st_size)}, data=fh)
    for _ in range(60):
        st = _g("GET", f"{g}/{c['id']}", params={"fields": "status_code", "access_token": tok})
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"IG story processing error: {st}")
        time.sleep(5)
    m = _g("POST", f"{g}/{ig}/media_publish", data={"creation_id": c["id"], "access_token": tok})
    return {"id": m["id"]}


def fb_story(path):
    """Facebook Page Story from a reel video."""
    tok, _, page = meta()
    g = f"https://graph.facebook.com/{GV()}"
    s = _g("POST", f"{g}/{page}/video_stories", data={"upload_phase": "start", "access_token": tok})
    with open(path, "rb") as fh:
        _g("POST", s.get("upload_url") or f"https://rupload.facebook.com/video-upload/{GV()}/{s['video_id']}",
           headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(Path(path).stat().st_size)}, data=fh)
    r = _g("POST", f"{g}/{page}/video_stories", data={"upload_phase": "finish", "video_id": s["video_id"], "access_token": tok})
    return {"id": r.get("post_id") or s["video_id"]}


def ig_comment(media_id, text):
    tok, _, _ = meta()
    _g("POST", f"https://graph.facebook.com/{GV()}/{media_id}/comments", data={"message": text, "access_token": tok})


def ig_stats(media_id):
    tok, _, _ = meta()
    g = f"https://graph.facebook.com/{GV()}"
    out = {}
    for m in ("views", "reach", "likes", "comments", "shares", "saved", "ig_reels_avg_watch_time"):
        try:
            r = _g("GET", f"{g}/{media_id}/insights", params={"metric": m, "access_token": tok})
            out[m] = r["data"][0]["values"][0]["value"] if r.get("data") else None
        except Exception:
            out[m] = None
    return out


def fb_video(path, caption, title=""):
    """Normal Page video post (graph-video.facebook.com /{page}/videos). Shows in the Page feed in the mobile app;
    Facebook turns vertical short videos into Reels itself."""
    tok, _, page = meta()
    if not page:
        raise Skip("FB_PAGE_ID missing in .env")
    with open(path, "rb") as fh:
        r = _g("POST", f"https://graph-video.facebook.com/{GV()}/{page}/videos",
               data={"description": caption, "title": title[:250], "published": "true", "access_token": tok},
               files={"source": (Path(path).name, fh, "video/mp4")})
    vid = r["id"]
    for _ in range(60):                                  # wait until Facebook has processed and published it
        st = _g("GET", f"https://graph.facebook.com/{GV()}/{vid}", params={"fields": "status,permalink_url", "access_token": tok})
        s = st.get("status", {})
        if s.get("video_status") == "ready" and s.get("publishing_phase", {}).get("publish_status") == "published":
            break
        if s.get("video_status") == "error":
            raise RuntimeError(f"Facebook video processing error: {s}")
        time.sleep(5)
    link = st.get("permalink_url", "")
    return {"id": vid, "url": ("https://www.facebook.com" + link) if link.startswith("/") else (link or f"https://www.facebook.com/{vid}")}


def fb_upload(path, caption):
    tok, _, page = meta()
    if not page:
        raise Skip("FB_PAGE_ID missing in .env")
    g = f"https://graph.facebook.com/{GV()}"
    s = _g("POST", f"{g}/{page}/video_reels", data={"upload_phase": "start", "access_token": tok})
    vid = s["video_id"]
    size = Path(path).stat().st_size
    with open(path, "rb") as fh:
        _g("POST", s.get("upload_url") or f"https://rupload.facebook.com/video-upload/{GV()}/{vid}",
           headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(size)}, data=fh)
    _g("POST", f"{g}/{page}/video_reels", data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                                "description": caption, "access_token": tok})
    return {"id": vid, "url": f"https://www.facebook.com/reel/{vid}"}


def ig_carousel(image_urls, caption):
    """Instagram carousel from public JPEG URLs (hosted on GitHub Pages)."""
    tok, ig, _ = meta()
    if not ig:
        raise Skip("IG_USER_ID missing in .env")
    g = f"https://graph.facebook.com/{GV()}"
    kids = [_g("POST", f"{g}/{ig}/media", data={"image_url": u, "is_carousel_item": "true", "access_token": tok})["id"]
            for u in image_urls[:10]]
    c = _g("POST", f"{g}/{ig}/media", data={"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption,
                                            "access_token": tok})
    for _ in range(30):
        st = _g("GET", f"{g}/{c['id']}", params={"fields": "status_code", "access_token": tok})
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"IG carousel error: {st}")
        time.sleep(5)
    m = _g("POST", f"{g}/{ig}/media_publish", data={"creation_id": c["id"], "access_token": tok})
    link = _g("GET", f"{g}/{m['id']}", params={"fields": "permalink", "access_token": tok}).get("permalink")
    return {"id": m["id"], "url": link}


def fb_photos(paths, caption):
    """Facebook Page multi-photo post: upload each photo unpublished, then one feed post with all of them."""
    tok, _, page = meta()
    if not page:
        raise Skip("FB_PAGE_ID missing in .env")
    g = f"https://graph.facebook.com/{GV()}"
    ids = []
    for p in paths:
        with open(p, "rb") as fh:
            ids.append(_g("POST", f"{g}/{page}/photos", data={"published": "false", "access_token": tok},
                          files={"source": (Path(p).name, fh, "image/jpeg")})["id"])
    data = {"message": caption, "access_token": tok}
    for i, pid in enumerate(ids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    r = _g("POST", f"{g}/{page}/feed", data=data)
    return {"id": r["id"], "url": f"https://www.facebook.com/{r['id']}"}


def fb_stats(video_id):
    tok, _, _ = meta()
    g = f"https://graph.facebook.com/{GV()}"
    out = {}
    try:
        r = _g("GET", f"{g}/{video_id}/video_insights", params={"access_token": tok})
        for it in r.get("data", []):
            if it.get("values"):
                out[it["name"]] = it["values"][0].get("value")
    except Exception as e:
        out["error"] = str(e)[:100]
    try:
        r = _g("GET", f"{g}/{video_id}", params={"fields": "likes.summary(true),comments.summary(true)", "access_token": tok})
        out["likes"] = r.get("likes", {}).get("summary", {}).get("total_count")
        out["comments"] = r.get("comments", {}).get("summary", {}).get("total_count")
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- TikTok (inbox draft - user taps Post + adds trending sound)
TT = "https://open.tiktokapis.com/v2"


TT_KEY = "TIKTOK_REFRESH_TOKEN"     # which stored login to use; the Studio helper switches this to its own key


def tt_token():
    e = env()
    if not e.get(TT_KEY):
        raise Skip("TikTok not authorised - run: python Tools/autopost/post.py --auth tiktok")
    r = requests.post(f"{TT}/oauth/token/", data={"client_key": e["TIKTOK_CLIENT_KEY"], "client_secret": e["TIKTOK_CLIENT_SECRET"],
                                                  "grant_type": "refresh_token", "refresh_token": e[TT_KEY]},
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=60).json()
    if "access_token" not in r:
        raise RuntimeError(f"TikTok token refresh failed: {r}")
    if r.get("refresh_token") and r["refresh_token"] != e[TT_KEY]:
        set_env(TT_KEY, r["refresh_token"])
    return r["access_token"]


def tt_upload(path):
    tok = tt_token()
    size = Path(path).stat().st_size
    chunk = 10 * 1024 * 1024
    n = max(1, size // chunk)                     # last chunk absorbs the remainder (allowed up to 128 MB)
    init = requests.post(f"{TT}/post/publish/inbox/video/init/", headers={"Authorization": f"Bearer {tok}",
                         "Content-Type": "application/json; charset=UTF-8"},
                         json={"source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk if n > 1 else size,
                                               "total_chunk_count": n}}, timeout=60).json()
    if init.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok init failed: {init['error']}")
    url, pid = init["data"]["upload_url"], init["data"]["publish_id"]
    _tt_chunks(url, path, size, chunk, n)
    return {"id": pid, "url": "TikTok inbox (draft) - open TikTok, tap the notification, add a trending sound, Post"}


TT_DIRECT_SCOPES = "user.info.basic,video.upload,video.publish"


def _tt_json(path, tok, body):
    r = requests.post(f"{TT}{path}", headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"},
                      json=body, timeout=60).json()
    if r.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok {path}: {r['error'].get('code')} - {r['error'].get('message')}")
    return r.get("data", {})


def _tt_chunks(url, path, size, chunk, n):
    with open(path, "rb") as fh:
        for i in range(n):
            start = i * chunk
            end = size - 1 if i == n - 1 else start + chunk - 1
            fh.seek(start)
            data = fh.read(end - start + 1)
            for attempt in range(3):                    # short network drops happen: retry the chunk
                try:
                    r = requests.put(url, data=data, timeout=600, headers={"Content-Type": "video/mp4",
                                     "Content-Length": str(len(data)), "Content-Range": f"bytes {start}-{end}/{size}"})
                    break
                except requests.exceptions.ConnectionError:
                    if attempt == 2:
                        raise
                    time.sleep(5)
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok chunk {i} failed: {r.status_code} {r.text[:200]}")


def tt_exchange(code, redirect_uri=None):
    """Swap the one-time login code for tokens; stores the refresh token and granted scopes in .env."""
    import urllib.parse
    e = env()
    r = requests.post(f"{TT}/oauth/token/", data={"client_key": e["TIKTOK_CLIENT_KEY"], "client_secret": e["TIKTOK_CLIENT_SECRET"],
                      "code": urllib.parse.unquote(code), "grant_type": "authorization_code",
                      "redirect_uri": redirect_uri or e["TIKTOK_REDIRECT_URI"]},
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=60).json()
    if "refresh_token" not in r:
        raise RuntimeError(f"TikTok login failed: {r.get('error')} - {r.get('error_description')}")
    set_env(TT_KEY, r["refresh_token"])
    set_env("TIKTOK_GRANTED_SCOPES" if TT_KEY == "TIKTOK_REFRESH_TOKEN" else TT_KEY.replace("REFRESH_TOKEN", "SCOPES"), r.get("scope", ""))
    return r.get("scope", "")


def tt_creator():
    """Who is logged in + what they are allowed to post (privacy options, interaction settings, max duration)."""
    return _tt_json("/post/publish/creator_info/query/", tt_token(), {})


def tt_direct(path, title, privacy_level, disable_comment=False, disable_duet=False, disable_stitch=False,
              brand_organic=False, brand_content=False):
    """Direct Post (needs the video.publish scope). Until TikTok has audited the app, only SELF_ONLY is accepted."""
    tok = tt_token()
    size = Path(path).stat().st_size
    chunk = 10 * 1024 * 1024
    n = max(1, size // chunk)
    d = _tt_json("/post/publish/video/init/", tok, {
        "post_info": {"title": title[:2200], "privacy_level": privacy_level, "disable_comment": bool(disable_comment),
                      "disable_duet": bool(disable_duet), "disable_stitch": bool(disable_stitch),
                      "brand_organic_toggle": bool(brand_organic), "brand_content_toggle": bool(brand_content)},
        "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk if n > 1 else size, "total_chunk_count": n}})
    _tt_chunks(d["upload_url"], path, size, chunk, n)
    return {"id": d["publish_id"], "url": "TikTok (direct post)"}


def tt_publish_status(publish_id):
    return _tt_json("/post/publish/status/fetch/", tt_token(), {"publish_id": publish_id})


def tt_auth():
    """One-time: print the authorize URL, user pastes back the ?code= from the redirect."""
    import urllib.parse
    e = env()
    for k in ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REDIRECT_URI"):
        if not e.get(k):
            raise SystemExit(f"{k} missing in .env")
    q = urllib.parse.urlencode({"client_key": e["TIKTOK_CLIENT_KEY"], "scope": e.get("TIKTOK_SCOPES", "user.info.basic,video.upload"),
                                "response_type": "code", "redirect_uri": e["TIKTOK_REDIRECT_URI"], "state": "nz"})
    code = e.get("TIKTOK_AUTH_CODE", "").strip()
    if not code:   # step 1: open the approval page in the browser
        import webbrowser
        url = f"https://www.tiktok.com/v2/auth/authorize/?{q}"
        webbrowser.open(url)
        print("Opened TikTok approval page in your browser:\n" + url)
        print("\nAfter approving, copy the code from nomadzohaib.github.io/callback.html into .env as TIKTOK_AUTH_CODE=..., then run --auth tiktok again.")
        return
    code = urllib.parse.unquote(code)
    set_env("TIKTOK_AUTH_CODE", "")   # single-use: clear it
    r = requests.post(f"{TT}/oauth/token/", data={"client_key": e["TIKTOK_CLIENT_KEY"], "client_secret": e["TIKTOK_CLIENT_SECRET"],
                      "code": code, "grant_type": "authorization_code", "redirect_uri": e["TIKTOK_REDIRECT_URI"]},
                      headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=60).json()
    if "refresh_token" not in r:
        raise SystemExit(f"failed: {r}")
    set_env("TIKTOK_REFRESH_TOKEN", r["refresh_token"])
    print("TikTok connected.")


def tt_stats():
    """Recent videos on the account (after you post the drafts) with view/like counts."""
    tok = tt_token()
    r = requests.post(f"{TT}/video/list/?fields=id,title,create_time,view_count,like_count,comment_count,share_count",
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
                      json={"max_count": 20}, timeout=60).json()
    return r.get("data", {}).get("videos", [])
