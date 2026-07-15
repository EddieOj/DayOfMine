#!/usr/bin/env python3
"""Convert all MP4 videos to HLS (m3u8 + ts segments) for smooth streaming.
Each video gets its own subfolder under assets/videos/hls/<scene_id>/.
"""
import subprocess, sys, json
from pathlib import Path

ROOT = Path(__file__).parent.parent
VIDEOS = ROOT / "assets/videos"
HLS_DIR = VIDEOS / "hls"
FFMPEG = "ffmpeg"

def convert(mp4_path, scene_id):
    """Convert single MP4 to HLS. Returns (m3u8_path, success)."""
    out_dir = HLS_DIR / scene_id
    out_dir.mkdir(parents=True, exist_ok=True)
    m3u8 = out_dir / "index.m3u8"
    ts_pattern = str(out_dir / "seg_%03d.ts")

    cmd = [
        FFMPEG, "-y",
        "-i", str(mp4_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "64k", "-ar", "44100",
        "-g", "30", "-keyint_min", "30",
        "-hls_time", "3",
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", ts_pattern,
        "-hls_list_size", "0",
        str(m3u8),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  ✗ {scene_id}: {r.stderr[:200]}")
            return None, False
        # Count segments
        ts_count = len(list(out_dir.glob("*.ts")))
        size = sum(f.stat().st_size for f in out_dir.glob("*.ts")) + m3u8.stat().st_size
        print(f"  ✓ {scene_id}: {ts_count} segments, {size//1024}KB total")
        return m3u8, True
    except subprocess.TimeoutExpired:
        print(f"  ✗ {scene_id}: timeout")
        return None, False

def main():
    mp4s = sorted(VIDEOS.glob("*.mp4"))
    if not mp4s:
        print("No MP4 files found")
        sys.exit(1)

    print(f"Found {len(mp4s)} MP4 files")
    results = []
    for mp4 in mp4s:
        scene_id = mp4.stem
        print(f"\n  Converting {scene_id}...")
        m3u8, ok = convert(mp4, scene_id)
        results.append({"id": scene_id, "ok": ok, "hls": f"assets/videos/hls/{scene_id}/index.m3u8" if ok else None})

    # Generate HLS manifest JSON for frontend
    hls_manifest = {r["id"]: r["hls"] for r in results if r["ok"]}
    out = ROOT / "assets/videos/hls_manifest.json"
    out.write_text(json.dumps(hls_manifest, indent=2), encoding="utf-8")
    print(f"\n{'='*50}")
    print(f"  Done: {sum(1 for r in results if r['ok'])}/{len(results)} converted")
    print(f"  Manifest: {out}")

if __name__ == "__main__":
    main()
