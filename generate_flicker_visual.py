# generate_flicker_visual.py — 실시간 영상 화면 깜빡임 시각화
# 실행: python generate_flicker_visual.py

from PIL import Image, ImageDraw, ImageFont
import os
import random

OUT = os.path.dirname(os.path.abspath(__file__))

# 색상
RED        = (220, 53, 69)
YELLOW     = (245, 158, 11)
GRAY       = (100, 116, 139)
LIGHT_GRAY = (241, 245, 249)
BORDER     = (203, 213, 225)
WHITE      = (255, 255, 255)
BLACK      = (26, 26, 26)
DARK_NAVY  = (15, 23, 42)
PAGE_BG    = (248, 250, 252)
GREEN_BOX  = (76, 175, 80)


def load_fonts():
    try:
        return {
            "big":    ImageFont.truetype("malgunbd.ttf", 48),
            "title":  ImageFont.truetype("malgunbd.ttf", 28),
            "label":  ImageFont.truetype("malgunbd.ttf", 20),
            "small":  ImageFont.truetype("malgun.ttf", 18),
            "tiny":   ImageFont.truetype("malgun.ttf", 13),
            "mono":   ImageFont.truetype("consola.ttf", 16),
        }
    except:
        d = ImageFont.load_default()
        return {k: d for k in ["big", "title", "label", "small", "tiny", "mono"]}


fonts = load_fonts()

# 캔버스
W, H = 900, 620
img  = Image.new("RGB", (W, H), PAGE_BG)
draw = ImageDraw.Draw(img)

# ── 브라우저 외곽 ──────────────────────────────────
bx, by, bw, bh = 40, 40, W - 80, H - 80
draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)],
                       radius=14, fill=WHITE, outline=GRAY, width=2)

# ── 상단 바 ──────────────────────────────────────
bar_h = 52
draw.rounded_rectangle([(bx, by), (bx + bw, by + bar_h)],
                       radius=14, fill=LIGHT_GRAY, outline=GRAY, width=2)
draw.rectangle([(bx, by + 30), (bx + bw, by + bar_h)], fill=LIGHT_GRAY)
draw.line([(bx, by + bar_h), (bx + bw, by + bar_h)], fill=BORDER, width=2)

# 신호등
for i, color in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
    cx = bx + 24 + i * 26
    draw.ellipse([(cx - 8, by + 18), (cx + 8, by + 34)], fill=color)

# URL 바
url_x1, url_y1 = bx + 130, by + 12
url_x2, url_y2 = bx + bw - 25, by + 40
draw.rounded_rectangle([(url_x1, url_y1), (url_x2, url_y2)],
                       radius=6, fill=WHITE, outline=BORDER, width=1)
draw.rectangle([(url_x1 + 12, url_y1 + 9), (url_x1 + 22, url_y1 + 19)], outline=GRAY, width=2)
draw.arc([(url_x1 + 13, url_y1 + 4), (url_x1 + 21, url_y1 + 13)], start=0, end=180, fill=GRAY, width=2)
draw.text((url_x1 + 32, url_y1 + 4), "localhost:8501/모니터링",
          font=fonts["small"], fill=BLACK)

# ── 비디오 재생 영역 (깜빡임 현상) ───────────────────
vx = bx + 30
vy = by + bar_h + 40
vw = bw - 60
vh = bh - bar_h - 100

# 반투명 흰색 플래시 오버레이 효과를 위해 먼저 어두운 배경
draw.rounded_rectangle([(vx, vy), (vx + vw, vy + vh)],
                       radius=10, fill=DARK_NAVY)

