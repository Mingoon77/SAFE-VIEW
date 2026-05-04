# generate_midterm_ppt.py — 중간발표용 PPT 생성 (WBS + 추가 슬라이드)
# 실행: python generate_midterm_ppt.py

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)

# ── 색상 팔레트 ──────────────────────────────────────
GREEN      = RGBColor(76, 175, 80)
DARK_GREEN = RGBColor(46, 125, 50)
BG_GREEN   = RGBColor(232, 245, 233)
WHITE      = RGBColor(255, 255, 255)
BLACK      = RGBColor(26, 26, 26)
GRAY       = RGBColor(100, 116, 139)
LIGHT_GRAY = RGBColor(241, 245, 249)
BORDER     = RGBColor(226, 232, 240)
RED        = RGBColor(220, 38, 38)
ORANGE     = RGBColor(234, 88, 12)
BLUE       = RGBColor(59, 130, 246)
AMBER      = RGBColor(245, 158, 11)
PURPLE     = RGBColor(147, 51, 234)
CYAN       = RGBColor(6, 182, 212)
BG         = RGBColor(248, 250, 252)

LOGO = os.path.join(os.path.dirname(__file__), "logo.png")
HAS_LOGO = os.path.exists(LOGO)
DIAGRAM = os.path.join(os.path.dirname(__file__), "system_diagram.png")
HAS_DIAGRAM = os.path.exists(DIAGRAM)


def set_bg(slide, color=BG):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color

def card(slide, x, y, w, h, color=WHITE, border=BORDER):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color
    s.line.color.rgb = border; s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s

def txt(slide, x, y, w, h, text, size=14, bold=False, color=BLACK, align=PP_ALIGN.LEFT, font="맑은 고딕"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size); p.font.bold = bold
    p.font.color.rgb = color; p.font.name = font
    p.alignment = align
    return tb

def page_title(slide, num, title):
    if HAS_LOGO:
        slide.shapes.add_picture(LOGO, Inches(0.4), Inches(0.3), Inches(0.55), Inches(0.55))
    if num:
        s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(0.35), Inches(0.7), Inches(0.5))
        s.fill.solid(); s.fill.fore_color.rgb = GREEN; s.line.fill.background()
        txt(slide, Inches(1.1), Inches(0.4), Inches(0.7), Inches(0.45), num, 18, True, WHITE, PP_ALIGN.CENTER)
        txt(slide, Inches(1.9), Inches(0.4), Inches(10), Inches(0.5), title, 24, True, BLACK)
    else:
        txt(slide, Inches(1.1), Inches(0.4), Inches(10), Inches(0.5), title, 24, True, BLACK)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.4), Inches(1.0), Inches(12.5), Inches(0.02))
    line.fill.solid(); line.fill.fore_color.rgb = BORDER; line.line.fill.background()


# ══════════════════════════════════════════════════════
# 슬라이드 1: 표지
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide, DARK_GREEN)
if HAS_LOGO:
    slide.shapes.add_picture(LOGO, Inches(5.8), Inches(1.3), Inches(1.8), Inches(1.8))
txt(slide, Inches(1), Inches(3.3), Inches(11.3), Inches(0.8), "SAFEVIEW", 56, True, WHITE, PP_ALIGN.CENTER)
txt(slide, Inches(1), Inches(4.3), Inches(11.3), Inches(0.6), "AI 기반 사각지대 위험 감지 시스템", 26, False, RGBColor(200, 230, 200), PP_ALIGN.CENTER)
b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.7), Inches(5.2), Inches(2), Inches(0.55))
b.fill.solid(); b.fill.fore_color.rgb = WHITE; b.line.fill.background()
txt(slide, Inches(5.7), Inches(5.25), Inches(2), Inches(0.5), "중 간 발 표", 18, True, DARK_GREEN, PP_ALIGN.CENTER)
txt(slide, Inches(1), Inches(6.3), Inches(11.3), Inches(0.4), "Capstone Design | 2026학년도 1학기", 14, False, RGBColor(180, 210, 180), PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════
# 슬라이드 2: 목차
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "", "목차")

items = [
    ("01", "시스템 개요",         "아키텍처 · 판단 로직 · 기술 스택"),
    ("02", "진행 현황",            "WBS 기준 수행 결과"),
    ("03", "주요 변경 사항",       "구현 과정에서 보완·추가된 기능"),
    ("04", "수행 이슈 및 대응",    "RTSP 영상 속도 · 개발 우선순위 조정"),
    ("05", "추가 개발 예정",       "다중 CCTV 프리셋 토글"),
    ("06", "성능 지표 · 리스크",   "현재 지표와 리스크 관리"),
    ("07", "향후 로드맵",          "최종 발표까지의 일정"),
]
for i, (num, title, desc) in enumerate(items):
    y = Inches(1.3) + Inches(i * 0.8)
    card(slide, Inches(1.5), y, Inches(10.3), Inches(0.7))
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.8), y + Inches(0.08), Inches(0.52), Inches(0.52))
    s.fill.solid(); s.fill.fore_color.rgb = GREEN; s.line.fill.background()
    txt(slide, Inches(1.8), y + Inches(0.1), Inches(0.52), Inches(0.5), num, 14, True, WHITE, PP_ALIGN.CENTER)
    txt(slide, Inches(2.6), y + Inches(0.05), Inches(8), Inches(0.35), title, 17, True, BLACK)
    txt(slide, Inches(2.6), y + Inches(0.4), Inches(8.5), Inches(0.3), desc, 12, False, GRAY)


