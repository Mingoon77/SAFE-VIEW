# generate_demo.py — 프로토타입 예상 결과 이미지 생성기
# 실행: python generate_demo.py
# 결과: data/demo_normal.png, data/demo_danger.png, data/demo_ui_normal.png, data/demo_ui_danger.png

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════
# 1. 배경 프레임 생성 (골목길 느낌)
# ══════════════════════════════════════════════════════
W, H = 960, 540

def make_background():
    """도로변 골목 느낌의 배경 생성"""
    frame = np.zeros((H, W, 3), dtype=np.uint8)

    # 하늘 (어두운 회색)
    frame[0:180, :] = [60, 60, 70]

    # 건물 벽 왼쪽
    frame[0:H, 0:200] = [80, 75, 70]
    cv2.rectangle(frame, (20, 50), (180, 400), [90, 85, 80], -1)
    for y in range(80, 380, 60):
        for x in range(30, 170, 50):
            cv2.rectangle(frame, (x, y), (x+35, y+40), [50, 55, 65], -1)
            cv2.rectangle(frame, (x, y), (x+35, y+40), [40, 45, 55], 1)

    # 건물 벽 오른쪽
    frame[0:H, 720:W] = [75, 70, 65]
    cv2.rectangle(frame, (740, 30), (940, 420), [85, 80, 75], -1)
    for y in range(60, 380, 60):
        for x in range(750, 920, 55):
            cv2.rectangle(frame, (x, y), (x+38, y+42), [50, 55, 65], -1)

    # 도로 바닥
    frame[380:H, :] = [50, 50, 52]
    frame[380:400, :] = [60, 60, 62]  # 경계선

    # 도로 차선
    for x in range(100, W - 100, 80):
        cv2.line(frame, (x, 460), (x + 40, 460), [90, 90, 90], 2)

    # 인도 (밝은 회색)
    frame[400:H, 200:720] = [72, 70, 68]

    # 담장 / 주차 구분선
    cv2.rectangle(frame, (195, 380), (205, H), [100, 95, 90], -1)
    cv2.rectangle(frame, (715, 380), (725, H), [100, 95, 90], -1)

    return frame


def draw_parked_car(frame, x, y, w=220, h=110, color=(40, 50, 80)):
    """주차된 차량 그리기"""
    # 차체
    cv2.rectangle(frame, (x, y), (x+w, y+h), color, -1)
    cv2.rectangle(frame, (x+20, y-35), (x+w-20, y+5), color, -1)
    # 유리
    cv2.rectangle(frame, (x+30, y-30), (x+w-30, y+2), [80, 100, 120], -1)
    # 바퀴
    cv2.circle(frame, (x+40, y+h), 22, [25, 25, 25], -1)
    cv2.circle(frame, (x+40, y+h), 12, [50, 50, 50], -1)
    cv2.circle(frame, (x+w-40, y+h), 22, [25, 25, 25], -1)
    cv2.circle(frame, (x+w-40, y+h), 12, [50, 50, 50], -1)
    # 광택
    cv2.line(frame, (x+5, y+20), (x+w-5, y+20), [60, 70, 100], 1)
    return frame


def draw_person(frame, cx, cy, scale=1.0):
    """사람 실루엣 그리기"""
    s = scale
    # 머리
    cv2.circle(frame, (cx, int(cy - 60*s)), int(18*s), [200, 170, 140], -1)
    # 몸통
    cv2.rectangle(frame,
                  (int(cx-16*s), int(cy-42*s)),
                  (int(cx+16*s), int(cy+20*s)),
                  [60, 80, 120], -1)
    # 다리
    cv2.rectangle(frame,
                  (int(cx-14*s), int(cy+20*s)),
                  (int(cx-4*s), int(cy+65*s)),
                  [40, 50, 80], -1)
    cv2.rectangle(frame,
                  (int(cx+4*s), int(cy+20*s)),
                  (int(cx+14*s), int(cy+65*s)),
                  [40, 50, 80], -1)
    return frame


# ══════════════════════════════════════════════════════
# 2. 공통 그리기 함수
# ══════════════════════════════════════════════════════

def draw_roi(frame, pts, danger=False):
    pts_np = np.array(pts, dtype=np.int32)
    color  = (0, 0, 200) if danger else (0, 220, 220)
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pts_np], color)
    cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)
    cv2.polylines(frame, [pts_np], True, color, 2)
    for i, p in enumerate(pts):
        cv2.circle(frame, p, 5, color, -1)
    return frame


