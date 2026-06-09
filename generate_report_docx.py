# generate_report_docx.py — 흐름도 4종을 한글파일에서 편집 가능한 docx로 생성
# 한글에서 열어서 .hwp로 다른 이름 저장 가능

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Mm
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

OUT = os.path.dirname(os.path.abspath(__file__))


# ──────────────────────────────────────────────────
# 헬퍼: 셀 배경색 지정
# ──────────────────────────────────────────────────
def set_cell_bg(cell, hex_color):
    """셀 배경색을 16진수 RGB로 설정 (예: 'EAF6FF')"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_cell_border(cell, color="CCCCCC", size="6"):
    tc_pr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        border = OxmlElement(f"w:{edge}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), size)
        border.set(qn("w:color"), color)
        tcBorders.append(border)
    tc_pr.append(tcBorders)


def add_para_text(cell, text, bold=False, size=11, color="000000", align="center"):
    """셀 안에 텍스트 추가 (기존 빈 단락 활용)"""
    para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
    para.alignment = {
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "left":   WD_ALIGN_PARAGRAPH.LEFT,
        "right":  WD_ALIGN_PARAGRAPH.RIGHT,
    }[align]
    if para.text:
        run = para.add_run("\n" + text)
    else:
        run = para.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "맑은 고딕"
    run.font.color.rgb = RGBColor.from_string(color)
    # 한글 폰트도 명시
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "맑은 고딕")


def add_arrow(doc, color="666666"):
    """가운데 정렬된 ↓ 화살표 한 줄"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("↓")
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor.from_string(color)


def add_flow_box(doc, title, body_lines, header_color, table_width_cm=14):
    """
    흐름도용 박스 1개 추가 (2행 1열 표).
    1행: 컬러 헤더 (제목)
    2행: 흰색 본문
    """
    table = doc.add_table(rows=2, cols=1)
    table.alignment = 1   # 가운데 정렬
    table.autofit = False

    # 너비
    for row in table.rows:
        for cell in row.cells:
            cell.width = Cm(table_width_cm)
            set_cell_border(cell, color=header_color, size="12")

    # 헤더
    head = table.rows[0].cells[0]
    set_cell_bg(head, header_color)
    head.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    add_para_text(head, title, bold=True, size=14, color="FFFFFF")

    # 본문
    body = table.rows[1].cells[0]
    set_cell_bg(body, "FFFFFF")
    body.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    para = body.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, line in enumerate(body_lines):
        if i == 0:
            run = para.add_run(line)
        else:
            run = para.add_run("\n" + line)
        run.font.size = Pt(11)
        run.font.name = "맑은 고딕"
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.append(rFonts)
        rFonts.set(qn("w:eastAsia"), "맑은 고딕")


def add_section_heading(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = "맑은 고딕"
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), "맑은 고딕")


# ──────────────────────────────────────────────────
# 문서 생성
# ──────────────────────────────────────────────────
doc = Document()

# 페이지 여백 줄이기 (한글 기본 여백과 비슷하게)
section = doc.sections[0]
section.top_margin    = Cm(2.0)
section.bottom_margin = Cm(2.0)
section.left_margin   = Cm(2.5)
section.right_margin  = Cm(2.5)

# 색상 (16진수)
BLUE       = "3B82F6"
CYAN       = "06B6D4"
PURPLE     = "9333EA"
AMBER      = "F59E0B"
DARK_GREEN = "2E7D32"
GREEN      = "4CAF50"
RED        = "DC3545"
ORANGE     = "EA580C"
LIGHT_GRAY = "F1F5F9"
BG_GREEN   = "E8F5E9"
GRAY_TEXT  = "64748B"


# ══════════════════════════════════════════════════
# ① 시스템 전체 흐름도
# ══════════════════════════════════════════════════
add_section_heading(doc, "시스템 전체 흐름도")