# ══════════════════════════════════════════════════════
# 슬라이드 3: 시스템 아키텍처 구조도
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "01", "시스템 아키텍처")

if HAS_DIAGRAM:
    # 중앙 상단에 구조도 배치
    slide.shapes.add_picture(DIAGRAM, Inches(1.0), Inches(1.3), Inches(11.3), Inches(5.3))
else:
    card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(5.5), color=LIGHT_GRAY)
    txt(slide, Inches(0.5), Inches(3.8), Inches(12.3), Inches(0.6),
        "📷 system_diagram.png 파일 필요", 18, True, GRAY, PP_ALIGN.CENTER)

# 하단 요약 설명
card(slide, Inches(0.5), Inches(6.7), Inches(12.3), Inches(0.6), color=BG_GREEN, border=GREEN)
txt(slide, Inches(0.7), Inches(6.8), Inches(12), Inches(0.4),
    "Input(CCTV·파일) → Transmission(RTSP·파일) → Processing(OpenCV·YOLOv8·ROI) → Output(UI·경고) + Storage(이미지·클립·로그)",
    12, True, DARK_GREEN)


# ══════════════════════════════════════════════════════
# 슬라이드 4: 위험 판단 로직 플로우
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "01", "위험 판단 로직")

# 좌: 판단 규칙 표
card(slide, Inches(0.5), Inches(1.3), Inches(6.2), Inches(5.8))
txt(slide, Inches(0.8), Inches(1.45), Inches(6), Inches(0.4), "📋 규칙 기반 상태 판단", 16, True, DARK_GREEN)

# 헤더
card(slide, Inches(0.8), Inches(2.0), Inches(5.7), Inches(0.45), color=DARK_GREEN, border=DARK_GREEN)
txt(slide, Inches(0.95), Inches(2.05), Inches(2.8), Inches(0.35), "감지 조건",  12, True, WHITE)
txt(slide, Inches(3.8),  Inches(2.05), Inches(1.2), Inches(0.35), "위치",       12, True, WHITE)
txt(slide, Inches(5.1),  Inches(2.05), Inches(1.4), Inches(0.35), "판단",       12, True, WHITE)

rules = [
    ("사람 + 차량 동시 감지", "ROI 내부", "🔴 위험", RED),
    ("사람 + 차량 동시 감지", "ROI 외부", "🟢 정상", GREEN),
    ("사람만 감지",           "내/외 무관","🟢 정상", GREEN),
    ("차량만 감지",           "내/외 무관","🟢 정상", GREEN),
    ("아무것도 없음",         "—",        "🟢 정상", GREEN),
]
for i, (cond, area, res, color) in enumerate(rules):
    y = Inches(2.5) + Inches(i * 0.55)
    bg = LIGHT_GRAY if i % 2 == 0 else WHITE
    card(slide, Inches(0.8), y, Inches(5.7), Inches(0.5), color=bg, border=BORDER)
    txt(slide, Inches(0.95), y + Inches(0.1), Inches(2.8), Inches(0.35), cond, 11, False, BLACK)
    txt(slide, Inches(3.8),  y + Inches(0.1), Inches(1.2), Inches(0.35), area, 11, False, GRAY)
    txt(slide, Inches(5.1),  y + Inches(0.1), Inches(1.4), Inches(0.35), res,  12, True,  color)

# 우: 이벤트 트리거 플로우
card(slide, Inches(7.0), Inches(1.3), Inches(5.8), Inches(5.8))
txt(slide, Inches(7.3), Inches(1.45), Inches(5.5), Inches(0.4), "⚡ 이벤트 발생 플로우", 16, True, DARK_GREEN)

flow = [
    ("프레임 수신",      "CCTV·영상에서 프레임 획득",     CYAN),
    ("객체 탐지",        "YOLOv8로 person·car 인식",      BLUE),
    ("ROI 판정",         "사람 발 위치가 ROI 내부인지",   PURPLE),
    ("상태 결정",        "정상 / 위험 규칙 적용",         GREEN),
    ("이벤트 트리거",    "정상 → 위험 전환 순간에만",     AMBER),
    ("저장 + 경고",       "이미지·클립·로그 + 시청각 경고",  RED),
]
for i, (title, desc, color) in enumerate(flow):
    y = Inches(2.0) + Inches(i * 0.82)
    # 단계 번호
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.3), y + Inches(0.1), Inches(0.4), Inches(0.4))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    txt(slide, Inches(7.3), y + Inches(0.1), Inches(0.4), Inches(0.4), str(i+1), 14, True, WHITE, PP_ALIGN.CENTER)
    txt(slide, Inches(7.85), y + Inches(0.05), Inches(4.8), Inches(0.35), title, 13, True, BLACK)
    txt(slide, Inches(7.85), y + Inches(0.4),  Inches(4.8), Inches(0.35), desc,  11, False, GRAY)
    # 화살표 (마지막 제외)
    if i < len(flow) - 1:
        arr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.48), y + Inches(0.55), Inches(0.08), Inches(0.25))
        arr.fill.solid(); arr.fill.fore_color.rgb = BORDER; arr.line.fill.background()


