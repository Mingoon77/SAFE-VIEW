# generate_clip_issue_visual.py — 영상 클립 재생 이슈 시각화
# 실행: python generate_clip_issue_visual.py

from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# 색상
RED        = (220, 53, 69)
GREEN      = (40, 167, 69)
BLUE       = (59, 130, 246)
PURPLE     = (147, 51, 234)
AMBER      = (245, 158, 11)
DARK_NAVY  = (15, 23, 42)
GRAY       = (100, 116, 139)
LIGHT_GRAY = (241, 245, 249)
BORDER     = (226, 232, 240)
WHITE      = (255, 255, 255)
BLACK      = (26, 26, 26)
PAGE_BG    = (248, 250, 252)


def load_fonts():
    try:
        return {
            "title":   ImageFont.truetype("malgunbd.ttf", 34),
            "section": ImageFont.truetype("malgunbd.ttf", 22),
            "label":   ImageFont.truetype("malgunbd.ttf", 16),
            "small":   ImageFont.truetype("malgun.ttf", 14),
            "mono":    ImageFont.truetype("consolab.ttf", 16),
        }
    except:
        default = ImageFont.load_default()
        return {k: default for k in ["title", "section", "label", "small", "mono"]}


def draw_box(draw, x, y, w, h, color=WHITE, border=BORDER, radius=12):
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius,
                           fill=color, outline=border, width=2)


def draw_arrow(draw, x1, y1, x2, y2, color=GRAY, width=3):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # 화살촉
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    ah = 10
    p1 = (x2 - ah * math.cos(angle - 0.5), y2 - ah * math.sin(angle - 0.5))
    p2 = (x2 - ah * math.cos(angle + 0.5), y2 - ah * math.sin(angle + 0.5))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def draw_browser(draw, x, y, w, h, status, fonts):
    """브라우저 모양 + 재생 영역 그리기. status: 'fail' or 'success'"""
    # 브라우저 외곽
    draw_box(draw, x, y, w, h, color=WHITE, border=GRAY)
    # 상단 바
    draw.rounded_rectangle([(x, y), (x + w, y + 30)], radius=12,
                           fill=LIGHT_GRAY, outline=GRAY, width=2)
    draw.rectangle([(x, y + 18), (x + w, y + 30)], fill=LIGHT_GRAY)
    # 신호등
    for i, color in enumerate([(255, 95, 87), (255, 189, 46), (40, 200, 64)]):
        cx = x + 15 + i * 18
        draw.ellipse([(cx - 5, y + 10), (cx + 5, y + 20)], fill=color)
    # URL 바
    draw.rounded_rectangle([(x + 80, y + 7), (x + w - 15, y + 23)],
                           radius=4, fill=WHITE, outline=BORDER, width=1)
    draw.text((x + 88, y + 9), "localhost:8501", font=fonts["small"], fill=GRAY)

    # 비디오 영역
    video_x = x + 15
    video_y = y + 45
    video_w = w - 30
    video_h = h - 60

    if status == "fail":
        # 검은 화면 + X 표시
        draw.rectangle([(video_x, video_y), (video_x + video_w, video_y + video_h)],
                        fill=DARK_NAVY)
        # 경고 아이콘 (X)
        cx = video_x + video_w // 2
        cy = video_y + video_h // 2
        draw.ellipse([(cx - 40, cy - 50), (cx + 40, cy + 30)],
                      outline=RED, width=5)
        draw.text((cx - 8, cy - 24), "!", font=fonts["title"], fill=RED)
        # 에러 텍스트
        draw.text((cx - 95, cy + 40), "재생할 수 없는 형식", font=fonts["label"], fill=(255, 120, 120))
    else:
        # 재생 성공 - 영상 프레임 흉내 (녹색 계열)
        draw.rectangle([(video_x, video_y), (video_x + video_w, video_y + video_h)],
                        fill=(30, 60, 50))
        # 재생 아이콘 (삼각형)
        cx = video_x + video_w // 2
        cy = video_y + video_h // 2
        draw.polygon([(cx - 20, cy - 25), (cx - 20, cy + 25), (cx + 25, cy)],
                      fill=(180, 255, 200))
        draw.text((cx - 60, cy + 40), "정상 재생", font=fonts["label"], fill=(180, 255, 200))


def draw_file_icon(draw, x, y, label, ext, color, fonts, w=100, h=120):
    """파일 아이콘 그리기"""
    # 접힌 모서리 효과
    points = [
        (x, y),
        (x + w - 20, y),
        (x + w, y + 20),
        (x + w, y + h),
        (x, y + h),
    ]
    draw.polygon(points, fill=WHITE, outline=color)
    # 외곽선 (굵게)
    for i in range(len(points)):
        draw.line([points[i], points[(i + 1) % len(points)]], fill=color, width=3)
    # 접힌 모서리 삼각형
    draw.polygon([(x + w - 20, y), (x + w - 20, y + 20), (x + w, y + 20)],
                  fill=color)
    # 확장자 배지
    draw.rounded_rectangle([(x + 10, y + 45), (x + w - 10, y + 72)],
                            radius=4, fill=color)
    draw.text((x + 18, y + 48), ext, font=fonts["label"], fill=WHITE)
    # 라벨
    draw.text((x, y + h + 10), label, font=fonts["small"], fill=BLACK)