def draw_bbox(frame, x1, y1, x2, y2, label, danger=False):
    color = (0, 0, 210) if danger else (0, 200, 60)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.rectangle(frame, (x1, y1-th-8), (x1+tw+4, y1), color, -1)
    cv2.putText(frame, label, (x1+2, y1-4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return frame


def draw_red_border(frame):
    """위험 상태 빨간 테두리"""
    t = 8
    cv2.rectangle(frame, (0, 0), (W-1, H-1), (0, 0, 210), t)
    return frame


def draw_danger_text(frame):
    text  = "DANGER - PEDESTRIAN DETECTED"
    scale = 0.9
    thick = 2
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    x = 12
    y = 42
    cv2.rectangle(frame, (x-4, y-th-6), (x+tw+4, y+4), (0, 0, 0), -1)
    cv2.putText(frame, text, (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 60, 255), thick, cv2.LINE_AA)
    return frame


def draw_fps_info(frame, fps="24.3", idx=142, is_rtsp=False):
    src = "[RTSP]" if is_rtsp else "[FILE]"
    text = f"FPS:{fps}  F:{idx}  {src}"
    cv2.putText(frame, text, (10, H-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)
    return frame


# ══════════════════════════════════════════════════════
# 3. 프레임 생성 (정상 / 위험)
# ══════════════════════════════════════════════════════

ROI_PTS = [(310, 390), (540, 385), (560, 530), (290, 530)]

# 주차 차량 위치
CAR1_X, CAR1_Y = 220, 310
CAR2_X, CAR2_Y = 490, 300

# 사람 위치 (정상: ROI 밖 / 위험: ROI 안)
PERSON_NORMAL_CX, PERSON_NORMAL_CY = 620, 450   # ROI 밖
PERSON_DANGER_CX, PERSON_DANGER_CY = 420, 470   # ROI 안


def make_scene(danger: bool) -> np.ndarray:
    frame = make_background()
    frame = draw_parked_car(frame, CAR1_X, CAR1_Y, color=(35, 45, 70))
    frame = draw_parked_car(frame, CAR2_X, CAR2_Y, w=200, h=100, color=(55, 40, 40))

    if danger:
        cx, cy = PERSON_DANGER_CX, PERSON_DANGER_CY
    else:
        cx, cy = PERSON_NORMAL_CX, PERSON_NORMAL_CY

    frame = draw_person(frame, cx, cy, scale=0.95)
    frame = draw_roi(frame, ROI_PTS, danger=danger)

    # 차량 bbox
    draw_bbox(frame, CAR1_X-5,  CAR1_Y-40, CAR1_X+225, CAR1_Y+115,
              "car 0.88", danger=danger)
    draw_bbox(frame, CAR2_X-5,  CAR2_Y-38, CAR2_X+205, CAR2_Y+108,
              "car 0.82", danger=danger)

    # 사람 bbox
    px1 = cx - 22
    py1 = cy - 78
    px2 = cx + 22
    py2 = cy + 68
    draw_bbox(frame, px1, py1, px2, py2, "person 0.91", danger=danger)

    if danger:
        frame = draw_red_border(frame)
        frame = draw_danger_text(frame)

    draw_fps_info(frame, fps="24.3", idx=142, is_rtsp=False)
    return frame


# ══════════════════════════════════════════════════════
# 4. Streamlit UI 느낌의 전체 화면 합성
# ══════════════════════════════════════════════════════

def make_ui_mockup(video_frame_bgr: np.ndarray, danger: bool) -> Image.Image:
    """
    Streamlit 화면처럼 보이도록 사이드바 + 영상 + 상태창을 합성합니다.
    """
    UI_W, UI_H = 1400, 680
    img = Image.new("RGB", (UI_W, UI_H), (14, 17, 23))  # Streamlit 배경색
    draw = ImageDraw.Draw(img)

    # ── 상단 타이틀 바 ────────────────────────────────
    draw.rectangle([(0, 0), (UI_W, 52)], fill=(20, 24, 32))
    draw.text((20, 14), "🎥  실시간 모니터링  |  보행자 위험 감지 시스템",
              fill=(240, 240, 240))
    draw.text((UI_W - 220, 14), "● 실행 중", fill=(80, 200, 80))

    # ── 사이드바 ──────────────────────────────────────
    SB_W = 220
    draw.rectangle([(0, 52), (SB_W, UI_H)], fill=(20, 24, 32))
    draw.line([(SB_W, 52), (SB_W, UI_H)], fill=(40, 44, 52), width=1)

    sb_texts = [
        ("⚙️ 설정", (160, 160, 160), 68),
        ("영상 소스", (120, 120, 120), 96),
        ("● 로컬 영상 파일", (100, 180, 255), 116),
        ("  골목길_샘플.mp4", (200, 200, 200), 136),
        ("─────────────────", (50, 54, 62), 158),
        ("✅ ROI 로드됨 (4꼭짓점)", (80, 200, 80), 176),
        ("─────────────────", (50, 54, 62), 198),
        ("탐지 신뢰도: 0.40", (180, 180, 180), 216),
        ("─────────────────", (50, 54, 62), 238),
        ("  실시간 FPS   24.3", (180, 180, 180), 258),
        ("  처리 프레임  142", (180, 180, 180), 278),
        ("─────────────────", (50, 54, 62), 300),
    ]
    for text, color, y in sb_texts:
        draw.text((12, y), text, fill=color)

    # 시작/정지 버튼
    draw.rectangle([(12, 318), (104, 346)], fill=(40, 100, 200))
    draw.text((28, 326), "▶ 시작", fill=(255, 255, 255))
    draw.rectangle([(112, 318), (204, 346)], fill=(60, 64, 72))
    draw.text((128, 326), "⏹ 정지", fill=(180, 180, 180))

    # ── 영상 프레임 삽입 ─────────────────────────────
    VID_X, VID_Y = SB_W + 10, 62
    VID_W, VID_H = 940, 528

    frame_rgb = cv2.cvtColor(video_frame_bgr, cv2.COLOR_BGR2RGB)
    frame_pil = Image.fromarray(frame_rgb).resize((VID_W, VID_H), Image.LANCZOS)
    img.paste(frame_pil, (VID_X, VID_Y))

    # 영상 테두리
    border_color = (200, 40, 40) if danger else (40, 100, 200)
    draw.rectangle([(VID_X, VID_Y), (VID_X+VID_W, VID_Y+VID_H)],
                   outline=border_color, width=2)

    # 영상 아래 캡션
    src_text = "탐지: 사람 1명 | 자동차 2대 | ROI 설정됨 | 소스: 골목길_샘플 | 📁 파일"
    draw.text((VID_X, VID_Y + VID_H + 6), src_text, fill=(120, 120, 120))

    # ── 오른쪽 상태 패널 ─────────────────────────────
    ST_X = VID_X + VID_W + 12
    ST_W = UI_W - ST_X - 8

    # 상태창
    if danger:
        draw.rectangle([(ST_X, 70), (UI_W-8, 170)],
                       fill=(58, 20, 20), outline=(200, 40, 40), width=2)
        draw.text((ST_X + 24, 94),  "🔴 경고",          fill=(255, 80, 80))
        draw.text((ST_X + 16, 126), "보행자 위험 감지!", fill=(255, 160, 160))
    else:
        draw.rectangle([(ST_X, 70), (UI_W-8, 170)],
                       fill=(18, 46, 22), outline=(40, 160, 60), width=2)
        draw.text((ST_X + 24, 94),  "🟢 정상",  fill=(80, 220, 80))
        draw.text((ST_X + 24, 126), "위험 없음", fill=(150, 220, 150))

    # 경고 배너
    if danger:
        draw.rectangle([(ST_X, 182), (UI_W-8, 218)],
                       fill=(100, 20, 20), outline=(200, 40, 40), width=1)
        draw.text((ST_X + 8, 194), "🚨 위험! 보행자 감지", fill=(255, 100, 100))

    # 최근 이벤트
    draw.text((ST_X + 8, 236), "📋 최근 이벤트", fill=(200, 200, 200))
    draw.line([(ST_X, 256), (UI_W-8, 256)], fill=(50, 54, 62), width=1)

    events = [
        ("2026-03-19 14:32:11", "위험", (255, 100, 100)),
        ("2026-03-19 14:28:45", "위험", (255, 100, 100)),
        ("2026-03-19 14:21:03", "위험", (255, 100, 100)),
    ]
    for i, (ts, status, color) in enumerate(events):
        y_ev = 266 + i * 46
        draw.rectangle([(ST_X, y_ev), (UI_W-8, y_ev+38)], fill=(24, 28, 38))
        draw.text((ST_X + 8, y_ev + 6),  ts,               fill=(160, 160, 160))
        draw.text((ST_X + 8, y_ev + 22), f"● {status}",    fill=color)

    # 저장 안내
    draw.text((ST_X + 8, 420), "💾 저장 위치",            fill=(160, 160, 160))
    draw.text((ST_X + 8, 442), "saved_events/",           fill=(100, 140, 200))
    draw.text((ST_X + 8, 464), "logs/events_log.csv",     fill=(100, 140, 200))

    return img


# ══════════════════════════════════════════════════════
# 5. 실행
# ══════════════════════════════════════════════════════

print("예상 결과 이미지 생성 중...")

# 정상 상태 프레임
frame_normal = make_scene(danger=False)
cv2.imwrite(os.path.join(OUT_DIR, "demo_normal_frame.png"), frame_normal)
print("  ✅ demo_normal_frame.png 저장")

# 위험 상태 프레임
frame_danger = make_scene(danger=True)
cv2.imwrite(os.path.join(OUT_DIR, "demo_danger_frame.png"), frame_danger)
print("  ✅ demo_danger_frame.png 저장")

# 전체 UI 정상 상태
ui_normal = make_ui_mockup(frame_normal, danger=False)
ui_normal.save(os.path.join(OUT_DIR, "demo_ui_normal.png"))
print("  ✅ demo_ui_normal.png 저장")

# 전체 UI 위험 상태
ui_danger = make_ui_mockup(frame_danger, danger=True)
ui_danger.save(os.path.join(OUT_DIR, "demo_ui_danger.png"))
print("  ✅ demo_ui_danger.png 저장")

print(f"\n완료! 'data/' 폴더에서 확인하세요.")
print("  - demo_ui_normal.png  : 정상 상태 전체 UI")
print("  - demo_ui_danger.png  : 위험 상태 전체 UI")
print("  - demo_normal_frame.png : 정상 상태 영상 프레임만")
print("  - demo_danger_frame.png : 위험 상태 영상 프레임만")