# ══════════════════════════════════════════════════════
# 슬라이드 5: 기술 스택 아이콘 카드
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "01", "기술 스택")

techs = [
    ("🐍", "Python 3.13",      "메인 개발 언어",                DARK_GREEN),
    ("🤖", "YOLOv8 (Nano)",    "객체 탐지 모델\nAGPL-3.0",      BLUE),
    ("📹", "OpenCV",           "영상 프레임 처리\nRTSP 디코딩", CYAN),
    ("🖥️", "Streamlit",        "웹 기반 UI\n빠른 프로토타이핑", PURPLE),
    ("📡", "RTSP + H.264",     "실시간 CCTV\n스트리밍 프로토콜",ORANGE),
    ("🎬", "imageio-ffmpeg",   "H.264 클립 변환\n브라우저 재생",AMBER),
    ("☁️", "Cloudflare Tunnel","외부 공유 배포\n무료 HTTPS",    RED),
    ("🧬", "GitHub",           "버전 관리\n협업",               GRAY),
]

# 2행 4열 배치
for i, (icon, name, desc, color) in enumerate(techs):
    col = i % 4
    row = i // 4
    x = Inches(0.5) + Inches(col * 3.2)
    y = Inches(1.4) + Inches(row * 2.8)
    card(slide, x, y, Inches(3.0), Inches(2.6))
    # 아이콘 원형 배경
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(1.1), y + Inches(0.25), Inches(0.8), Inches(0.8))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    txt(slide, x + Inches(1.1), y + Inches(0.32), Inches(0.8), Inches(0.7), icon, 24, False, WHITE, PP_ALIGN.CENTER, font="Segoe UI Emoji")
    # 이름
    txt(slide, x + Inches(0.1), y + Inches(1.15), Inches(2.8), Inches(0.4), name, 15, True, BLACK, PP_ALIGN.CENTER)
    # 설명
    txt(slide, x + Inches(0.1), y + Inches(1.6),  Inches(2.8), Inches(0.9), desc, 11, False, GRAY, PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════
# 슬라이드 6: 진행 현황 (WBS 단계별)
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "02", "진행 현황 — WBS 단계별 수행 결과")

phases = [
    ("1", "프로젝트 기획",               "3/3 ~ 3/15",  "완료",   GREEN),
    ("2", "기초 조사 및 계획 수립",       "3/12 ~ 3/19", "완료",   GREEN),
    ("3", "시스템 설계 · 핵심 모듈 개발", "3/12 ~ 4/12", "완료",   GREEN),
    ("4", "중간 점검 및 UI 보완",         "3/30 ~ 4/22", "진행 중", BLUE),
    ("5", "통합 테스트 및 최종 마무리",   "4/10 ~ 6/11", "진행 중", AMBER),
]
for i, (num, name, period, status, color) in enumerate(phases):
    y = Inches(1.3) + Inches(i * 1.15)
    card(slide, Inches(0.5), y, Inches(12.3), Inches(1.0))
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.75), y + Inches(0.22), Inches(0.55), Inches(0.55))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    txt(slide, Inches(0.75), y + Inches(0.24), Inches(0.55), Inches(0.5), num, 18, True, WHITE, PP_ALIGN.CENTER)
    txt(slide, Inches(1.6), y + Inches(0.15), Inches(7), Inches(0.4), name, 17, True, BLACK)
    txt(slide, Inches(1.6), y + Inches(0.55), Inches(7), Inches(0.35), period, 12, False, GRAY)
    b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.8), y + Inches(0.3), Inches(1.7), Inches(0.4))
    b.fill.solid(); b.fill.fore_color.rgb = color; b.line.fill.background()
    txt(slide, Inches(10.8), y + Inches(0.34), Inches(1.7), Inches(0.35), status, 13, True, WHITE, PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════
# 슬라이드 7: 핵심 모듈 구현 결과
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "02", "핵심 모듈 및 UI 구현 결과 (WBS 3~4단계)")

card(slide, Inches(0.5), Inches(1.3), Inches(6.2), Inches(5.8))
txt(slide, Inches(0.8), Inches(1.45), Inches(6), Inches(0.4), "🔧 3단계  시스템 설계 · 핵심 모듈", 16, True, DARK_GREEN)
m3 = [
    "시스템 구조 설계 및 화면 구성안 (3.1)",
    "영상 입력 처리 (RTSP / 로컬 파일)",
    "YOLOv8 기반 객체 인식 구현 (3.2)",
    "ROI 수동 지정 — 마우스 드로잉 (3.3)",
    "규칙 기반 위험 판단 로직 (3.3)",
    "시각 경고 · 병렬 프로토타이핑 (3.4)",
]
for i, item in enumerate(m3):
    y = Inches(2.0) + Inches(i * 0.6)
    txt(slide, Inches(0.9), y, Inches(6), Inches(0.4), f"  ✓  {item}", 13, False, BLACK)

