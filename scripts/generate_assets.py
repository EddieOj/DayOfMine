#!/usr/bin/env python3
"""Generate first 6 scenes only.  Adjusts prompt to fix 'No image URL' issue."""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import requests as req
from src.api_helper import JimengAI

SCENES = [
    {"id":"sleep","t":"00:00–08:00","l":"呼呼大睡",
     "pt":"cute chibi girl with long black slightly wavy hair sleeping in bed, moonlight through window, warm bedroom, soft lighting, healing style, flat vector art, pastel colors, cozy atmosphere",
     "pv":"cute girl sleeping peacefully, gentle breathing, moonlight shining, calm and cozy"},
    {"id":"wakeup","t":"08:00–08:30","l":"起床咯",
     "pt":"cute chibi girl with long black wavy hair sitting on bed rubbing eyes, waking up, morning sunlight streaming into bedroom, stretching, healing flat vector style, soft warm colors",
     "pv":"cute girl waking up, rubbing eyes, stretching, warm morning sunlight, fresh atmosphere"},
    {"id":"wash","t":"08:30–09:00","l":"洗漱",
     "pt":"cute chibi girl with long black wavy hair brushing teeth at sink, white towel, mirror reflection, bubbles floating, bathroom, flat vector art, soft blue tones",
     "pv":"cute girl brushing teeth, water flowing, bubbles floating, fresh and lively"},
    {"id":"login_game","t":"09:00–09:10","l":"代号莺",
     "pt":"cute chibi girl with long black wavy hair sitting on sofa playing mobile game '代号莺' on smartphone, excited expression, phone screen showing colorful game interface with莺 character, warm indoor lighting, flat vector art, purple blue neon game glow",
     "pv":"cute girl playing mobile game'代号莺'on phone, fingers tapping screen, game animations flashing, happy excited expression, immersed in gameplay"},
    {"id":"study","t":"09:10–09:40","l":"学科一",
     "pt":"cute chibi girl with long black wavy hair studying at desk, driving test book and laptop, reading seriously, concentrated expression, flat vector illustration, soft indigo tones",
     "pv":"cute girl studying seriously, turning pages, thinking pose, focused learning atmosphere"},
    {"id":"scroll_phone","t":"10:00–11:00","l":"刷手机",
     "pt":"cute chibi girl with long black wavy hair lying on sofa scrolling phone, relaxing, casual clothes, warm indoor lighting, flat vector art, soft colors",
     "pv":"cute girl lying on sofa scrolling phone, relaxed, changing expressions while browsing"},
    {"id":"lunch","t":"11:00–12:00","l":"吃饭",
     "pt":"cute chibi girl with long black wavy hair eating lunch at table, rice and dishes, chopsticks, warm dining atmosphere, flat vector illustration, soft warm colors",
     "pv":"cute girl eating lunch happily, chopsticks picking up food, satisfied eating"},
    {"id":"chat_baby","t":"12:00–15:00","l":"和宝宝聊天",
     "pt":"cute chibi girl with long black wavy hair video chatting on phone, smiling happily at screen, cozy room, warm lighting, flat vector art, pinkish warm tones",
     "pv":"cute girl video chatting on phone, laughing and talking, warm and happy conversation atmosphere"},
    {"id":"buy_dumpling","t":"15:00–15:30","l":"买饺子皮",
     "pt":"cute chibi girl with long black wavy hair walking outside to shop, holding small bag, street with shops, daytime, flat vector illustration, soft outdoor lighting",
     "pv":"cute girl walking outside to buy dumpling wrappers, cheerful steps, outdoor daylight"},
]

assets_dir = Path(__file__).parent.parent / "assets"
(scenes_dir := assets_dir / "scenes").mkdir(parents=True, exist_ok=True)
(videos_dir := assets_dir / "videos").mkdir(parents=True, exist_ok=True)

ai = JimengAI()
manifest = []

for idx, s in enumerate(SCENES):
    sid = s["id"]
    print(f"\n{'─'*50}")
    print(f"  [{idx+1}/{len(SCENES)}] {s['l']}  {s['t']}")
    print(f"{'─'*50}")

    # 1. Image
    print("  → Text-to-Image...")
    try:
        tid = ai.submit_text_to_image(s["pt"], width=1080, height=1920, use_pre_llm=True)
        print(f"    task={tid}")
    except Exception as e:
        print(f"  ✗ {e}"); continue

    print("  → Waiting...")
    res = ai.wait_for_result(tid, "jimeng_t2i_v31", max_wait=180)
    if res.get("status") != "done":
        print(f"  ✗ {res}"); continue

    img_url = (res.get("image_urls") or [None])[0]
    if not img_url:
        print("  ✗ No image URL"); continue
    print(f"    url={img_url[:70]}...")

    r = req.get(img_url, timeout=60)
    (scenes_dir / f"{sid}.jpg").write_bytes(r.content)
    print(f"  ✓ Saved scene/{sid}.jpg ({len(r.content)//1024}KB)")

    # 2. Video
    print("  → Video (first&last=same image)...")
    try:
        vtid = ai.submit_video_first_last(img_url, img_url, s["pv"], seconds=5)
        print(f"    task={vtid}")
    except Exception as e:
        print(f"  ✗ {e}")
        manifest.append({"id":sid,"label":s["l"],"time":s["t"],"image_file":f"assets/scenes/{sid}.jpg","video_file":None})
        time.sleep(3); continue

    print("  → Waiting for video...")
    vres = ai.wait_for_result(vtid, "jimeng_i2v_first_tail_v30_1080", poll_interval=10, max_wait=600)
    if vres.get("status") != "done":
        print(f"  ✗ {vres}")
        manifest.append({"id":sid,"label":s["l"],"time":s["t"],"image_file":f"assets/scenes/{sid}.jpg","video_file":None})
        time.sleep(3); continue

    vurl = vres.get("video_url")
    if vurl:
        r2 = req.get(vurl, timeout=120)
        (videos_dir / f"{sid}.mp4").write_bytes(r2.content)
        print(f"  ✓ Saved video/{sid}.mp4 ({len(r2.content)//1024}KB)")
        manifest.append({"id":sid,"label":s["l"],"time":s["t"],"image_file":f"assets/scenes/{sid}.jpg","video_file":f"assets/videos/{sid}.mp4"})
    else:
        manifest.append({"id":sid,"label":s["l"],"time":s["t"],"image_file":f"assets/scenes/{sid}.jpg","video_file":None})

    time.sleep(3)

# Save
out = assets_dir / "scene_data.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n{'='*50}")
print(f"  Done! {len(manifest)}/{len(SCENES)} scenes.")
print(f"  Data: {out}")
