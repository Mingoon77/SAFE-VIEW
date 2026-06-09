# generate_cloudflare_diagram.py — Cloudflare Tunnel 작동 원리 다이어그램
# 실행: python generate_cloudflare_diagram.py

import os
from PIL import Image, ImageDraw, ImageFont


OUTPUT = os.path.join(os.path.dirname(__file__), "cloudflare_tunnel_diagram.png")

W, H = 1400, 900
BG = (248, 250, 252)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)


def korean_font(size, bold=True):
    names = ["malgunbd.ttf"] if bold else ["malgun.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def mono_font(size):
    for name in ["consolab.ttf", "consola.ttf", "cour.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


FONT_TITLE     = korean_font(32, bold=True)
FONT_BOX_TITLE = korean_font(22, bold=True)
FONT_BOX_SUB   = korean_font(16, bold=False)
FONT_LABEL     = korean_font(17, bold=True)
FONT_FOOTER    = korean_font(15, bold=False)


# ── 색상 ───────────────────────────────────────────
LOCAL_COLOR = (76, 175, 80)
LOCAL_BG    = (232, 245, 233)
CF_COLOR    = (244, 129, 32)
CF_BG       = (255, 237, 217)
USER_COLOR  = (59, 130, 246)
USER_BG     = (219, 234, 254)
TEXT_DARK   = (33, 33, 33)
TEXT_GRAY   = (100, 116, 139)
ARROW_GREEN = (34, 134, 58)
ARROW_BLUE  = (29, 78, 216)
WHITE       = (255, 255, 255)


# ── 타이틀 ─────────────────────────────────────────
title = "Cloudflare Tunnel 외부 배포 동작 원리"
bb = draw.textbbox((0, 0), title, font=FONT_TITLE)
tw = bb[2] - bb[0]
draw.text(((W - tw) // 2, 30), title, font=FONT_TITLE, fill=TEXT_DARK)
draw.rectangle([(80, 90), (W - 80, 92)], fill=(226, 232, 240))


# ── 박스 3개 ────────────────────────────────────────
BOX_W = 320
BOX_H = 220
Y_BOX = 250
GAP = (W - BOX_W * 3) // 4

x1 = GAP
x2 = GAP * 2 + BOX_W
x3 = GAP * 3 + BOX_W * 2


def draw_box(x, y, w, h, color, bg_color, title_text, lines):
    draw.rounded_rectangle(
        [(x, y), (x + w, y + h)],
        radius=20, fill=bg_color, outline=color, width=3,
    )
    # 타이틀 바
    draw.rounded_rectangle(
        [(x, y), (x + w, y + 60)],
        radius=20, fill=color,
    )
    draw.rectangle([(x, y + 30), (x + w, y + 60)], fill=color)
    # 타이틀
    bb = draw.textbbox((0, 0), title_text, font=FONT_BOX_TITLE)
    tw = bb[2] - bb[0]
    draw.text((x + (w - tw) // 2, y + 16), title_text, font=FONT_BOX_TITLE, fill=WHITE)
    # 내용
    cy = y + 80
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=FONT_BOX_SUB)
        tw = bb[2] - bb[0]
        draw.text((x + (w - tw) // 2, cy), line, font=FONT_BOX_SUB, fill=TEXT_DARK)
        cy += 32


draw_box(x1, Y_BOX, BOX_W, BOX_H, LOCAL_COLOR, LOCAL_BG, "로컬 PC", [
    "Streamlit 앱",
    "localhost : 8501",
    "",
    "cloudflared 실행 중",
])

draw_box(x2, Y_BOX, BOX_W, BOX_H, CF_COLOR, CF_BG, "Cloudflare Network", [
    "HTTPS 터널 연결",
    "자동 SSL 인증서 발급",
    "",
    "trycloudflare.com 도메인",
])

draw_box(x3, Y_BOX, BOX_W, BOX_H, USER_COLOR, USER_BG, "외부 사용자", [
    "팀원 / 평가자",
    "( PC · 태블릿 · 모바일 )",
    "",
    "별도 설치 / 설정 없음",
])


# ── 화살표 ─────────────────────────────────────────
y_arrow = Y_BOX + BOX_H // 2


def draw_arrow(sx, ex, y, color, label_top=None, label_bot=None):
    draw.line([(sx, y), (ex, y)], fill=color, width=4)
    head = 12
    if ex > sx:
        draw.polygon([
            (ex, y),
            (ex - head, y - head // 2 - 3),
            (ex - head, y + head // 2 + 3),
        ], fill=color)
    else:
        draw.polygon([
            (ex, y),
            (ex + head, y - head // 2 - 3),
            (ex + head, y + head // 2 + 3),
        ], fill=color)
    if label_top:
        bb = draw.textbbox((0, 0), label_top, font=FONT_LABEL)
        tw = bb[2] - bb[0]
        cx = (sx + ex) // 2
        draw.text((cx - tw // 2, y - 32), label_top, font=FONT_LABEL, fill=color)
    if label_bot:
        bb = draw.textbbox((0, 0), label_bot, font=FONT_LABEL)
        tw = bb[2] - bb[0]
        cx = (sx + ex) // 2
        draw.text((cx - tw // 2, y + 12), label_bot, font=FONT_LABEL, fill=color)


# 로컬 ↔ 클플
draw_arrow(x1 + BOX_W + 5, x2 - 5, y_arrow - 25, ARROW_GREEN, label_top="아웃바운드 연결")
draw_arrow(x2 - 5, x1 + BOX_W + 5, y_arrow + 25, ARROW_GREEN, label_bot="요청 포워딩")

# 클플 ↔ 사용자
draw_arrow(x2 + BOX_W + 5, x3 - 5, y_arrow - 25, ARROW_BLUE, label_top="HTTPS 응답")
draw_arrow(x3 - 5, x2 + BOX_W + 5, y_arrow + 25, ARROW_BLUE, label_bot="HTTPS 요청")


# ── 명령어 박스 ────────────────────────────────────
cmd_y, cmd_h = 590, 100
draw.rounded_rectangle(
    [(80, cmd_y), (W - 80, cmd_y + cmd_h)],
    radius=15, fill=(30, 30, 30), outline=(60, 60, 60), width=2,
)
draw.text((100, cmd_y + 15), "사용 명령어", font=FONT_BOX_TITLE, fill=(248, 250, 252))

cmd_text = "$ cloudflared tunnel --url http://localhost:8501"
draw.text((100, cmd_y + 55), cmd_text, font=mono_font(22), fill=(86, 220, 167))


# ── 결과 박스 ──────────────────────────────────────
res_y, res_h = 720, 100
draw.rounded_rectangle(
    [(80, res_y), (W - 80, res_y + res_h)],
    radius=15, fill=(255, 248, 225), outline=(245, 158, 11), width=2,
)
draw.text((100, res_y + 15), "생성 결과 (예시)", font=FONT_BOX_TITLE, fill=(133, 77, 14))

result_url = "https://gap-experimental-whereas-geographical.trycloudflare.com"
draw.text((100, res_y + 55), result_url, font=mono_font(20), fill=(124, 45, 18))


# ── 푸터 ───────────────────────────────────────────
footer = "장점 : 별도 서버 / 도메인 불필요 · HTTPS 자동 적용 · 무료 무제한 대역폭"
bb = draw.textbbox((0, 0), footer, font=FONT_FOOTER)
tw = bb[2] - bb[0]
draw.text(((W - tw) // 2, H - 40), footer, font=FONT_FOOTER, fill=TEXT_GRAY)


img.save(OUTPUT)
print(f"[완료] 다이어그램 저장 → {OUTPUT}")

try:
    os.startfile(OUTPUT)
    print("[열기] 기본 이미지 뷰어에서 여는 중...")
except Exception as e:
    print(f"[실패] 자동 열기 실패: {e}")
