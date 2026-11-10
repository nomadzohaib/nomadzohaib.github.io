"""Runs on GitHub Actions every 3 hours and rebuilds videos.json from the channel's uploads.
Uses the YouTube Data API v3 with the YT_API_KEY repository secret (never exposed on the website).
Standard library only."""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CHANNEL_ID = "UCD5f8tlS83WxpYYS0-gY8Ag"
UPLOADS = "UU" + CHANNEL_ID[2:]
OUT = Path(__file__).resolve().parents[1] / "videos.json"
API = "https://www.googleapis.com/youtube/v3/"
UA = {"User-Agent": "Mozilla/5.0 (nomadzohaib.github.io sync)"}


def api(path, **params):
    params["key"] = os.environ["YT_API_KEY"]
    with urllib.request.urlopen(API + path + "?" + urllib.parse.urlencode(params), timeout=30) as r:
        return json.load(r)


def secs(iso):
    m = re.match(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h * 3600 + mi * 60 + s


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def is_short(vid):
    """/shorts/<id> answers 200 for a Short and redirects for a normal video."""
    try:
        r = urllib.request.build_opener(NoRedirect).open(
            urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", headers=UA, method="HEAD"), timeout=20)
        return r.status == 200
    except urllib.error.HTTPError as e:
        return False if e.code in (301, 302, 303, 307, 308) else None
    except Exception:
        return None


def main():
    if not os.environ.get("YT_API_KEY"):
        sys.exit("YT_API_KEY secret is not set")
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"channel": {}, "videos": []}
    known = {v["id"]: v for v in old["videos"]}
    ids, tok = [], None
    while True:
        p = {"part": "contentDetails", "playlistId": UPLOADS, "maxResults": 50}
        if tok:
            p["pageToken"] = tok
        r = api("playlistItems", **p)
        ids += [it["contentDetails"]["videoId"] for it in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    videos, added = [], []
    for i in range(0, len(ids), 50):
        r = api("videos", part="snippet,contentDetails,statistics,status", id=",".join(ids[i:i + 50]))
        for v in r.get("items", []):
            if v["status"].get("privacyStatus") != "public":
                continue
            d = secs(v["contentDetails"]["duration"])
            prev = known.get(v["id"])
            short = prev["short"] if prev else is_short(v["id"])
            if short is None:
                short = d <= 60
            item = {"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
                    "seconds": d, "short": short, "views": int(v["statistics"].get("viewCount", 0))}
            videos.append(item)
            if not prev:
                added.append(item)
    videos.sort(key=lambda v: v["published"], reverse=True)
    ch = api("channels", part="statistics", id=CHANNEL_ID).get("items", [{}])[0].get("statistics", {})
    data = {"channel": dict(old.get("channel", {}), videos=len(videos), subscribers=int(ch.get("subscriberCount", 0))),
            "videos": videos}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(videos)} public videos, {len(added)} new")
    for v in added:
        print("  +", "SHORT" if v["short"] else "FILM ", v["title"])


if __name__ == "__main__":
    main()