card(slide, Inches(7.0), Inches(1.3), Inches(5.8), Inches(5.8))
txt(slide, Inches(7.3), Inches(1.45), Inches(5.5), Inches(0.4), "🎨 4단계  중간 점검 · UI 보완", 16, True, DARK_GREEN)
m4 = [
    "프로토타입 1차 구현 · 실행 검증 (4.1)",
    "노션 기록 및 발표 자료 제작 (4.2)",
    "이벤트 이미지 / 클립 저장 기능 (4.3)",
    "전 5초 + 후 10초 자동 녹화",
    "캘린더 기반 이벤트 다시보기",
    "영상 H.264 자동 변환 재생",
    "3컬럼 대시보드 UI 개편 (4.4)",
    "SAFEVIEW 브랜딩 · 로고 적용",
    "경고음 추가 (Web Audio API)",
    "Cloudflare Tunnel 외부 공유",
]
for i, item in enumerate(m4):
    y = Inches(2.0) + Inches(i * 0.5)
    txt(slide, Inches(7.4), y, Inches(5.5), Inches(0.4), f"  ✓  {item}", 12, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 8: 주요 변경 사항
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "03", "과제계획서 대비 주요 변경 사항")

card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(0.5), color=DARK_GREEN, border=DARK_GREEN)
txt(slide, Inches(0.7), Inches(1.4), Inches(3.5), Inches(0.35), "항목",      14, True, WHITE)
txt(slide, Inches(4.2), Inches(1.4), Inches(4),   Inches(0.35), "원 계획",   14, True, WHITE)
txt(slide, Inches(8.5), Inches(1.4), Inches(4.2), Inches(0.35), "구현 결과", 14, True, WHITE)

rows = [
    ("ROI 설정 방식",    "좌표 텍스트 직접 입력",        "마우스 클릭으로 다각형 드로잉"),
    ("영상 클립 재생",   "OpenCV mp4v 코덱 저장",        "H.264 자동 변환 → 브라우저 재생"),
    ("녹화 구간",        "이벤트 발생 시점 이전만 저장", "전 5초 + 후 10초 (총 15초)"),
    ("이벤트 조회",      "CSV 로그만 제공",              "캘린더 UI + 썸네일 + 영상 재생"),
    ("외부 공유",        "로컬 실행만",                  "Cloudflare Tunnel 링크 공유"),
    ("경고 방식",        "시각 경고만",                  "시각 + 청각(경고음) 동시 제공"),
    ("UI 디자인",        "기본 Streamlit",               "SAFEVIEW 브랜딩 · 3컬럼 레이아웃"),
]
for i, (cat, orig, new) in enumerate(rows):
    y = Inches(1.9) + Inches(i * 0.68)
    bg = LIGHT_GRAY if i % 2 == 0 else WHITE
    card(slide, Inches(0.5), y, Inches(12.3), Inches(0.6), color=bg, border=BORDER)
    txt(slide, Inches(0.7), y + Inches(0.15), Inches(3.5), Inches(0.35), cat,  13, True,  BLACK)
    txt(slide, Inches(4.2), y + Inches(0.15), Inches(4.2), Inches(0.35), orig, 12, False, GRAY)
    txt(slide, Inches(8.5), y + Inches(0.15), Inches(4.2), Inches(0.35), new,  12, True,  DARK_GREEN)


# ══════════════════════════════════════════════════════
# 슬라이드 9: 이슈 ① 화면 깜빡임 해결 (개발 초기)
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "04", "이슈 ① 실시간 영상 화면 깜빡임 현상")

# 증상 설명
card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(1.3), color=RGBColor(254, 242, 242), border=RED)
txt(slide, Inches(0.8), Inches(1.42), Inches(12), Inches(0.4), "⚠️ 증상", 15, True, RED)
txt(slide, Inches(0.8), Inches(1.82), Inches(12), Inches(0.8),
    "자택 CCTV(RTSP) 연동은 정상 작동했으나, 실시간 영상이 매 프레임마다\n"
    "하얗게 깜빡이며 심한 플리커 현상 발생 → 시인성 저하 및 발표 시연 불가",
    12, False, BLACK)

# Before / After 코드 이미지 (좌/우)
card(slide, Inches(0.5), Inches(2.75), Inches(6.2), Inches(3.4), color=RGBColor(254, 242, 242), border=RED)
code_before = os.path.join(os.path.dirname(__file__), "code_before.png")
if os.path.exists(code_before):
    slide.shapes.add_picture(code_before, Inches(0.6), Inches(2.85), Inches(6.0), Inches(3.2))

card(slide, Inches(6.9), Inches(2.75), Inches(6.0), Inches(3.4), color=BG_GREEN, border=GREEN)
code_after = os.path.join(os.path.dirname(__file__), "code_after.png")
if os.path.exists(code_after):
    slide.shapes.add_picture(code_after, Inches(7.0), Inches(2.85), Inches(5.8), Inches(3.2))

