# generate_browser_fail.py — 브라우저 재생 실패 화면 이미지
# 실행: python generate_browser_fail.py

from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# 색상
RED        = (220, 53, 69)
DARK_NAVY  = (15, 23, 42)
GRAY       = (100, 116, 139)
LIGHT_GRAY = (241, 245, 249)
BORDER     = (203, 213, 225)
WHITE      = (255, 255, 255)
BLACK      = (26, 26, 26)
PAGE_BG    = (248, 250, 252)


def load_fonts():
    try:
        return {
            "big":    ImageFont.truetype("malgunbd.ttf", 48),
            "title":  ImageFont.truetype("malgunbd.ttf", 28),
            "label":  ImageFont.truetype("malgunbd.ttf", 20),
            "small":  ImageFont.truetype("malgun.ttf", 18),
            "mono":   ImageFont.truetype("consola.ttf", 16),
        }
    except:
        d = ImageFont.load_default()
        return {k: d for k in ["big", "title", "label", "small", "mono"]}


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
# 자물쇠 아이콘
draw.rectangle([(url_x1 + 12, url_y1 + 9), (url_x1 + 22, url_y1 + 19)], outline=GRAY, width=2)
draw.arc([(url_x1 + 13, url_y1 + 4), (url_x1 + 21, url_y1 + 13)], start=0, end=180, fill=GRAY, width=2)
draw.text((url_x1 + 32, url_y1 + 4), "localhost:8501/이벤트_다시보기",
          font=fonts["small"], fill=BLACK)

# ── 비디오 재생 영역 (실패) ────────────────────────
vx = bx + 30
vy = by + bar_h + 40
vw = bw - 60
vh = bh - bar_h - 100

# 검은 배경
draw.rounded_rectangle([(vx, vy), (vx + vw, vy + vh)],
                       radius=10, fill=DARK_NAVY)

# 중앙 경고 아이콘 (빨간 원 + 느낌표)
cx = vx + vw // 2
cy = vy + vh // 2 - 30

# 큰 원 (테두리)
r = 70
draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
             outline=RED, width=7)
# 느낌표
draw.rectangle([(cx - 6, cy - 35), (cx + 6, cy + 15)], fill=RED)
draw.ellipse([(cx - 7, cy + 22), (cx + 7, cy + 36)], fill=RED)

# 에러 메시지
err_title = "재생할 수 없는 형식입니다"
err_detail = "지원되지 않는 비디오 코덱 (mp4v / MPEG-4 Part 2)"

# 중앙 정렬
bbox1 = draw.textbbox((0, 0), err_title, font=fonts["title"])
bbox2 = draw.textbbox((0, 0), err_detail, font=fonts["small"])
tw1 = bbox1[2] - bbox1[0]
tw2 = bbox2[2] - bbox2[0]
draw.text((cx - tw1 // 2, cy + 75), err_title, font=fonts["title"], fill=(255, 120, 120))
draw.text((cx - tw2 // 2, cy + 115), err_detail, font=fonts["small"], fill=(255, 180, 180))

# ── 하단 플레이어 컨트롤 바 (비활성) ────────────────
ctrl_y = vy + vh - 40
# 재생 버튼 (회색 - 비활성)
btn_x = vx + 20
btn_y = ctrl_y + 5
draw.ellipse([(btn_x, btn_y), (btn_x + 30, btn_y + 30)],
             fill=(60, 70, 85), outline=(80, 90, 105), width=2)
draw.polygon([(btn_x + 11, btn_y + 8), (btn_x + 11, btn_y + 22), (btn_x + 23, btn_y + 15)],
             fill=(120, 130, 145))

# 진행 바 (비활성)
bar_x1 = btn_x + 50
bar_x2 = vx + vw - 120
draw.rounded_rectangle([(bar_x1, ctrl_y + 15), (bar_x2, ctrl_y + 21)],
                       radius=3, fill=(60, 70, 85))

# 시간 표시
draw.text((vx + vw - 100, ctrl_y + 10), "00:00 / --:--",
          font=fonts["mono"], fill=(120, 130, 145))

# ── 하단 라벨 (브라우저 외부) ───────────────────────
draw.text((40, H - 30), "❌ 브라우저에서 영상 클립 재생 실패",
          font=fonts["label"], fill=RED)

img.save(os.path.join(OUT, "browser_playback_fail.png"))
print(f"✅ 저장: browser_playback_fail.png")