stages = [
    ("입력 (Input)",       ["CCTV 카메라 (RTSP) / 로컬 영상 파일"],                                       BLUE),
    ("전처리",              ["OpenCV 프레임 추출", "야간 자동 밝기 보정 (CLAHE)"],                          CYAN),
    ("객체 인식",           ["YOLOv8 (nano) 추론", "person · car 클래스 필터링"],                          PURPLE),
    ("정지 차량 판정",      ["좌표 비교 기반 자체 알고리즘", "10초 이상 이동량 30px 미만 → pk.car"],         AMBER),
    ("위험 판단",           ["(이동) 차량 + 사람 동시 존재", "사람의 발 위치 ∈ ROI → 위험 상태"],            DARK_GREEN),
    ("시각·청각 경고",      ["빨간 테두리 + 경고 텍스트", "경고음 (Web Audio API) 자동 재생"],              RED),
    ("이벤트 자동 저장",    ["캡처 이미지 · 전 5초 + 후 10초 클립 영상", "CSV 로그 기록"],                  ORANGE),
]
for i, (title, body, color) in enumerate(stages):
    add_flow_box(doc, title, body, color)
    if i < len(stages) - 1:
        add_arrow(doc)

doc.add_page_break()


# ══════════════════════════════════════════════════
# ② 위험 판단 로직 흐름도
# ══════════════════════════════════════════════════
add_section_heading(doc, "위험 판단 로직 흐름도")

add_flow_box(doc, "프레임 수신 및 YOLOv8 객체 탐지", [""], BLUE)
add_arrow(doc)

# 조건 분기를 3개 박스로 표현 (마름모 대신)
add_flow_box(doc, "조건 ① 사람 객체 존재?", ["NO → 🟢 정상  /  YES → 다음 단계"], DARK_GREEN)
add_arrow(doc)
add_flow_box(doc, "조건 ② 이동 차량 존재? (정지 차량 제외)", ["NO → 🟢 정상  /  YES → 다음 단계"], DARK_GREEN)
add_arrow(doc)
add_flow_box(doc, "조건 ③ 사람의 발 위치가 ROI 내부?", ["NO → 🟢 정상  /  YES → 다음 단계"], DARK_GREEN)
add_arrow(doc)
add_flow_box(doc, "🚨 위험 상태 (Danger)", ["3가지 조건 모두 만족 시 위험으로 판정"], RED)
add_arrow(doc)
add_flow_box(doc, "이전 상태가 정상 → 위험 전환?", [
    "YES → 이벤트 트리거 (이미지 저장 + 10초 후속 녹화 + 클립 저장 + 경고음, 15초 쿨다운)",
    "NO  → 상태 유지 (위험 상태 유지, 중복 발생 방지)",
], AMBER)

doc.add_page_break()


# ══════════════════════════════════════════════════
# ③ 정지 차량 판정 알고리즘
# ══════════════════════════════════════════════════
add_section_heading(doc, "정지 차량 판정 알고리즘 (좌표 비교 방식)")

# 부제 단락
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
sub_run = sub.add_run("AI 객체 추적(ByteTrack 등) 사용하지 않고 YOLO 좌표만으로 정지 여부 판정")
sub_run.font.size = Pt(11)
sub_run.font.color.rgb = RGBColor.from_string(GRAY_TEXT)
sub_run.font.name = "맑은 고딕"

steps = [
    ("① 프레임의 차량 중심 좌표 추출", "YOLOv8 결과에서 class='car' 박스의 중심 (cx, cy) 계산"),
    ("② 기존 슬롯과 거리 매칭",        "현재 좌표와 가장 가까운 슬롯(MATCH_DISTANCE_PX=80) 찾아 매칭"),
    ("③ 매칭 성공 → 위치 이력에 추가", "(현재시각, 좌표) 형식으로 슬롯에 누적 저장"),
    ("④ 10초 이전 위치와 비교",        "현재 좌표와 10초 전 좌표의 유클리드 거리(현재좌표 − 10초전좌표) 측정"),
    ("⑤ 거리 < 30px → 정지 차량 판정", "is_parked=True 플래그 부여, 위험 판단에서 제외, pk.car 라벨"),
]
for i, (title, body) in enumerate(steps):
    add_flow_box(doc, title, [body], DARK_GREEN)
    if i < len(steps) - 1:
        add_arrow(doc)