# 원인 + 해결 요약
card(slide, Inches(0.5), Inches(6.25), Inches(12.3), Inches(0.85), color=BG_GREEN, border=GREEN)
txt(slide, Inches(0.8), Inches(6.3), Inches(5.5), Inches(0.35), "🔍 원인", 13, True, RED)
txt(slide, Inches(0.8), Inches(6.62), Inches(5.5), Inches(0.4),
    "st.rerun()이 매 프레임마다 페이지 전체를 리렌더", 11, False, BLACK)
txt(slide, Inches(6.8), Inches(6.3), Inches(6), Inches(0.35), "✅ 해결", 13, True, DARK_GREEN)
txt(slide, Inches(6.8), Inches(6.62), Inches(6), Inches(0.4),
    "while 루프 + st.empty() placeholder에 이미지만 직접 갱신", 11, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 10: 이슈 ② RTSP 영상 속도
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "04", "이슈 ② RTSP 실시간 영상 처리 속도")

card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(1.5), color=RGBColor(255, 251, 235), border=AMBER)
txt(slide, Inches(0.8), Inches(1.45), Inches(12), Inches(0.4), "📋 현황", 16, True, ORANGE)
txt(slide, Inches(0.8), Inches(1.85), Inches(12), Inches(0.9),
    "고해상도 RTSP 스트림(1080p) 처리 시 재생 지연 · 끊김 현상 발생 가능\n"
    "→ 주요 요인: 네트워크 대역폭 · YOLO 추론 부하 · 웹 프레임 전송 속도",
    13, False, BLACK)

card(slide, Inches(0.5), Inches(3.0), Inches(12.3), Inches(4.1), color=BG_GREEN, border=GREEN)
txt(slide, Inches(0.8), Inches(3.15), Inches(12), Inches(0.4), "✅ 적용한 최적화 및 향후 계획", 16, True, DARK_GREEN)

fixes = [
    ("적용", "RTSP 백그라운드 스레드",     "네트워크 대기 시간을 메인 루프에서 분리"),
    ("적용", "FRAME_SKIP 기반 추론 주기",  "2프레임당 1회 YOLO 실행 → 부하 50% 감소"),
    ("적용", "탐지 결과 캐싱",              "스킵 프레임에서 직전 바운딩 박스 유지"),
    ("적용", "원격 접속 자동 감지",         "Host 헤더로 판별 → 외부 접속 시 해상도 축소"),
    ("계획", "모델 경량화 벤치마크",        "YOLOv8n vs YOLOv8s 속도·정확도 비교"),
    ("계획", "GPU 추론 환경 검토",          "CUDA 활용 시 추론 속도 3~5배 향상 기대"),
]
for i, (tag, title, desc) in enumerate(fixes):
    y = Inches(3.65) + Inches(i * 0.55)
    color = GREEN if tag == "적용" else AMBER
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(0.85), Inches(0.4))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    txt(slide, Inches(0.8), y + Inches(0.05), Inches(0.85), Inches(0.35), tag, 12, True, WHITE, PP_ALIGN.CENTER)
    txt(slide, Inches(1.85), y + Inches(0.02), Inches(3.3), Inches(0.4), title, 13, True, BLACK)
    txt(slide, Inches(5.2),  y + Inches(0.05), Inches(7.5), Inches(0.4), desc,  12, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 10: 이슈 ② 개발 우선순위 조정
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "04", "이슈 ③ 개발 우선순위 조정 — 자체 데이터셋 학습")

card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(1.6), color=RGBColor(255, 251, 235), border=AMBER)
txt(slide, Inches(0.8), Inches(1.45), Inches(12), Inches(0.4), "📋 배경", 16, True, ORANGE)
txt(slide, Inches(0.8), Inches(1.85), Inches(12), Inches(1.0),
    "사전 계획: 사각지대 환경 특화 자체 데이터셋 구축 및 Fine-tuning 학습\n"
    "실제 검토: 학습 데이터 확보·라벨링·검증 리소스 대비 성능 개선 폭 제한적으로 판단",
    13, False, BLACK)

card(slide, Inches(0.5), Inches(3.1), Inches(12.3), Inches(1.7), color=RGBColor(239, 246, 255), border=BLUE)
txt(slide, Inches(0.8), Inches(3.25), Inches(12), Inches(0.4), "💡 의사결정", 16, True, BLUE)
txt(slide, Inches(0.8), Inches(3.65), Inches(12), Inches(1.1),
    "교수님 피드백 반영 → 자체 데이터셋 학습 생략, 확보한 리소스를 다음 항목에 재투자\n"
    "COCO 사전학습 YOLOv8n 모델 유지 (person/car 클래스 성능 검증 완료)",
    13, False, BLACK)

card(slide, Inches(0.5), Inches(5.0), Inches(12.3), Inches(2.1), color=BG_GREEN, border=GREEN)
txt(slide, Inches(0.8), Inches(5.15), Inches(12), Inches(0.4), "✅ 리소스 재투자 방향", 16, True, DARK_GREEN)