def draw_tool_icon(draw, x, y, label, sublabel, color, fonts, w=140, h=80):
    """도구 아이콘 (FFmpeg 등)"""
    draw_box(draw, x, y, w, h, color=color, border=color, radius=12)
    draw.text((x + 15, y + 18), label, font=fonts["section"], fill=WHITE)
    draw.text((x + 15, y + 50), sublabel, font=fonts["small"], fill=(230, 230, 230))


# ══════════════════════════════════════════════════════
# 이미지 생성
# ══════════════════════════════════════════════════════
fonts = load_fonts()

W, H = 2000, 1200
img  = Image.new("RGB", (W, H), PAGE_BG)
draw = ImageDraw.Draw(img)

# ── 메인 타이틀 ──
draw.text((40, 30), "영상 클립 브라우저 재생 문제 — 해결 과정", font=fonts["title"], fill=BLACK)
draw.line([(40, 85), (W - 40, 85)], fill=BORDER, width=2)

# ══════════════════════════════════════════════════════
# BEFORE (상단)
# ══════════════════════════════════════════════════════
draw.rounded_rectangle([(40, 110), (W - 40, 150)], radius=10,
                        fill=RED, outline=RED)
draw.text((60, 118), "Before — 저장은 되지만 브라우저에서 재생 불가",
            font=fonts["section"], fill=WHITE)

# 흐름: CCTV → OpenCV(mp4v) → 파일 → 브라우저(실패)
y_flow = 200

# CCTV 카메라
cam_x, cam_y = 70, y_flow
draw_box(draw, cam_x, cam_y, 160, 120, color=WHITE, border=BLUE)
draw.text((cam_x + 60, cam_y + 15), "📹",
            font=ImageFont.truetype("seguiemj.ttf", 40) if os.path.exists("C:/Windows/Fonts/seguiemj.ttf") else fonts["title"],
            fill=BLUE)
draw.text((cam_x + 45, cam_y + 70), "CCTV / 영상", font=fonts["label"], fill=BLACK)
draw.text((cam_x + 60, cam_y + 95), "프레임", font=fonts["small"], fill=GRAY)

# OpenCV (mp4v)
ocv_x = 300
draw_tool_icon(draw, ocv_x, y_flow + 20, "OpenCV", "fourcc: mp4v", BLUE, fonts, w=160, h=80)

# 파일
file_x = 530
draw_file_icon(draw, file_x, y_flow, "clip_xxx.mp4", "mp4v", AMBER, fonts)

# 브라우저 (실패)
br_x = 800
draw_browser(draw, br_x, y_flow - 30, 400, 220, "fail", fonts)

# 화살표
draw_arrow(draw, 240, y_flow + 60, 290, y_flow + 60, GRAY)
draw_arrow(draw, 470, y_flow + 60, 520, y_flow + 60, GRAY)
draw_arrow(draw, 640, y_flow + 60, 780, y_flow + 60, GRAY)

# 실패 설명
draw.rounded_rectangle([(1230, y_flow - 30), (W - 60, y_flow + 190)],
                        radius=12, fill=(254, 242, 242), outline=RED, width=2)
draw.text((1250, y_flow - 10), "🔍 원인", font=fonts["section"], fill=RED)
draw.text((1250, y_flow + 25),
            "• OpenCV 기본 mp4v 코덱 = MPEG-4 Part 2",
            font=fonts["small"], fill=BLACK)
draw.text((1250, y_flow + 55),
            "• 모던 브라우저 HTML5 Video는 H.264 필요",
            font=fonts["small"], fill=BLACK)
draw.text((1250, y_flow + 85),
            "• 파일은 생성되지만 <video> 태그에서 재생 불가",
            font=fonts["small"], fill=BLACK)
draw.text((1250, y_flow + 115),
            "• VLC 등 로컬 플레이어는 재생되어 혼란 유발",
            font=fonts["small"], fill=BLACK)
draw.text((1250, y_flow + 150),
            "→ 사용자는 매번 다운로드 후 외부 재생해야 함",
            font=fonts["label"], fill=RED)


# ══════════════════════════════════════════════════════
# AFTER (하단)
# ══════════════════════════════════════════════════════
draw.rounded_rectangle([(40, 630), (W - 40, 670)], radius=10,
                        fill=GREEN, outline=GREEN)
draw.text((60, 638), "After — FFmpeg 자동 변환 + 캐싱으로 브라우저 직접 재생",
            font=fonts["section"], fill=WHITE)