# 하단 설명 박스
doc.add_paragraph()
add_flow_box(doc, "💡 알고리즘 채택 이유", [
    "ByteTrack 등 AI 추적 알고리즘은 CPU 환경에서 FPS 급감 발생",
    "→ 좌표 비교만으로 충분히 정확하면서 실시간성을 유지할 수 있는 자체 로직 설계",
    "→ 유클리드 거리 공식: d = √((x₁−x₂)² + (y₁−y₂)²)",
], GREEN)

doc.add_page_break()


# ══════════════════════════════════════════════════
# ④ 이벤트 클립 영상 저장 흐름도
# ══════════════════════════════════════════════════
add_section_heading(doc, "이벤트 클립 영상 저장 흐름도")

sub = doc.add_paragraph()
sub_run = sub.add_run("전 5초 + 후 10초 = 총 15초 클립 자동 녹화")
sub_run.font.size = Pt(11)
sub_run.font.color.rgb = RGBColor.from_string(GRAY_TEXT)
sub_run.font.name = "맑은 고딕"

# 타임라인 표 (1행 3열)
doc.add_paragraph()
timeline = doc.add_table(rows=2, cols=3)
timeline.alignment = 1
timeline.autofit = False

# 1행: 구간 라벨
labels = [
    ("전 5초 (frame_buffer)", BLUE, "FFFFFF"),
    ("⚡ 이벤트 발생 (t = 0초)", RED, "FFFFFF"),
    ("후 10초 (post_frames)", RED, "FFFFFF"),
]
for cell, (text, bg, fg) in zip(timeline.rows[0].cells, labels):
    cell.width = Cm(5)
    set_cell_bg(cell, bg)
    set_cell_border(cell, color=bg, size="12")
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    add_para_text(cell, text, bold=True, size=12, color=fg)

# 2행: 설명
descs = [
    "이벤트 발생 직전 5초 분량의 프레임을 순환 버퍼(deque)에 항상 보관",
    "이벤트 트리거 시점 (전·후 클립의 경계점)",
    "이벤트 트리거 후 10초 동안의 프레임을 실시간으로 수집",
]
for cell, desc in zip(timeline.rows[1].cells, descs):
    cell.width = Cm(5)
    set_cell_bg(cell, "FFFFFF")
    set_cell_border(cell, color="CCCCCC", size="6")
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    add_para_text(cell, desc, size=10, color="000000")

doc.add_paragraph()
doc.add_paragraph()

# 처리 순서 (3단계)
processes = [
    ("① 발생 즉시 (t = 0초)", AMBER, [
        "• 캡처 이미지 저장 (.jpg)",
        "• pre_frames = buffer 복사 (직전 5초 프레임)",
        "• post_recording = True (후속 녹화 시작)",
    ]),
    ("② 후속 녹화 (이벤트 이후 10초간)", BLUE, [
        "• 매 프레임 post_frames 리스트에 누적",
        "• 동시에 실시간 모니터링은 계속 진행",
        "• 15초 쿨다운 적용으로 중복 이벤트 방지",
    ]),
    ("③ 10초 후 클립 영상 저장", DARK_GREEN, [
        "• 전 5초 + 후 10초 프레임을 합쳐 .mp4 생성",
        "• 재생 시 H.264 자동 변환 + 결과 캐싱",
        "• CSV 로그에 시간 · 소스 · 파일명 기록",
    ]),
]
for i, (title, color, body) in enumerate(processes):
    add_flow_box(doc, title, body, color)
    if i < len(processes) - 1:
        add_arrow(doc)


# ──────────────────────────────────────────────────
output_path = os.path.join(OUT, "결과보고서_흐름도.docx")
doc.save(output_path)
print(f"✅ 생성 완료: {output_path}")
print()
print("📌 사용법:")
print("  1. 한글(HWP)에서 [파일 → 불러오기]로 위 docx 파일 열기")
print("  2. 색상·표·텍스트가 그대로 들어옴 → 필요하면 한글에서 수정")
print("  3. [파일 → 다른 이름으로 저장]에서 .hwp 선택")