reinvest = [
    ("시스템 안정성 강화", "장시간 운용 테스트 · 메모리 누수 제거 · 오류 처리"),
    ("오탐·미탐 분석",      "실환경 데이터로 규칙 기반 판단 로직 튜닝"),
    ("UX · 운영 편의성",    "다중 CCTV 프리셋 토글 · 관리자 편의 기능"),
]
for i, (title, desc) in enumerate(reinvest):
    y = Inches(5.65) + Inches(i * 0.45)
    txt(slide, Inches(0.9), y, Inches(3.2), Inches(0.35), f"● {title}", 13, True, DARK_GREEN)
    txt(slide, Inches(4.3), y, Inches(8.5), Inches(0.35), desc, 12, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 11: 추가 개발 예정 - CCTV 프리셋
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "05", "추가 개발 예정 — 다중 CCTV 프리셋 토글")

card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(1.4), color=RGBColor(250, 245, 255), border=PURPLE)
txt(slide, Inches(0.8), Inches(1.45), Inches(12), Inches(0.4), "🎯 도입 배경", 16, True, PURPLE)
txt(slide, Inches(0.8), Inches(1.85), Inches(12), Inches(0.9),
    "현재는 모니터링할 카메라를 바꿀 때마다 RTSP 주소를 직접 입력해야 함 → 운영 비효율\n"
    "실제 관제 환경(주차장·골목·입구 등 다중 지점)을 고려한 UX 개선 필요",
    13, False, BLACK)

card(slide, Inches(0.5), Inches(2.9), Inches(6.0), Inches(4.2))
txt(slide, Inches(0.8), Inches(3.05), Inches(5.5), Inches(0.4), "📐 구현 방식", 15, True, DARK_GREEN)

impl = [
    ("프리셋 저장",   "JSON 파일에 카메라별 RTSP 주소·이름 사전 등록"),
    ("토글 버튼 UI",  "사이드바에 카메라 선택 버튼 그룹 배치"),
    ("원클릭 전환",   "버튼 클릭 시 주소 자동 입력 + 즉시 연결"),
    ("이름·설명",     "'주차장', '골목', '입구' 등 식별자 표시"),
    ("보안 강화",     "자격증명은 secrets.toml에서 관리"),
]
for i, (title, desc) in enumerate(impl):
    y = Inches(3.5) + Inches(i * 0.65)
    txt(slide, Inches(0.9), y,              Inches(5), Inches(0.35), f"● {title}", 13, True, BLACK)
    txt(slide, Inches(1.1), y + Inches(0.3), Inches(5), Inches(0.35), desc, 11, False, GRAY)

card(slide, Inches(6.8), Inches(2.9), Inches(6.0), Inches(4.2), color=BG_GREEN, border=GREEN)
txt(slide, Inches(7.1), Inches(3.05), Inches(5.5), Inches(0.4), "✨ 기대 효과", 15, True, DARK_GREEN)

effects = [
    ("운영 편의성 향상",   "입력 오류 방지 · 전환 시간 최소화"),
    ("다중 지점 대응",     "여러 CCTV를 빠르게 순회 모니터링 가능"),
    ("시연 신뢰성",        "발표·시연 시 즉각적인 소스 전환"),
    ("확장성 기반 마련",   "향후 다중 화면 동시 모니터링 토대"),
]
for i, (title, desc) in enumerate(effects):
    y = Inches(3.55) + Inches(i * 0.8)
    txt(slide, Inches(7.2), y,              Inches(5), Inches(0.35), f"✓ {title}", 13, True, DARK_GREEN)
    txt(slide, Inches(7.4), y + Inches(0.3), Inches(5), Inches(0.35), desc, 11, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 12: 프로토타입 시연
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "05", "프로토타입 시연")

card(slide, Inches(0.5), Inches(1.3), Inches(8.3), Inches(5.8), color=RGBColor(245, 245, 245), border=BORDER)
txt(slide, Inches(0.5), Inches(3.8), Inches(8.3), Inches(0.6),
    "📷 실행 화면 스크린샷 삽입 위치", 18, True, GRAY, PP_ALIGN.CENTER)
txt(slide, Inches(0.5), Inches(4.4), Inches(8.3), Inches(0.4),
    "(모니터링 페이지 — 실시간 탐지 결과)", 12, False, GRAY, PP_ALIGN.CENTER)

card(slide, Inches(9.0), Inches(1.3), Inches(3.8), Inches(5.8))
txt(slide, Inches(9.2), Inches(1.5), Inches(3.5), Inches(0.4), "🎥 주요 화면", 16, True, DARK_GREEN)

screens = [
    ("실시간 모니터링",  "CCTV + 탐지 박스 + ROI"),
    ("위험 감지 경고",    "빨간 테두리 + 경고음"),
    ("ROI 설정",          "마우스로 다각형 그리기"),
    ("이벤트 다시보기",   "캘린더 + 영상 재생"),
]
for i, (name, desc) in enumerate(screens):
    y = Inches(2.1) + Inches(i * 1.15)
    txt(slide, Inches(9.2), y, Inches(3.5), Inches(0.35), f"● {name}", 13, True, BLACK)
    txt(slide, Inches(9.4), y + Inches(0.35), Inches(3.4), Inches(0.65), desc, 11, False, GRAY)


# ══════════════════════════════════════════════════════
# 슬라이드 13: 현재 성능 지표
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "06", "현재 성능 지표")