# 영상 프레임 잔상 효과 - 반쯤 그려진 영상
# 좌측 절반: 살짝 보이는 도로/차량 (희미한 회색)
for _ in range(18):
    lx = vx + random.randint(20, vw // 2)
    ly = vy + random.randint(20, vh - 40)
    lw = random.randint(40, 100)
    lh = random.randint(20, 50)
    shade = random.randint(35, 60)
    draw.rounded_rectangle([(lx, ly), (lx + lw, ly + lh)],
                            radius=3, fill=(shade, shade, shade + 5))

# 희미한 바운딩 박스 (깜빡임으로 사라졌다 나타났다)
box_alpha_img = Image.new("RGBA", (vw, vh), (0, 0, 0, 0))
box_draw = ImageDraw.Draw(box_alpha_img)
# 흐릿한 녹색 박스
box_draw.rectangle([(50, 60), (180, 170)], outline=(76, 175, 80, 100), width=3)
box_draw.rectangle([(250, 80), (380, 190)], outline=(76, 175, 80, 60), width=3)
img.paste(Image.alpha_composite(
    img.crop((vx, vy, vx + vw, vy + vh)).convert("RGBA"),
    box_alpha_img
).convert("RGB"), (vx, vy))

# 우측 절반: 강한 흰색 플래시 (깜빡임 순간 포착)
flash_x1 = vx + vw // 2
flash_img = Image.new("RGBA", (vw // 2, vh), (255, 255, 255, 220))
img.paste(Image.alpha_composite(
    img.crop((flash_x1, vy, flash_x1 + vw // 2, vy + vh)).convert("RGBA"),
    flash_img
).convert("RGB"), (flash_x1, vy))

# 플래시 경계선 (점선)
for dy in range(vy + 10, vy + vh - 10, 12):
    draw.line([(flash_x1, dy), (flash_x1, dy + 6)], fill=(255, 230, 100), width=2)

# 중앙 경고 아이콘 (깜빡임 표시) — 진한 노란색 번개
cx = vx + vw // 2 - 160
cy = vy + 50

# 번개 아이콘 (깜빡임 = flash 의미)
lightning = [
    (cx + 20, cy),
    (cx, cy + 25),
    (cx + 12, cy + 25),
    (cx + 5, cy + 50),
    (cx + 28, cy + 22),
    (cx + 16, cy + 22),
    (cx + 22, cy),
]
draw.polygon(lightning, fill=YELLOW, outline=RED)

# "FLICKER" 라벨
draw.text((cx - 10, cy + 60), "FLICKER", font=fonts["label"], fill=YELLOW)

# 상단 가로 플래시 스트라이프 (깜빡임 간격 시각화)
stripe_y = vy + 20
for i in range(6):
    sx1 = vx + 20 + i * (vw // 6)
    sx2 = sx1 + (vw // 12)
    if i % 2 == 0:
        draw.rectangle([(sx1, stripe_y), (sx2, stripe_y + 4)],
                        fill=(255, 255, 255, 180))

# 하단 에러 메시지
err_main = "⚡ 화면 깜빡임 발생"
err_sub  = "매 프레임마다 페이지 전체가 새로고침되어 흰색 플래시가 반복됨"

bbox1 = draw.textbbox((0, 0), err_main, font=fonts["title"])
bbox2 = draw.textbbox((0, 0), err_sub, font=fonts["small"])
tw1 = bbox1[2] - bbox1[0]
tw2 = bbox2[2] - bbox2[0]
tcy = vy + vh - 90
# 반투명 배경
overlay = Image.new("RGBA", (vw - 40, 70), (0, 0, 0, 180))
img.paste(overlay, (vx + 20, tcy - 5), overlay)
draw.text((vx + vw // 2 - tw1 // 2, tcy), err_main, font=fonts["title"], fill=(255, 200, 80))
draw.text((vx + vw // 2 - tw2 // 2, tcy + 38), err_sub, font=fonts["small"], fill=(255, 230, 180))

# ── 하단 FPS 지표 (비정상적으로 빠른 리프레시) ─────
ctrl_y = vy + vh - 15
# 라이브 표시
draw.ellipse([(vx + 15, ctrl_y + 2), (vx + 29, ctrl_y + 16)], fill=RED)
draw.text((vx + 35, ctrl_y), "LIVE",
          font=fonts["mono"], fill=(255, 100, 100))
draw.text((vx + 90, ctrl_y), "페이지 전체 리렌더: 30 회/초",
          font=fonts["mono"], fill=(255, 180, 180))

# ── 하단 라벨 (브라우저 외부) ───────────────────────
draw.text((40, H - 30), "⚠️ 실시간 CCTV 영상 화면 깜빡임 (플리커) 현상",
          font=fonts["label"], fill=RED)

img.save(os.path.join(OUT, "screen_flicker_issue.png"))
print(f"✅ 저장: screen_flicker_issue.png")
