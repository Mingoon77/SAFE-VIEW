# generate_report_assets.py — 결과 보고서(HWP)용 흐름도 이미지 생성
# A4 본문 너비(약 1200px)에 맞춰 디자인됨
# 실행: python generate_report_assets.py

from PIL import Image, ImageDraw, ImageFont
import os, math

OUT = os.path.dirname(os.path.abspath(__file__))

# ── 공통 색상 ─────────────────────────────────────────
WHITE       = (255, 255, 255)
BLACK       = (26, 26, 26)
GRAY        = (100, 116, 139)
BORDER      = (203, 213, 225)
LIGHT_GRAY  = (241, 245, 249)
PAGE_BG     = (248, 250, 252)
GREEN       = (76, 175, 80)
DARK_GREEN  = (46, 125, 50)
BG_GREEN    = (232, 245, 233)
RED         = (220, 53, 69)
ORANGE      = (234, 88, 12)
BLUE        = (59, 130, 246)
PURPLE      = (147, 51, 234)
AMBER       = (245, 158, 11)
CYAN        = (6, 182, 212)


def load_fonts():
    try:
        return {
            "title":   ImageFont.truetype("malgunbd.ttf", 26),
            "section": ImageFont.truetype("malgunbd.ttf", 18),
            "label":   ImageFont.truetype("malgunbd.ttf", 14),
            "small":   ImageFont.truetype("malgun.ttf", 12),
            "tiny":    ImageFont.truetype("malgun.ttf", 11),
        }
    except:
        d = ImageFont.load_default()
        return {k: d for k in ["title", "section", "label", "small", "tiny"]}


def draw_round_box(draw, x, y, w, h, fill, border=None, radius=10, border_width=2):
    draw.rounded_rectangle([(x, y), (x + w, y + h)], radius=radius,
                           fill=fill, outline=border, width=border_width)


def draw_arrow(draw, x1, y1, x2, y2, color=GRAY, width=2):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    ah = 8
    p1 = (x2 - ah * math.cos(angle - 0.5), y2 - ah * math.sin(angle - 0.5))
    p2 = (x2 - ah * math.cos(angle + 0.5), y2 - ah * math.sin(angle + 0.5))
    draw.polygon([(x2, y2), p1, p2], fill=color)


