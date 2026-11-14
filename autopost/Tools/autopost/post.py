"""
Autoposter - Bali Day 5: reels 2/5/7 PM + tips carousels 3/8 PM PKT, Tue 10 Nov -> Sun 15 Nov 2026.

    python Tools/autopost/post.py --plan            build/print the week's schedule
    python Tools/autopost/post.py --due             post whatever slot is due now (Task Scheduler runs this)
    python Tools/autopost/post.py --due --dry-run   show what would be posted, post nothing
    python Tools/autopost/post.py --check           test every platform connection (no posting)
    python Tools/autopost/post.py --auth youtube|tiktok
    python Tools/autopost/post.py --status
"""
import argparse
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import captions as CAP  # noqa: E402
import platforms as P  # noqa: E402

ROOT = P.ROOT
PLAN = P.STATE / "schedule.json"
LOG = P.STATE / "post_log.txt"
PKT = dt.timezone(dt.timedelta(hours=5))

# concepts in the test (strongest hooks first); hotel_switch is the reserve for next week
TEST = ["finns_story", "coconut", "storm", "labubu", "pakistan_beach", "sunset"]
START = dt.date(2026, 11, 10)
SLOTS = [(14, 0), (19, 0)]
LATE_LIMIT_H = 4          # if the PC was off at slot time, still post up to 4 h late; after that skip


def log(msg):
    line = f"{dt.datetime.now(PKT):%Y-%m-%d %H:%M} {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# Reels at 2 PM / 5 PM / 7 PM (2 PM + 7 PM keep the original A/B design; 5 PM = travel tips + hotel story),
# tips image carousels 1 hour after the 2 PM and 7 PM reels (3 PM / 8 PM), Instagram + Facebook.
REELS = [  # per day: (14:00 moment, 17:00 travel tips, 19:00 story series "Bali Day 5 - Part n/5")
    (("finns_story", "cine"), ("tips_prices", "cine"), ("story_p2", "cine")),
    (("coconut", "bold"), ("tips_itinerary", "bold"), ("story_p3", "cine")),
    (("storm", "cine"), ("sunset", "cine"), ("story_p4", "cine")),
    (("labubu", "bold"), ("tips_prices", "bold"), ("story_p5", "cine")),
    (("pakistan_beach", "cine"), ("tips_itinerary", "cine"), ("hotel_switch", "cine")),
    (("sunset", "bold"), ("coconut", "cine"), ("labubu", "cine")),
]
EXTRA = [("2026-11-10T14:40:00+05:00", "story_p1", "cine")]   # one-off posts outside the fixed hours
RETIRE = {"2026-11-10T14:00:00+05:00"}   # whole-video recap: keep what is live, post it nowhere else
IMAGES = [("prices", "itinerary"), ("rain", "finns"), ("beachwalk", "kuta_beach"), ("scooter", "pakistani"),
          ("stay", "budget"), ("sunset_spots", "recap")]
IMAGE_PLATFORMS = ["instagram", "facebook"]
TIPS = P.STATE / "tips_posts.json"
# EXPERIMENT E8 (14 Nov): Instagram cover frame. Sunset bold (Sun 15 Nov 2 PM) uses the golden sun-on-horizon frame
# with "Aur phir... aasmaan ne yeh kiya" (7.5 s) instead of the default first frame. Video itself is unchanged.
IG_COVER_MS = {("sunset", "bold"): 7500}


