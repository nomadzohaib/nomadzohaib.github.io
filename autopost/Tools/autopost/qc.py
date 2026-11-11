"""Pre-post quality gate. Checks the video file and the post's metadata before anything is uploaded.
    python Tools/autopost/qc.py            check every scheduled post (prints a table)
Used by post.py: a post that fails is held back (logged), never uploaded."""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import captions as CAP  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
_cache = {}


def probe(path):
    if path in _cache:
        return _cache[path]
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                                     capture_output=True, text=True).stdout or "{}")
    v = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), {})
    a = next((s for s in info.get("streams", []) if s["codec_type"] == "audio"), None)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf", "blackdetect=d=0.6:pix_th=0.06,freezedetect=n=0.002:d=2.5",
                        "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"], capture_output=True, text=True)
    err = r.stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    out = {"w": v.get("width"), "h": v.get("height"), "codec": v.get("codec_name"), "fps": v.get("r_frame_rate"),
           "dur": float(info.get("format", {}).get("duration", 0)), "mb": Path(path).stat().st_size / 1e6,
           "audio": a is not None, "lufs": float(I[-1]) if I else None, "tp": float(TP[-1]) if TP else None,
           "black": len(re.findall(r"black_start", err)), "freeze": len(re.findall(r"freeze_start", err))}
    _cache[path] = out
    return out


def check_video(path):
    p = Path(path)
    if not p.exists():
        return ["file missing"], {}
    m = probe(p)
    issues = []
    if (m["w"], m["h"]) != (1080, 1920):
        issues.append(f"not 1080x1920 ({m['w']}x{m['h']})")
    if m["codec"] != "h264":
        issues.append(f"codec {m['codec']}")
    if not 5 <= m["dur"] <= 90:
        issues.append(f"duration {m['dur']:.1f}s outside 5-90 s")
    if m["mb"] > 250:
        issues.append(f"file {m['mb']:.0f} MB too large")
    if not m["audio"]:
        issues.append("no audio track")
    if m["lufs"] is None or not -17.5 <= m["lufs"] <= -11:
        issues.append(f"loudness {m['lufs']} LUFS (want about -14)")
    if m["tp"] is not None and m["tp"] > -0.5:
        issues.append(f"clipping risk, true peak {m['tp']} dBTP")
    if m["black"]:
        issues.append(f"{m['black']} black gap(s)")
    if m["freeze"]:
        issues.append(f"{m['freeze']} frozen stretch(es)")
    return issues, m


def check_meta(concept, yt_url=""):
    issues = []
    t = CAP.yt_title(concept)
    if len(t) > 100:
        issues.append(f"YouTube title {len(t)} chars (max 100)")
    if "bali" not in t.lower()[:45]:
        issues.append("YouTube title: keyword 'Bali' not in first 45 chars")
    caps = sum(ch.isupper() for ch in t) / max(1, sum(ch.isalpha() for ch in t))
    if caps > 0.6:
        issues.append("YouTube title mostly CAPS (spam signal)")
    for pf, limit, tag_max in (("instagram", 2200, 30), ("facebook", 5000, 30), ("tiktok", 2200, 10), ("youtube", 4900, 15)):
        c = CAP.caption(concept, pf, yt_url)
        tags = re.findall(r"#\w+", c)
        if len(c) > limit:
            issues.append(f"{pf} caption {len(c)} chars > {limit}")
        if not 3 <= len(tags) <= tag_max:
            issues.append(f"{pf}: {len(tags)} hashtags (want 3-{tag_max})")
        if len(set(t.lower() for t in tags)) != len(tags):
            issues.append(f"{pf}: duplicate hashtags")
        if pf in ("instagram", "facebook", "youtube") and not re.search(r"youtube|vlog", c, re.I):
            issues.append(f"{pf}: no call-to-action to the full vlog")
    if len(CAP.yt_tags(concept)) < 8 or len(",".join(CAP.yt_tags(concept))) > 480:
        issues.append("YouTube tags: want 8+ tags under 480 chars")
    return issues


def check_post(p, yt_url=""):
    """Returns (ok, issues) for one schedule entry."""
    issues = []
    for key in ("file_music", "file_clean"):
        vi, _ = check_video(ROOT / p[key])
        issues += [f"{Path(p[key]).name}: {x}" for x in vi]
    issues += check_meta(p["concept"], yt_url)
    return (not issues), issues


if __name__ == "__main__":
    plan = json.loads((ROOT / "05_Work" / "autopost" / "schedule.json").read_text(encoding="utf-8"))
    bad = 0
    plan = [p for p in plan if p.get("kind", "reel") == "reel"]      # carousels have no video file
    for p in plan:
        ok, iss = check_post(p)
        m = probe(ROOT / p["file_music"])
        print(f"{p['slot'][5:16]} {p['concept']:<15} {p['style']:<5} {m['dur']:5.1f}s {m['mb']:5.1f}MB "
              f"{m['lufs']} LUFS tp {m['tp']}  {'PASS' if ok else 'FAIL'}")
        for x in iss:
            print("     -", x)
        bad += not ok
    print(f"\n{len(plan) - bad}/{len(plan)} posts pass")