def center_text(draw, x, y, w, h, text, font, color=BLACK):
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text((x + (w - tw) // 2, y + (h - th) // 2 - 2),
              text, font=font, fill=color)


# ══════════════════════════════════════════════════════
# 1. 전체 시스템 흐름도 (세로형, A4 본문 너비에 맞춤)
# ══════════════════════════════════════════════════════
def make_overall_flow():
    # 박스 안 글씨 크기 키운 버전 (가시성 강화)
    try:
        font_title  = ImageFont.truetype("malgunbd.ttf", 28)
        font_header = ImageFont.truetype("malgunbd.ttf", 24)
        font_body   = ImageFont.truetype("malgun.ttf",   18)
    except:
        d = ImageFont.load_default()
        font_title = font_header = font_body = d

    W, H = 1200, 1600
    img = Image.new("RGB", (W, H), PAGE_BG)
    draw = ImageDraw.Draw(img)

    draw.text((40, 30), "시스템 전체 흐름도", font=font_title, fill=BLACK)
    draw.line([(40, 80), (W - 40, 80)], fill=BORDER, width=2)

    stages = [
        ("입력 (Input)",   "CCTV 카메라 (RTSP) / 로컬 영상 파일",                    BLUE),
        ("전처리",          "OpenCV 프레임 추출\n야간 자동 밝기 보정 (CLAHE)",          CYAN),
        ("객체 인식",       "YOLOv8 (nano) 추론\nperson · car 클래스 필터링",          PURPLE),
        ("정지 차량 판정",  "좌표 비교 기반 자체 알고리즘\n10초 이상 이동량 30px 미만 → pk.car", AMBER),
        ("위험 판단",       "(이동) 차량 + 사람 동시 존재\n사람의 발 위치 ∈ ROI → 위험 상태", DARK_GREEN),
        ("시각·청각 경고",  "빨간 테두리 + 경고 텍스트\n경고음 (Web Audio API) 자동 재생", RED),
        ("이벤트 자동 저장","캡처 이미지 · 전 5초 + 후 10초 클립 영상\nCSV 로그 기록", ORANGE),
    ]

    box_w   = 880
    box_h   = 150
    header_h = 50
    line_h  = 28
    gap     = 30
    start_y = 120

    for i, (title, desc, color) in enumerate(stages):
        x = (W - box_w) // 2
        y = start_y + i * (box_h + gap)

        # 컬러 헤더
        draw.rounded_rectangle([(x, y), (x + box_w, y + header_h)],
                               radius=12, fill=color)
        center_text(draw, x, y, box_w, header_h, title, font_header, WHITE)

        # 본문 박스
        draw.rounded_rectangle([(x, y + header_h), (x + box_w, y + box_h)],
                               radius=12, fill=WHITE, outline=color, width=2)

        # 본문 텍스트 (가운데 정렬, 줄 간격 키움)
        lines = desc.split("\n")
        total_h = len(lines) * line_h
        text_start_y = y + header_h + ((box_h - header_h) - total_h) // 2
        for j, line in enumerate(lines):
            lbb = draw.textbbox((0, 0), line, font=font_body)
            lw  = lbb[2] - lbb[0]
            draw.text((x + (box_w - lw) // 2,
                       text_start_y + j * line_h),
                      line, font=font_body, fill=BLACK)

        # 다음 단계로 화살표
        if i < len(stages) - 1:
            ax = W // 2
            draw_arrow(draw, ax, y + box_h + 8, ax, y + box_h + gap - 8,
                       color=GRAY, width=4)

    img.save(os.path.join(OUT, "report_overall_flow.png"))
    print("  ✅ report_overall_flow.png  (세로 1200x1600, 컴팩트)")


# ══════════════════════════════════════════════════════
# 2. 위험 판단 로직 흐름도 (A4 본문 너비)
# ══════════════════════════════════════════════════════
def make_danger_logic_flow():
    fonts = load_fonts()
    W, H = 1200, 1100
    img = Image.new("RGB", (W, H), PAGE_BG)
    draw = ImageDraw.Draw(img)

    draw.text((40, 30), "위험 판단 로직 흐름도", font=fonts["title"], fill=BLACK)
    draw.line([(40, 75), (W - 40, 75)], fill=BORDER, width=2)

    cx = W // 2

    def diamond(cx, cy, w, h, text, color):
        pts = [(cx, cy - h//2), (cx + w//2, cy), (cx, cy + h//2), (cx - w//2, cy)]
        draw.polygon(pts, fill=WHITE, outline=color)
        for i in range(len(pts)):
            draw.line([pts[i], pts[(i + 1) % len(pts)]], fill=color, width=3)
        lines = text.split("\n")
        for i, line in enumerate(lines):
            bb = draw.textbbox((0, 0), line, font=fonts["small"])
            lw = bb[2] - bb[0]
            draw.text((cx - lw // 2, cy - 9 + (i - (len(lines)-1)/2) * 20),
                      line, font=fonts["small"], fill=BLACK)

    def box(cy, color, title, height=60):
        x = cx - 150
        draw_round_box(draw, x, cy, 300, height, WHITE, color, 10, 2)
        draw.rounded_rectangle([(x, cy), (x + 8, cy + height)], radius=4, fill=color)
        center_text(draw, x, cy, 300, height, title, fonts["label"], BLACK)

    # 시작
    box(110, BLUE, "프레임 수신 및 YOLOv8 객체 탐지")

    # 판단 1
    draw_arrow(draw, cx, 175, cx, 215, GRAY, 3)
    diamond(cx, 260, 340, 90, "사람 객체 존재?", DARK_GREEN)
    draw.text((cx + 180, 250), "NO →", font=fonts["small"], fill=GRAY)
    draw.text((cx + 245, 250), "정상", font=fonts["label"], fill=GREEN)

    # 판단 2
    draw_arrow(draw, cx, 305, cx, 360, GRAY, 3)
    diamond(cx, 415, 420, 95, "이동 차량 존재?\n(정지 차량 제외)", DARK_GREEN)
    draw.text((cx + 220, 405), "NO →", font=fonts["small"], fill=GRAY)
    draw.text((cx + 285, 405), "정상", font=fonts["label"], fill=GREEN)

    # 판단 3
    draw_arrow(draw, cx, 463, cx, 525, GRAY, 3)
    diamond(cx, 580, 420, 100, "사람의 발 위치가\nROI 내부?", DARK_GREEN)
    draw.text((cx + 220, 570), "NO →", font=fonts["small"], fill=GRAY)
    draw.text((cx + 285, 570), "정상", font=fonts["label"], fill=GREEN)

    # 위험 판정
    draw_arrow(draw, cx, 630, cx, 695, RED, 3)
    draw.rounded_rectangle([(cx - 180, 695), (cx + 180, 770)],
                            radius=14, fill=RED)
    center_text(draw, cx - 180, 695, 360, 75, "🚨 위험 (Danger)",
                fonts["section"], WHITE)

    # 이벤트
    draw_arrow(draw, cx, 775, cx, 820, GRAY, 3)
    box(820, AMBER, "이전 상태가 정상 → 위험 전환?", 55)

    # 분기
    draw_arrow(draw, cx - 120, 880, cx - 180, 940, GRAY, 2)
    draw_arrow(draw, cx + 120, 880, cx + 180, 940, GRAY, 2)

    # 결과 박스 2개
    draw.rounded_rectangle([(50, 940), (580, 1050)],
                           radius=12, fill=BG_GREEN, outline=DARK_GREEN, width=2)
    draw.text((70, 955), "✅ 이벤트 트리거 (YES)",
              font=fonts["label"], fill=DARK_GREEN)
    draw.text((70, 985),
              "이미지 저장 → 후속 10초 녹화 → 클립 저장 → 경고음",
              font=fonts["small"], fill=BLACK)
    draw.text((70, 1010),
              "쿨다운 15초 적용 (중복 발생 방지)",
              font=fonts["small"], fill=BLACK)

    draw.rounded_rectangle([(620, 940), (W - 50, 1050)],
                           radius=12, fill=LIGHT_GRAY, outline=GRAY, width=2)
    draw.text((640, 955), "⏸ 상태 유지 (NO)",
              font=fonts["label"], fill=GRAY)
    draw.text((640, 985), "위험 상태 유지, 이벤트 중복 발생 방지",
              font=fonts["small"], fill=BLACK)

    img.save(os.path.join(OUT, "report_danger_flow.png"))
    print("  ✅ report_danger_flow.png   (1200x1100)")


# ══════════════════════════════════════════════════════
# 3. 정지 차량 판정 흐름도 (A4 본문 너비)
# ══════════════════════════════════════════════════════
def make_parked_detection_flow():
    # 세로 비율 + 글씨 키운 버전
    try:
        font_title = ImageFont.truetype("malgunbd.ttf", 30)
        font_sub   = ImageFont.truetype("malgun.ttf", 16)
        font_num   = ImageFont.truetype("malgunbd.ttf", 28)
        font_step  = ImageFont.truetype("malgunbd.ttf", 20)
        font_desc  = ImageFont.truetype("malgun.ttf", 16)
    except:
        d = ImageFont.load_default()
        font_title = font_sub = font_num = font_step = font_desc = d

    W, H = 1200, 1500
    img = Image.new("RGB", (W, H), PAGE_BG)
    draw = ImageDraw.Draw(img)

    # 제목
    draw.text((40, 30), "정지 차량 판정 알고리즘",
              font=font_title, fill=BLACK)
    draw.text((40, 75),
              "AI 객체 추적(ByteTrack 등) 사용하지 않고 YOLO 좌표만으로 정지 여부 판정",
              font=font_sub, fill=GRAY)
    draw.line([(40, 115), (W - 40, 115)], fill=BORDER, width=2)

    steps = [
        ("1", "프레임의 차량 중심 좌표 추출",
         "YOLOv8 결과에서 class='car' 박스의 중심 (cx, cy) 계산"),
        ("2", "기존 슬롯과 거리 매칭",
         "현재 좌표와 가장 가까운 슬롯(MATCH_DISTANCE_PX=80) 찾아 매칭"),
        ("3", "매칭 성공 → 위치 이력에 추가",
         "(현재시각, 좌표) 형식으로 슬롯에 누적 저장"),
        ("4", "10초 이전 위치와 비교",
         "현재 좌표와 10초 전 좌표의 유클리드 거리(현재좌표 − 10초전좌표) 측정"),
        ("5", "거리 < 30px → 정지 차량 판정",
         "is_parked=True 플래그 부여, 위험 판단에서 제외, pk.car 라벨"),
    ]

    box_h    = 110
    gap      = 60
    circle_w = 75
    y = 160

    for num, title, desc in steps:
        # 번호 원
        cy = y + box_h // 2
        draw.ellipse([(70, cy - circle_w // 2),
                      (70 + circle_w, cy + circle_w // 2)],
                     fill=DARK_GREEN)
        center_text(draw, 70, cy - circle_w // 2,
                    circle_w, circle_w, num, font_num, WHITE)

        # 본문 박스
        bx = 180
        bw = W - bx - 50
        draw_round_box(draw, bx, y, bw, box_h, WHITE, BORDER, 12, 2)
        draw.text((bx + 25, y + 18), title, font=font_step, fill=BLACK)
        draw.text((bx + 25, y + 62), desc, font=font_desc, fill=GRAY)

        # 화살표
        if num != "5":
            draw_arrow(draw, 70 + circle_w // 2, y + box_h + 8,
                       70 + circle_w // 2, y + box_h + gap - 8, GRAY, 3)
        y += box_h + gap

    # 하단 설명 박스
    draw.rounded_rectangle([(40, y + 40), (W - 40, y + 220)],
                           radius=14, fill=BG_GREEN, outline=GREEN, width=2)
    draw.text((60, y + 60), "💡 알고리즘 채택 이유",
              font=font_step, fill=DARK_GREEN)
    draw.text((60, y + 105),
              "ByteTrack 등 AI 추적 알고리즘은 CPU 환경에서 FPS 급감 발생",
              font=font_desc, fill=BLACK)
    draw.text((60, y + 140),
              "→ 좌표 비교만으로 충분히 정확하면서 실시간성을 유지할 수 있는 자체 로직 설계",
              font=font_desc, fill=BLACK)
    draw.text((60, y + 175),
              "→ 유클리드 거리 공식 사용  d = √((x₁−x₂)² + (y₁−y₂)²)",
              font=font_desc, fill=BLACK)

    img.save(os.path.join(OUT, "report_parked_flow.png"))
    print("  ✅ report_parked_flow.png   (세로 1200x1500)")


# ══════════════════════════════════════════════════════
# 4. 이벤트 저장 흐름도 (A4 본문 너비)
# ══════════════════════════════════════════════════════
def make_event_save_flow():
    # 세로 비율 + 글씨 키운 버전
    try:
        font_title  = ImageFont.truetype("malgunbd.ttf", 30)
        font_label  = ImageFont.truetype("malgunbd.ttf", 22)
        font_step   = ImageFont.truetype("malgunbd.ttf", 22)
        font_desc   = ImageFont.truetype("malgun.ttf", 17)
        font_sub    = ImageFont.truetype("malgun.ttf", 16)
        font_emoji  = ImageFont.truetype("malgunbd.ttf", 20)
    except:
        d = ImageFont.load_default()
        font_title = font_label = font_step = font_desc = font_sub = font_emoji = d

    W, H = 1200, 1500
    img = Image.new("RGB", (W, H), PAGE_BG)
    draw = ImageDraw.Draw(img)

    # 제목
    draw.text((40, 30), "이벤트 클립 영상 저장 흐름도",
              font=font_title, fill=BLACK)
    draw.text((40, 75), "전 5초 + 후 10초 = 총 15초 클립 자동 녹화",
              font=font_sub, fill=GRAY)
    draw.line([(40, 115), (W - 40, 115)], fill=BORDER, width=2)

    # ── 상단: 타임라인 ──────────────────────────────
    tl_y         = 260
    tl_x1, tl_x2 = 120, W - 120
    draw.line([(tl_x1, tl_y), (tl_x2, tl_y)], fill=GRAY, width=4)

    event_x = (tl_x1 + tl_x2) // 2
    draw.line([(event_x, tl_y - 40), (event_x, tl_y + 40)], fill=RED, width=5)
    draw.text((event_x - 95, tl_y - 90), "⚡ 이벤트 발생",
              font=font_label, fill=RED)
    draw.text((event_x - 38, tl_y - 60), "(t = 0초)",
              font=font_sub, fill=GRAY)

    # 전 5초 (파란색 구간)
    pre_x1 = event_x - 380
    draw.rounded_rectangle([(pre_x1, tl_y - 16), (event_x, tl_y + 16)],
                            radius=8, fill=BLUE)
    draw.text((pre_x1 + 30, tl_y + 35), "전 5초 (frame_buffer)",
              font=font_label, fill=BLUE)
    draw.text((pre_x1 + 30, tl_y + 70),
              "이벤트 발생 직전 5초 분량의 프레임을",
              font=font_desc, fill=BLACK)
    draw.text((pre_x1 + 30, tl_y + 95),
              "순환 버퍼(deque)에 항상 보관",
              font=font_desc, fill=BLACK)

    # 후 10초 (빨간색 구간)
    post_x2 = event_x + 480
    draw.rounded_rectangle([(event_x, tl_y - 16), (post_x2, tl_y + 16)],
                            radius=8, fill=RED)
    draw.text((event_x + 30, tl_y + 35), "후 10초 (post_frames)",
              font=font_label, fill=RED)
    draw.text((event_x + 30, tl_y + 70),
              "이벤트 트리거 후 10초 동안의 프레임을",
              font=font_desc, fill=BLACK)
    draw.text((event_x + 30, tl_y + 95),
              "실시간으로 수집",
              font=font_desc, fill=BLACK)

    # 시간 라벨
    draw.text((pre_x1 - 50, tl_y + 25), "t = -5",
              font=font_sub, fill=GRAY)
    draw.text((post_x2 + 10, tl_y + 25), "t = +10",
              font=font_sub, fill=GRAY)

    # ── 하단: 3단계 세로 배치 ─────────────────────────
    box_w = W - 120
    box_h = 170
    gap   = 50
    box_x = 60
    y2    = 510

    stages = [
        (AMBER, "① 발생 즉시 (t = 0초)", [
            "• 캡처 이미지 저장 (.jpg)",
            "• pre_frames = buffer 복사 (직전 5초 프레임)",
            "• post_recording = True (후속 녹화 시작)",
        ]),
        (BLUE, "② 후속 녹화 (이벤트 이후 10초간)", [
            "• 매 프레임 post_frames 리스트에 누적",
            "• 동시에 실시간 모니터링은 계속 진행",
            "• 15초 쿨다운 적용으로 중복 이벤트 방지",
        ]),
        (DARK_GREEN, "③ 10초 후 클립 영상 저장", [
            "• 전 5초 + 후 10초 프레임을 합쳐 .mp4 생성",
            "• 재생 시 H.264 자동 변환 + 결과 캐싱",
            "• CSV 로그에 시간 · 소스 · 파일명 기록",
        ]),
    ]

    for idx, (color, title, lines) in enumerate(stages):
        y = y2 + idx * (box_h + gap)

        # 박스
        draw_round_box(draw, box_x, y, box_w, box_h, WHITE, color, 12, 3)
        # 좌측 컬러 바
        draw.rounded_rectangle([(box_x, y), (box_x + 10, y + box_h)],
                                radius=4, fill=color)

        # 제목
        draw.text((box_x + 30, y + 18), title, font=font_step, fill=color)
        # 본문 리스트
        for j, line in enumerate(lines):
            draw.text((box_x + 30, y + 60 + j * 32),
                      line, font=font_desc, fill=BLACK)

        # 단계 간 화살표
        if idx < len(stages) - 1:
            ax = W // 2
            draw_arrow(draw, ax, y + box_h + 5,
                       ax, y + box_h + gap - 5, GRAY, 4)

    img.save(os.path.join(OUT, "report_event_save_flow.png"))
    print("  ✅ report_event_save_flow.png  (세로 1200x1500)")


# ══════════════════════════════════════════════════════
# 실행
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("📊 결과 보고서(HWP)용 흐름도 이미지 생성\n")
    make_overall_flow()
    make_danger_logic_flow()
    make_parked_detection_flow()
    make_event_save_flow()
    print("\n✅ 완료. 총 4장 (전체 흐름도 1 + 모듈별 3)")
    print("📌 가로 너비 1200px = HWP A4 본문 영역에 그대로 들어감")