def build_plan():
    plan = []
    for d, (reels, imgs) in enumerate(zip(REELS, IMAGES)):
        day = START + dt.timedelta(days=d)
        at = lambda hh: dt.datetime(day.year, day.month, day.day, hh, 0, tzinfo=PKT).isoformat()  # noqa: E731
        for hh, (c, s) in zip((14, 17, 19), reels):
            plan.append({"slot": at(hh), "kind": "reel", "concept": c, "style": s,
                         "time": {14: "afternoon", 17: "tips", 19: "evening"}[hh],
                         "file_music": f"06_Exports/Reels/{c}_{s}_music.mp4", "file_clean": f"06_Exports/Reels/{c}_{s}_clean.mp4",
                         "posted": {}})
        for hh, pid in zip((15, 20), imgs):
            plan.append({"slot": at(hh), "kind": "image", "concept": pid, "style": "carousel", "time": "image", "posted": {}})
    for slot, c, s in EXTRA:
        plan.append({"slot": slot, "kind": "reel", "concept": c, "style": s, "time": "afternoon",
                     "file_music": f"06_Exports/Reels/{c}_{s}_music.mp4", "file_clean": f"06_Exports/Reels/{c}_{s}_clean.mp4",
                     "posted": {}})
    plan.sort(key=lambda p: p["slot"])
    old = {p["slot"]: p for p in json.loads(PLAN.read_text(encoding="utf-8"))} if PLAN.exists() else {}
    for p in plan:                                    # keep what was already posted (same slot + same post)
        o = old.get(p["slot"])
        if o and o.get("concept") == p["concept"]:
            p["posted"] = o.get("posted", {})
        if p["slot"] in RETIRE:
            for pf in PLATFORMS:
                if not p["posted"].get(pf, {}).get("id"):
                    p["posted"][pf] = {"skip": "retired: whole-video recap replaced by story parts"}
    PLAN.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    return plan


def print_plan(plan):
    for p in plan:
        t = dt.datetime.fromisoformat(p["slot"])
        ok = "✓" if p.get("kind") == "image" or (ROOT / p["file_music"]).exists() else "✗ missing"
        done = ",".join(k for k, v in p["posted"].items() if v.get("id")) or "-"
        print(f"{t:%a %d %b %I:%M %p}  {p['concept']:<15} {p['style']:<5} file {ok:<9} posted: {done}")


PLATFORMS = ["youtube", "instagram", "facebook", "tiktok"]


def post_image(p, platform, dry):
    post = json.loads(TIPS.read_text(encoding="utf-8"))[p["concept"]]
    yt_url = P.env().get("YOUTUBE_VLOG_URL", "")
    cap = CAP.image_caption(post, platform, yt_url)
    if dry:
        return {"dry": True, "slides": len(post["files"]), "caption": cap[:80] + "..."}
    if platform == "instagram":
        r = P.ig_carousel(post["urls"], cap)
        try:
            P.ig_comment(r["id"], post["q"])
        except Exception as e:
            log(f"   instagram comment skipped: {str(e)[:100]}")
        try:                                              # cover slide to the Story
            r["story"] = P.ig_story(image_url=post["urls"][0])["id"]
            log("   instagram story posted")
        except Exception as e:
            log(f"   instagram story skipped: {str(e)[:120]}")
        return r
    if platform == "facebook":
        files = [ROOT / f for f in post["files"]]
        if CLOUD:                                 # slides are on the website; download them for the upload
            import requests
            for f, u in zip(files, post["urls"]):
                if not f.exists():
                    f.parent.mkdir(parents=True, exist_ok=True)
                    r = requests.get(u, timeout=120)
                    r.raise_for_status()
                    f.write_bytes(r.content)
        return P.fb_photos(files, cap)


CLOUD = P.env().get("NZ_CLOUD") == "1"      # running on GitHub Actions (laptop can be off)
RELEASE = "https://github.com/nomadzohaib/nomadzohaib.github.io/releases/download/reels/"


def fetch(f):
    """Cloud: reels live as GitHub release assets; download one to the path the schedule expects."""
    f = Path(f)
    if f.exists() or not CLOUD:
        return f
    import requests
    f.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(RELEASE + f.name, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(f, "wb") as fh:
            for b in r.iter_content(1 << 20):
                fh.write(b)
    return f


def social_safe(f):
    """Instagram/Facebook-safe copy: H.264 high, ~9 Mbps (IG max 25), AAC 128k 48 kHz, faststart. Cached."""
    import subprocess
    if CLOUD:                                     # cloud copies are already the social-safe encode
        return f
    out = P.STATE / "social" / f.name
    if out.exists() and out.stat().st_mtime > f.stat().st_mtime:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(f), "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",
                    "-pix_fmt", "yuv420p", "-b:v", "9M", "-maxrate", "12M", "-bufsize", "18M", "-r", "30",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(out)], check=True)
    return out


