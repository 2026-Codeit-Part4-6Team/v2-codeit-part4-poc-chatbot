# -*- coding: utf-8 -*-
"""
image_gen.py — 광고 이미지 생성 노드 (유료 플랜) [김재헌 담당 영역]

POC 전략: 4일/1인/무GPU 제약상 로컬 SDXL(RealVisXL+IP-Adapter)은 과함.
→ PIL로 '카피가 얹힌 브랜디드 카드 이미지'를 생성해 시연에서 눈에 보이는 산출물을 만든다.
   (파트4 팀의 backend_image_generator.py ImgGenPipeline.generate_image() 로 나중에 교체하는 슬롯.)

⚠ Cloud Run 파일시스템 이슈 회피: 파일에 저장하지 않고 **메모리(BytesIO) → base64**
   문자열로 반환한다. 이렇게 하면
     · 컨테이너 재시작/격리에 따른 404 원천 차단
     · StaticFiles / STATIC_DIR / URL fetch 로직 자체가 불필요
   응답 크기는 이미지당 30~80KB 정도로 시연용엔 문제 없음.
"""
import base64
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont

_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 채널별 캔버스 규격
_SIZES = {"instagram": (1080, 1080), "blog": (1200, 630), "banner": (1200, 400)}
_PALETTE = [((255, 138, 101), (255, 87, 34)),   # 주황
            ((77, 208, 225), (0, 151, 167)),    # 청록
            ((149, 117, 205), (94, 53, 177))]   # 보라


def image_gen_node(state) -> dict:
    """유료 플랜일 때만 호출. best_copy를 이미지 카드로 렌더링해 base64 로 반환."""
    copy_text = state.get("best_copy", "") or state.get("answer", "")
    channel = state.get("config", {}).get("channel", "instagram")
    store = state.get("store_name", "") or "우리가게"
    img_b64 = _render_card_b64(copy_text, channel, store)
    # 하위호환: image_path 필드도 채워두되(로그/DB), 실 렌더링은 image_b64 로.
    return {"image_b64": img_b64, "image_path": f"[inline_base64:{channel}]"}


def _render_card_b64(copy_text: str, channel: str, store: str) -> str:
    w, h = _SIZES.get(channel, _SIZES["instagram"])
    top, bottom = _PALETTE[hash(copy_text) % len(_PALETTE)]

    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    # 세로 그라데이션 배경
    for y in range(h):
        t = y / h
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=col)

    # 폰트 (컨테이너에 fonts-noto-cjk 설치돼 있음. 실패 시 기본 폰트로 폴백)
    try:
        f_title = ImageFont.truetype(_FONT, int(h * 0.075))
        f_store = ImageFont.truetype(_FONT, int(h * 0.045))
    except Exception:
        f_title = f_store = ImageFont.load_default()

    # 카피(첫 줄만, 래핑)
    headline = copy_text.split("\n")[0][:40]
    wrapped = textwrap.fill(headline, width=max(8, int(w / (h * 0.05))))
    draw.multiline_text((w * 0.08, h * 0.30), wrapped, font=f_title,
                        fill="white", spacing=int(h * 0.02))
    # 가게명 배지
    draw.text((w * 0.08, h * 0.80), f"@ {store}", font=f_store, fill="white")

    # BytesIO → base64 문자열 (파일 저장 없음)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


if __name__ == "__main__":
    st = {"best_copy": "시원한 여름, 오늘의 특별한 한 잔 #신메뉴 #여름한정",
          "store_name": "민재커피", "config": {"channel": "instagram"}}
    out = image_gen_node(st)
    print(f"image_b64 length: {len(out['image_b64'])} chars")