# 상단 주요 지표 카드 (4개)
metrics = [
    ("⚡", "실시간 FPS",      "15 ~ 25",   "fps",   "로컬 접속 기준", BLUE),
    ("🎯", "탐지 클래스",     "2",         "종류",  "person · car",   GREEN),
    ("⏱️", "이벤트 녹화",     "15",        "초",    "전 5초 + 후 10초", ORANGE),
    ("💾", "클립 파일 크기",  "2.3 ~ 2.5", "MB",    "15초 기준",      PURPLE),
]
for i, (icon, name, value, unit, desc, color) in enumerate(metrics):
    x = Inches(0.5) + Inches(i * 3.2)
    card(slide, x, Inches(1.3), Inches(3.0), Inches(1.8))
    # 좌측 컬러 바
    bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.3), Inches(0.12), Inches(1.8))
    bar.fill.solid(); bar.fill.fore_color.rgb = color; bar.line.fill.background()
    txt(slide, x + Inches(0.3), Inches(1.45), Inches(2.6), Inches(0.35), f"{icon}  {name}", 12, True, GRAY)
    txt(slide, x + Inches(0.3), Inches(1.85), Inches(2.0), Inches(0.7), value, 28, True, BLACK)
    txt(slide, x + Inches(2.1), Inches(2.15), Inches(0.8), Inches(0.4), unit,  12, False, GRAY)
    txt(slide, x + Inches(0.3), Inches(2.6), Inches(2.6), Inches(0.35), desc, 10, False, GRAY)

# 하단 세부 항목
card(slide, Inches(0.5), Inches(3.3), Inches(6.2), Inches(3.8))
txt(slide, Inches(0.8), Inches(3.45), Inches(6), Inches(0.4), "📊 처리 성능", 16, True, DARK_GREEN)

perf = [
    ("프레임 처리",       "OpenCV + YOLOv8n"),
    ("추론 최적화",        "FRAME_SKIP=2 (2프레임당 1회)"),
    ("RTSP 처리 방식",     "백그라운드 스레드 + 버퍼 최소화"),
    ("영상 클립 코덱",     "H.264 (브라우저 호환)"),
    ("원격 접속 대응",     "자동 감지 → 해상도 640px 축소"),
]
for i, (k, v) in enumerate(perf):
    y = Inches(4.0) + Inches(i * 0.55)
    txt(slide, Inches(0.9), y, Inches(2.5), Inches(0.4), f"● {k}", 12, True, BLACK)
    txt(slide, Inches(3.4), y, Inches(3.2), Inches(0.4), v,       11, False, GRAY)

card(slide, Inches(7.0), Inches(3.3), Inches(5.8), Inches(3.8))
txt(slide, Inches(7.3), Inches(3.45), Inches(5.5), Inches(0.4), "🎯 운용 지표 (누적)", 16, True, DARK_GREEN)

usage = [
    ("등록된 ROI",        "3 개 (영상 소스별)"),
    ("누적 이벤트 감지",   "20 건 이상"),
    ("이벤트 저장 형식",   "JPG + MP4 + CSV 로그"),
    ("외부 공유 횟수",     "Cloudflare 터널 안정화 완료"),
    ("연속 운용 테스트",   "30 분 무장애 동작 확인"),
]
for i, (k, v) in enumerate(usage):
    y = Inches(4.0) + Inches(i * 0.55)
    txt(slide, Inches(7.4), y, Inches(2.5), Inches(0.4), f"● {k}", 12, True, BLACK)
    txt(slide, Inches(9.9), y, Inches(2.8), Inches(0.4), v,       11, False, GRAY)


# ══════════════════════════════════════════════════════
# 슬라이드 14: 리스크 관리표
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "06", "리스크 관리")

# 헤더
card(slide, Inches(0.5), Inches(1.3), Inches(12.3), Inches(0.5), color=DARK_GREEN, border=DARK_GREEN)
txt(slide, Inches(0.7),  Inches(1.4), Inches(3.0), Inches(0.35), "리스크",    13, True, WHITE)
txt(slide, Inches(3.8),  Inches(1.4), Inches(1.2), Inches(0.35), "영향도",    13, True, WHITE)
txt(slide, Inches(5.0),  Inches(1.4), Inches(1.2), Inches(0.35), "발생 가능성", 13, True, WHITE)
txt(slide, Inches(6.3),  Inches(1.4), Inches(6.4), Inches(0.35), "대응 방안",  13, True, WHITE)