def post_one(p, platform, dry):
    if p.get("kind") == "image":
        return post_image(p, platform, dry)
    c = p["concept"]
    yt_url = P.env().get("YOUTUBE_VLOG_URL", "")
    f = ROOT / (p["file_clean"] if platform == "tiktok" else p["file_music"])
    if not f.exists():
        raise RuntimeError(f"missing file {f}")
    if dry:
        return {"dry": True, "file": str(f.name), "caption": CAP.caption(c, platform, yt_url)[:80] + "..."}
    if platform == "youtube":
        return P.yt_upload(f, CAP.yt_title(c), CAP.caption(c, "youtube", yt_url),
                           CAP.yt_tags(c), CAP.pinned_comment(c))
    if platform in ("instagram", "facebook"):
        f = social_safe(f)
    if platform == "instagram":
        r = P.ig_upload(f, CAP.caption(c, "instagram", yt_url), IG_COVER_MS.get((c, p.get("style"))))
        try:
            P.ig_comment(r["id"], CAP.pinned_comment(c))
        except Exception as e:
            log(f"   instagram comment skipped: {str(e)[:100]}")
        try:                                              # same reel to the Story: reaches followers a second time
            r["story"] = P.ig_story(f)["id"]
            log("   instagram story posted")
        except Exception as e:
            log(f"   instagram story skipped: {str(e)[:120]}")
        return r
    if platform == "facebook":
        r = P.fb_upload(f, CAP.caption(c, "facebook", yt_url))
        try:
            r["story"] = P.fb_story(f)["id"]
            log("   facebook story posted")
        except Exception as e:
            log(f"   facebook story skipped: {str(e)[:120]}")
        return r
    if platform == "tiktok" and P.env().get("TIKTOK_DIRECT") == "1":
        # Direct Post: only switch on (TIKTOK_DIRECT=1 in .env) after TikTok has approved + audited the app.
        info = P.tt_creator()
        want = P.env().get("TIKTOK_PRIVACY", "PUBLIC_TO_EVERYONE")
        if want not in info.get("privacy_level_options", []):
            raise RuntimeError(f"TikTok does not allow {want} for this account yet (allowed: {info.get('privacy_level_options')})")
        return P.tt_direct(social_safe(f), CAP.caption(c, "tiktok", yt_url), want)
    if platform == "tiktok":
        r = P.tt_upload(f)
        r["caption_to_paste"] = CAP.caption(c, "tiktok", yt_url)
        return r


def due(dry=False):
    plan = build_plan()                       # always re-derive from code; already-posted entries are kept
    now = dt.datetime.now(PKT)
    did = False
    for p in plan:
        t = dt.datetime.fromisoformat(p["slot"])
        if not (t - dt.timedelta(minutes=10) <= now <= t + dt.timedelta(hours=LATE_LIMIT_H)):
            continue
        pfs = IMAGE_PLATFORMS if p.get("kind") == "image" else PLATFORMS
        if all(p["posted"].get(pf, {}).get("id") or p["posted"].get(pf, {}).get("skip") for pf in pfs):
            continue                                              # nothing left to post for this slot
        if p.get("kind", "reel") == "reel" and not dry:
            for k in ("file_music", "file_clean"):
                fetch(ROOT / p[k])
        if p.get("kind", "reel") == "reel":
            import qc as QC
            ok, issues = QC.check_post(p, P.env().get("YOUTUBE_VLOG_URL", ""))
            if not ok:
                log(f"{p['concept']}/{p['style']}: HELD BACK by quality gate: " + "; ".join(issues)[:400])
                did = True
                continue
            log(f"{p['concept']}/{p['style']}: quality gate PASS")
        for pf in pfs:
            if p["posted"].get(pf, {}).get("id") or p["posted"].get(pf, {}).get("skip"):
                continue
            try:
                r = post_one(p, pf, dry)
                if not dry:
                    r["at"] = dt.datetime.now(PKT).isoformat()
                    p["posted"][pf] = r                   # save at once: a killed run must never re-post
                    PLAN.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
                log(f"{p['concept']}/{p['style']} -> {pf}: {r.get('url', r)}")
            except P.Skip as e:
                log(f"{p['concept']}/{p['style']} -> {pf}: SKIPPED ({e})")
            except Exception as e:
                log(f"{p['concept']}/{p['style']} -> {pf}: FAILED " + __import__("re").sub(r"(access_token|key|token)=[^&\s'\"]+", r"\1=***", str(e))[:300])
                with open(LOG, "a", encoding="utf-8") as fh:
                    fh.write(traceback.format_exc() + "\n")
            did = True
        if not dry:
            PLAN.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    if not did:
        log("nothing due")