y_flow2 = 720

# CCTV
draw_box(draw, 70, y_flow2, 160, 120, color=WHITE, border=BLUE)
draw.text((130, y_flow2 + 15), "📹",
            font=ImageFont.truetype("seguiemj.ttf", 40) if os.path.exists("C:/Windows/Fonts/seguiemj.ttf") else fonts["title"],
            fill=BLUE)
draw.text((115, y_flow2 + 70), "CCTV / 영상", font=fonts["label"], fill=BLACK)
draw.text((130, y_flow2 + 95), "프레임", font=fonts["small"], fill=GRAY)

# 원본 파일
draw_file_icon(draw, 300, y_flow2, "clip_xxx.mp4", "mp4v", AMBER, fonts)

# FFmpeg
draw_tool_icon(draw, 480, y_flow2 + 20, "FFmpeg", "libx264 변환", PURPLE, fonts, w=170, h=80)

# 변환된 파일 + 캐시 표시
draw_file_icon(draw, 720, y_flow2, "_converted/clip.mp4", "H.264", GREEN, fonts)
# 캐시 아이콘
draw.rounded_rectangle([(720, y_flow2 - 30), (820, y_flow2 - 5)],
                        radius=6, fill=AMBER, outline=AMBER)
draw.text((732, y_flow2 - 27), "💾 캐싱됨", font=fonts["small"], fill=WHITE)

# 브라우저 (성공)
draw_browser(draw, 900, y_flow2 - 30, 400, 220, "success", fonts)

# 화살표
draw_arrow(draw, 240, y_flow2 + 60, 290, y_flow2 + 60, GRAY)
draw_arrow(draw, 410, y_flow2 + 60, 470, y_flow2 + 60, GRAY)
draw_arrow(draw, 660, y_flow2 + 60, 710, y_flow2 + 60, GRAY)
draw_arrow(draw, 830, y_flow2 + 60, 880, y_flow2 + 60, GRAY)

# 성공 설명
draw.rounded_rectangle([(1330, y_flow2 - 30), (W - 60, y_flow2 + 190)],
                        radius=12, fill=(232, 245, 233), outline=GREEN, width=2)
draw.text((1350, y_flow2 - 10), "✅ 해결", font=fonts["section"], fill=GREEN)
draw.text((1350, y_flow2 + 25),
            "• imageio-ffmpeg: 내장 FFmpeg 바이너리 제공",
            font=fonts["small"], fill=BLACK)
draw.text((1350, y_flow2 + 55),
            "• libx264 코덱 + faststart로 웹 스트리밍 최적화",
            font=fonts["small"], fill=BLACK)
draw.text((1350, y_flow2 + 85),
            "• 첫 재생 시 1회 변환 → _converted/ 폴더에 캐싱",
            font=fonts["small"], fill=BLACK)
draw.text((1350, y_flow2 + 115),
            "• 재재생 시 캐시 파일 즉시 반환 (변환 없음)",
            font=fonts["small"], fill=BLACK)
draw.text((1350, y_flow2 + 150),
            "→ 다운로드 없이 페이지 내 즉시 재생 가능",
            font=fonts["label"], fill=GREEN)


# ══════════════════════════════════════════════════════
# 하단 결과 비교 표
# ══════════════════════════════════════════════════════
tbl_y = 1020
draw.text((40, tbl_y - 10), "📊 결과 비교", font=fonts["section"], fill=BLACK)

rows = [
    ("항목",          "Before",                     "After"),
    ("브라우저 재생", "❌ 불가",                    "✅ 즉시 재생"),
    ("사용자 동선",   "파일 다운로드 → VLC 실행",   "페이지 내 바로 재생"),
    ("변환 시간",     "—",                          "최초 1회 (1~2초)"),
]

col_x = [60, 700, 1300]
col_w = [620, 580, 620]

for i, (c1, c2, c3) in enumerate(rows):
    y = tbl_y + 30 + i * 42
    is_header = (i == 0)
    bg = (46, 125, 50) if is_header else (LIGHT_GRAY if i % 2 == 0 else WHITE)
    text_color = WHITE if is_header else BLACK
    draw.rounded_rectangle([(40, y), (W - 40, y + 36)], radius=6,
                            fill=bg, outline=BORDER, width=1)
    draw.text((col_x[0], y + 8), c1, font=fonts["label"], fill=text_color)
    color2 = RED if (not is_header and i == 1) else text_color
    color3 = GREEN if not is_header else text_color
    draw.text((col_x[1], y + 8), c2, font=fonts["label"], fill=color2)
    draw.text((col_x[2], y + 8), c3, font=fonts["label"], fill=color3)


img.save(os.path.join(OUT, "clip_issue_visual.png"))
print(f"✅ 저장: {os.path.join(OUT, 'clip_issue_visual.png')}")