risks = [
    ("RTSP 네트워크 장애",       "높음", "중간", "재연결 로직 + 최근 프레임 캐시 유지",     RED),
    ("YOLOv8 탐지 정확도 부족",  "중간", "중간", "오탐·미탐 분석 후 신뢰도 임계값 튜닝",   AMBER),
    ("장시간 운용 메모리 누수",  "높음", "낮음", "post_frames 명시적 해제 + 장기 테스트",  RED),
    ("외부 공유 대역폭 한계",    "낮음", "중간", "원격 접속 자동 감지 해상도 축소 적용",   AMBER),
    ("일시적 CCTV 화면 깜빡임",  "낮음", "낮음", "직전 프레임 캐싱으로 빈 화면 방지",      GREEN),
    ("발표일 시스템 장애",       "높음", "낮음", "로컬 + 녹화 영상 백업 + 시연 리허설",    RED),
]
for i, (risk, impact, prob, action, color) in enumerate(risks):
    y = Inches(1.9) + Inches(i * 0.72)
    bg = LIGHT_GRAY if i % 2 == 0 else WHITE
    card(slide, Inches(0.5), y, Inches(12.3), Inches(0.65), color=bg, border=BORDER)
    # 리스크 이름 앞 색상 표시
    dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.65), y + Inches(0.22), Inches(0.2), Inches(0.2))
    dot.fill.solid(); dot.fill.fore_color.rgb = color; dot.line.fill.background()
    txt(slide, Inches(0.95), y + Inches(0.17), Inches(2.8), Inches(0.35), risk,   12, True,  BLACK)
    txt(slide, Inches(3.8),  y + Inches(0.17), Inches(1.2), Inches(0.35), impact, 12, True,  color)
    txt(slide, Inches(5.0),  y + Inches(0.17), Inches(1.2), Inches(0.35), prob,   12, False, GRAY)
    txt(slide, Inches(6.3),  y + Inches(0.17), Inches(6.4), Inches(0.35), action, 11, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 15: 향후 로드맵
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide)
page_title(slide, "07", "향후 로드맵 — 최종 발표까지")

timeline = [
    ("4/24~5/22", "통합 테스트",           "오탐·미탐 분석\n성능 기준선 측정",       BLUE),
    ("5월 초",    "RTSP 프리셋 구현",      "다중 CCTV\n토글 UI 개발",                PURPLE),
    ("5월 중순",  "시스템 안정화",         "장시간 운용\n메모리 최적화",             DARK_GREEN),
    ("5/18~5/31", "시연 영상 제작",        "프로토타입 데모\n영상 녹화",             ORANGE),
    ("5/25~6/11", "최종 자료 완성",        "최종 보고서 +\n발표 자료",               RED),
]

for i in range(len(timeline) - 1):
    x1 = Inches(0.8 + i * 2.5 + 2.3)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x1, Inches(2.3), Inches(0.2), Inches(0.06))
    line.fill.solid(); line.fill.fore_color.rgb = BORDER; line.line.fill.background()

for i, (date, title, desc, color) in enumerate(timeline):
    x = Inches(0.8 + i * 2.5)
    b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.7), Inches(2.3), Inches(0.6))
    b.fill.solid(); b.fill.fore_color.rgb = color; b.line.fill.background()
    txt(slide, x, Inches(1.78), Inches(2.3), Inches(0.45), date, 13, True, WHITE, PP_ALIGN.CENTER)
    card(slide, x, Inches(2.45), Inches(2.3), Inches(2.1))
    txt(slide, x + Inches(0.1), Inches(2.6),  Inches(2.1), Inches(0.4), title, 13, True, BLACK, PP_ALIGN.CENTER)
    txt(slide, x + Inches(0.1), Inches(3.05), Inches(2.1), Inches(1.4), desc,  11, False, GRAY, PP_ALIGN.CENTER)

card(slide, Inches(0.5), Inches(4.9), Inches(12.3), Inches(2.2), color=BG_GREEN, border=GREEN)
txt(slide, Inches(0.8), Inches(5.05), Inches(12), Inches(0.4), "🎯 최종 발표 목표", 16, True, DARK_GREEN)

goals = [
    "✓ 실환경 기반 정량 성능 지표 확보 (오탐·미탐·FPS)",
    "✓ 다중 CCTV 프리셋 토글 기능 완성 및 시연",
    "✓ 실제 골목·주차장 시연 영상 및 데모 시나리오 완성",
    "✓ 시스템 안정성 검증 (장시간 운용 테스트 포함)",
]
for i, g in enumerate(goals):
    y = Inches(5.5) + Inches(i * 0.38)
    txt(slide, Inches(0.9), y, Inches(12), Inches(0.35), g, 13, False, BLACK)


# ══════════════════════════════════════════════════════
# 슬라이드 16: 마무리
# ══════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
set_bg(slide, DARK_GREEN)
if HAS_LOGO:
    slide.shapes.add_picture(LOGO, Inches(5.8), Inches(1.8), Inches(1.8), Inches(1.8))
txt(slide, Inches(1), Inches(3.9), Inches(11.3), Inches(0.8), "감사합니다", 42, True, WHITE, PP_ALIGN.CENTER)
txt(slide, Inches(1), Inches(4.9), Inches(11.3), Inches(0.5), "SAFEVIEW — AI 기반 사각지대 위험 감지 시스템", 20, False, RGBColor(200, 230, 200), PP_ALIGN.CENTER)
txt(slide, Inches(1), Inches(5.7), Inches(11.3), Inches(0.5), "Q & A", 26, True, WHITE, PP_ALIGN.CENTER)
txt(slide, Inches(1), Inches(6.5), Inches(11.3), Inches(0.4), "GitHub: github.com/Mingoon77/SAFE-VIEW", 12, False, RGBColor(180, 220, 180), PP_ALIGN.CENTER)


output = os.path.join(os.path.dirname(__file__), "SAFEVIEW_중간발표.pptx")
prs.save(output)
print(f"PPT 저장 완료: {output}")
print(f"총 {len(prs.slides)}장 슬라이드")