def check():
    for name, fn in (("youtube", lambda: P.yt_client().channels().list(part="snippet", mine=True).execute()["items"][0]["snippet"]["title"]),
                     ("facebook", lambda: "Page " + json.loads(P.META_CACHE.read_text()).get("page_name", "?") if P.meta() else ""),
                     ("instagram", lambda: P._g("GET", f"https://graph.facebook.com/{P.GV()}/{P.meta()[1]}",
                                                params={"fields": "username", "access_token": P.meta()[0]})["username"]),
                     ("tiktok", lambda: bool(P.tt_token()) and "token ok")):
        try:
            print(f"{name:<10} OK   {fn()}")
        except P.Skip as e:
            print(f"{name:<10} --   not set up: {e}")
        except Exception as e:
            import re
            msg = re.sub(r"(access_token|key|token)=[^&\s'\"]+", r"\1=***", str(e))
            print(f"{name:<10} FAIL {msg[:200]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--auth", choices=["youtube", "tiktok"])
    ap.add_argument("--pending", action="store_true", help="print yes/no: is anything due now (cheap, no posting)")
    a = ap.parse_args()
    if CLOUD and P.env().get("YT_TOKEN_JSON") and not P.YT_TOKEN.exists():
        P.YT_TOKEN.write_text(P.env()["YT_TOKEN_JSON"])
    if a.pending:
        now = dt.datetime.now(PKT)
        plan = build_plan()
        keys = {"reel": PLATFORMS, "image": IMAGE_PLATFORMS}
        due_now = any(dt.datetime.fromisoformat(p["slot"]) - dt.timedelta(minutes=10) <= now
                      <= dt.datetime.fromisoformat(p["slot"]) + dt.timedelta(hours=LATE_LIMIT_H)
                      and not all(p["posted"].get(pf, {}).get("id") or p["posted"].get(pf, {}).get("skip")
                                  for pf in keys[p.get("kind", "reel")]) for p in plan)
        print("yes" if due_now else "no")
        return
    if a.auth == "youtube":
        P.yt_client(interactive=True)
        print("YouTube connected.")
    elif a.auth == "tiktok":
        P.tt_auth()
    elif a.plan:
        print_plan(build_plan())
    elif a.due:
        if a.dry_run:
            return due(True)
        import os
        import time
        lock = P.STATE / "post.lock"

        def alive(pid):                          # is the run that wrote the lock still going?
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                return False
            code = ctypes.c_ulong()
            ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(h)
            return code.value == 259             # STILL_ACTIVE

        for _ in range(90):                      # another run still uploading? wait up to 45 min
            if not lock.exists() or time.time() - lock.stat().st_mtime > 3 * 3600:
                break
            pid = lock.read_text().split("|")[0].strip()
            if not pid.isdigit() or not alive(int(pid)):
                log("stale lock from a run that was stopped: ignoring it")
                break
            time.sleep(30)
        lock.write_text(f"{os.getpid()}|{dt.datetime.now(PKT)}")
        try:
            due(False)
        finally:
            lock.unlink(missing_ok=True)
    elif a.check:
        check()
    else:
        print_plan(json.loads(PLAN.read_text(encoding="utf-8")) if PLAN.exists() else build_plan())


if __name__ == "__main__":
    main()
