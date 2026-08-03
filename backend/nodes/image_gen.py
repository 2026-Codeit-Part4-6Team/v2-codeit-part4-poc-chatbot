# -*- coding: utf-8 -*-
"""
image_gen.py — 광고 이미지 생성 노드 (유료 플랜) [김재헌 담당 영역]

POC 전략: 4일/1인/무GPU 제약상 로컬 SDXL(RealVisXL+IP-Adapter)은 과함.
→ PIL로 '카피가 얹힌 브랜디드 카드 이미지'를 생성해 시연에서 눈에 보이는 산출물을 만든다.
   (파트4 팀의 backend_image_generator.py ImgGenPipeline.generate_image() 로 나중에 교체하는 슬롯.)
실 API로 바꾸려면 _render_card() 대신 SDXL/Gemini 호출만 끼우면 된다(인터페이스 유지).
"""
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# 이미지 저장 위치: 배포 환경(Cloud Run) 에서는 STATIC_DIR 환경변수로 지정한
# 쓰기 가능한 경로(/tmp/adcopilot_output)를 사용한다. 로컬 개발에서는 프로젝트
# 루트 output/ 로 폴백. main.py 가 이 경로를 /static 으로 mount 해 URL 서빙한다.
_OUT_DIR = os.getenv(
    "STATIC_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "output"),
)
os.makedirs(_OUT_DIR, exist_ok=True)
_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 채널별 캔버스 규격
_SIZES = {"instagram": (1080, 1080), "blog": (1200, 630), "banner": (1200, 400)}
_PALETTE = [((255, 138, 101), (255, 87, 34)),   # 주황
            ((77, 208, 225), (0, 151, 167)),    # 청록
            ((149, 117, 205), (94, 53, 177))]   # 보라


def image_gen_node(state) -> dict:
    """유료 플랜일 때만 호출. best_copy를 이미지 카드로 렌더링."""
    copy_text = state.get("best_copy", "") or state.get("answer", "")
    channel = state.get("config", {}).get("channel", "instagram")
    store = state.get("store_name", "") or "우리가게"
    path = _render_card(copy_text, channel, store)
    return {"image_path": path}


def _render_card(copy_text: str, channel: str, store: str) -> str:
    w, h = _SIZES.get(channel, _SIZES["instagram"])
    top, bottom = _PALETTE[hash(copy_text) % len(_PALETTE)]

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    # 세로 그라데이션 배경
    for y in range(h):
        t = y / h
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=col)

    # 폰트
    try:
        f_title = ImageFont.truetype(_FONT, int(h * 0.075))
        f_store = ImageFont.truetype(_FONT, int(h * 0.045))
    except Exception:
        f_title = f_store = ImageFont.load_default()

    # 카피(첫 2줄만, 래핑)
    headline = copy_text.split("\n")[0][:40]
    wrapped = textwrap.fill(headline, width=max(8, int(w / (h * 0.05))))
    draw.multiline_text((w * 0.08, h * 0.30), wrapped, font=f_title,
                        fill="white", spacing=int(h * 0.02))
    # 가게명 배지
    draw.text((w * 0.08, h * 0.80), f"@ {store}", font=f_store, fill="white")

    fname = f"ad_{channel}_{datetime.now():%Y%m%d_%H%M%S}.png"
    fpath = os.path.join(_OUT_DIR, fname)
    img.save(fpath)
    return fpath


if __name__ == "__main__":
    st = {"best_copy": "시원한 여름, 오늘의 특별한 한 잔 #신메뉴 #여름한정",
          "store_name": "민재커피", "config": {"channel": "instagram"}}
    print("이미지 생성:", image_gen_node(st)["image_path"])
