#!/usr/bin/env python3
"""Compress videos to lower bitrate and re-slice to HLS."""
import subprocess, json, shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
VIDEOS = ROOT / "assets/videos"
HLS_DIR = VIDEOS / "hls"
FFMPEG = "ffmpeg"

# scenes that don't have videos yet — they'll only show images
NO_VIDEO = {"scroll_phone", "lunch", "chat_baby", "buy_dumpling"}

def process(mp4_path, scene_id):
    print(f"\n  {scene_id}...")

    # Skip if no video
    if scene_id in NO_VIDEO:
        print(f"  → No video, skip")
        return None

    size_before = mp4_path.stat().st_size

    # 1. Compress MP4 (re-encode at lower bitrate)
    compressed = VIDEOS / f"{scene_id}_comp.mp4"
    cmd_compress = [
        FFMPEG, "-y", "-i", str(mp4_path),
        "-c:v", "libx264", "-preset", "fast", "-b:v", "800k", "-maxrate", "1000k", "-bufsize", "2000k",
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac", "-b:a", "48k", "-ar", "22050",
        "-movflags", "+faststart",
        str(compressed),
    ]
    r = subprocess.run(cmd_compress, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"  ✗ Compress failed: {r.stderr[:100]}")
        return None

    size_after = compressed.stat().st_size
    ratio = size_after / size_before if size_before else 1
    print(f"  → Compressed: {size_before//1024}K → {size_after//1024}K ({ratio*100:.0f}%)")

    # 2. Replace original with compressed
    compressed.replace(mp4_path)
    print(f"  → MP4 replaced")

    # 3. HLS slice from compressed
    out_dir = HLS_DIR / scene_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    m3u8 = out_dir / "index.m3u8"
    ts_pattern = str(out_dir / "seg_%03d.ts")

    cmd_hls = [
        FFMPEG, "-y", "-i", str(mp4_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "48k", "-ar", "22050",
        "-g", "30", "-keyint_min", "30",
        "-hls_time", "3",
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", ts_pattern,
        "-hls_list_size", "0",
        str(m3u8),
    ]
    r2 = subprocess.run(cmd_hls, capture_output=True, text=True, timeout=300)
    if r2.returncode != 0:
        print(f"  ✗ HLS failed: {r2.stderr[:100]}")
        return None

    ts_count = len(list(out_dir.glob("*.ts")))
    hls_size = sum(f.stat().st_size for f in out_dir.glob("*")) 
    print(f"  → HLS: {ts_count} segments, {hls_size//1024}K total")
    return str(m3u8)

def main():
    mp4s = sorted(VIDEOS.glob("*.mp4"))
    if not mp4s:
        print("No MP4 files found"); return

    print(f"Processing {len(mp4s)} videos...")
    results = {}
    for mp4 in mp4s:
        sid = mp4.stem
        if sid.endswith("_comp"): continue  # skip temp files
        m3u8 = process(mp4, sid)
        if m3u8:
            results[sid] = m3u8

    # Save manifest
    out = VIDEOS / "hls_manifest.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n{'='*50}")
    print(f"  Done: {len(results)} videos compressed + HLS sliced")
    print(f"  Manifest: {out}")

if __name__ == "__main__":
    main()
