# generate_personal_opensource_report.py — 팀장 개인 오픈소스 사용 보고서
# 실행: python generate_personal_opensource_report.py

import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


OUTPUT = os.path.join(os.path.dirname(__file__), "팀장_오픈소스_사용보고서.docx")

doc = Document()

# ── 기본 스타일 (맑은 고딕, 11pt) ──────────────────────────
style = doc.styles["Normal"]
style.font.name = "맑은 고딕"
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")

# 페이지 여백
for section in doc.sections:
    section.top_margin    = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.2)
    section.right_margin  = Cm(2.2)


def set_run_font(run, size=11, bold=False, color=None, font="맑은 고딕"):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), font)


def add_title(text, size=18):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run_font(run, size=size, bold=True, color=RGBColor(46, 125, 50))


def add_h1(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=14, bold=True, color=RGBColor(46, 125, 50))
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)


def add_body(text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    set_run_font(run, size=11)


def fill_cell(cell, text, bold=False, size=10, color=None, bg=None, align=None):
    cell.text = ""
    para = cell.paragraphs[0]
    if align:
        para.alignment = align
    run = para.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if bg:
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), bg)
        tc_pr.append(shd)


# ══════════════════════════════════════════════════════
# 표지/제목
# ══════════════════════════════════════════════════════
add_title("팀장 개인 오픈소스 사용 보고서", size=18)
add_title("SAFEVIEW — AI 기반 사각지대 위험 감지 시스템", size=12)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("팀명 : 세이프뷰(SAFEVIEW)    |    담당 : 팀장")
set_run_font(run, size=11)

doc.add_paragraph()

# ══════════════════════════════════════════════════════
# 1. 팀장 담당 역할
# ══════════════════════════════════════════════════════
add_h1("1. 팀장 담당 역할")

add_body(
    "본인은 팀장으로서 프로젝트 전반의 기획과 통합을 총괄했으며 다음 네 가지 영역을 "
    "직접 담당했다."
)

bullets = [
    "총괄 기획 및 기능 통합",
    "팀 일정 조율",
    "계획서 및 결과 보고서 작성",
    "위험 판단 및 경고 로직 설계",
]
for b in bullets:
    p = doc.add_paragraph(b, style="List Bullet")
    p.paragraph_format.line_spacing = 1.4
    for r in p.runs:
        set_run_font(r, size=11)


# ══════════════════════════════════════════════════════
# 2. 팀장 담당 영역 오픈소스 사용 목록
# ══════════════════════════════════════════════════════
add_h1("2. 팀장 담당 영역 오픈소스 사용 목록")

add_body(
    "팀 전체가 사용한 오픈소스 중에서 본인의 담당 역할(총괄 기획·기능 통합·위험 판단 및 "
    "경고 로직 설계)에 직접 사용한 오픈소스만 정리한 목록은 다음과 같다."
)

# 표 생성: 6열 (오픈소스명, 버전, 사용 목적, 적용 기능, 라이선스)
data = [
    ["오픈소스명", "버전", "사용 목적", "팀장 역할 내 적용 기능", "라이선스"],
    [
        "Streamlit",
        "1.55.0",
        "파이썬만으로 인터랙티브 웹 UI 구축",
        "5개 페이지(대시보드 · 모니터링 · ROI 설정 · 이벤트 다시보기 · 성능 평가)를 하나의 멀티페이지 앱으로 통합 / 사이드바·레이아웃·세션 상태 설계",
        "Apache 2.0",
    ],
    [
        "OpenCV",
        "4.8+",
        "영상 입출력 및 프레임 처리",
        "위험 판단 로직에서 ROI 다각형 침입 판정(pointPolygonTest) / 위험 발생 시 화면 테두리·바운딩 박스·붉은 오버레이 렌더링 / 경고 시각화",
        "Apache 2.0",
    ],
    [
        "NumPy",
        "1.24+",
        "다차원 배열 연산 처리",
        "위험 판단에서 ROI 다각형 좌표 배열화 및 사람 발 위치(bottom_center) 좌표 계산 / 영상 프레임 배열 처리",
        "BSD-3-Clause",
    ],
    [
        "Pillow (PIL Fork)",
        "10.0+",
        "이미지 생성·편집·텍스트 합성",
        "위험 감지 시 한글 '경고' 텍스트를 굵고 선명하게 화면 중앙에 렌더링(OpenCV는 한글 미지원) / 대기 화면 안내 이미지 생성",
        "HPND (MIT 호환)",
    ],
    [
        "Cloudflare Tunnel (Cloudflared)",
        "2024+",
        "로컬 서버를 외부 HTTPS로 배포",
        "총괄 기획 차원의 외부 시연 환경 구축 / 발표·중간 점검 시 팀원과 평가자에게 즉시 HTTPS 링크로 시스템 공유",
        "Apache 2.0",
    ],
]

table = doc.add_table(rows=len(data), cols=5)
table.style = "Light Grid Accent 1"
table.autofit = False

# 컬럼 폭 설정
widths = [Cm(3.0), Cm(1.5), Cm(3.5), Cm(6.0), Cm(2.5)]
for col_idx, w in enumerate(widths):
    for row in table.rows:
        row.cells[col_idx].width = w

# 헤더 채우기
for col_idx, val in enumerate(data[0]):
    fill_cell(
        table.rows[0].cells[col_idx],
        val, bold=True, size=10,
        color=RGBColor(255, 255, 255),
        bg="2E7D32",
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

# 데이터 채우기
for row_idx in range(1, len(data)):
    for col_idx, val in enumerate(data[row_idx]):
        align = WD_ALIGN_PARAGRAPH.CENTER if col_idx in (0, 1, 4) else WD_ALIGN_PARAGRAPH.LEFT
        bold = (col_idx == 0)
        fill_cell(
            table.rows[row_idx].cells[col_idx],
            val, bold=bold, size=10, align=align,
        )


# ══════════════════════════════════════════════════════
# 3. 역할별 매핑 요약
# ══════════════════════════════════════════════════════
add_h1("3. 역할별 오픈소스 매핑")

map_data = [
    ["담당 역할", "사용 오픈소스"],
    ["총괄 기획 및 기능 통합", "Streamlit · Cloudflare Tunnel"],
    ["위험 판단 및 경고 로직 설계", "OpenCV · NumPy · Pillow"],
    ["일정 조율 / 계획서·보고서 작성", "(오픈소스 직접 사용 없음 — 회의·문서 작업 영역)"],
]

map_table = doc.add_table(rows=len(map_data), cols=2)
map_table.style = "Light Grid Accent 1"
map_widths = [Cm(6.5), Cm(10.0)]
for col_idx, w in enumerate(map_widths):
    for row in map_table.rows:
        row.cells[col_idx].width = w

for col_idx, val in enumerate(map_data[0]):
    fill_cell(
        map_table.rows[0].cells[col_idx],
        val, bold=True, size=10,
        color=RGBColor(255, 255, 255),
        bg="2E7D32",
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

for row_idx in range(1, len(map_data)):
    for col_idx, val in enumerate(map_data[row_idx]):
        bold = (col_idx == 0)
        fill_cell(
            map_table.rows[row_idx].cells[col_idx],
            val, bold=bold, size=10,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )


# ══════════════════════════════════════════════════════
# 4. 오픈소스별 상세 활용 내역
# ══════════════════════════════════════════════════════
add_h1("4. 오픈소스별 상세 활용 내역")

add_body(
    "[Streamlit] 프로젝트 전체 UI 구조를 설계하고 5개 페이지를 하나의 앱으로 통합하는 데 "
    "사용했다. st.navigation 기반 멀티페이지 구성과 사이드바·세션 상태 관리·실시간 영상 "
    "갱신을 위한 st.empty() 플레이스홀더 패턴을 설계했다. 페이지 간 데이터 공유와 시스템 "
    "상태 표시 등 기능 통합의 중심축 역할을 수행했다."
)

add_body(
    "[OpenCV] 위험 판단 및 경고 로직의 핵심 라이브러리로 사용했다. ROI 다각형 안에 "
    "사람의 발 위치가 들어가는지 판정하는 pointPolygonTest 연산과 위험 발생 시 화면 "
    "테두리 강조 바운딩 박스 그리기 붉은 오버레이 적용 등 경고 시각화를 직접 구현했다."
)

add_body(
    "[NumPy] 위험 판단 과정에서 ROI 다각형 좌표를 numpy 배열로 다루고 사람의 발 "
    "위치(bottom_center) 좌표 계산과 영상 프레임 데이터 처리에 사용했다. 위험 판단 로직의 "
    "수치 연산 전반에 적용됐다."
)

add_body(
    "[Pillow] OpenCV는 한글 텍스트 렌더링을 지원하지 않기 때문에 위험 발생 시 화면 중앙에 "
    "'경고' 텍스트를 굵고 선명하게 표시하기 위해 사용했다. 맑은 고딕 폰트를 PIL ImageFont로 "
    "로드해 한글 출력을 처리했고 대기 화면의 안내 이미지 생성에도 활용했다."
)

add_body(
    "[Cloudflare Tunnel] 외부 시연 환경 구축을 위해 사용했다. 로컬 Streamlit 서버를 "
    "임시 HTTPS 링크로 노출시켜 팀원과 발표 참가자가 별도 설치 없이 브라우저로 즉시 "
    "시스템을 시연하고 확인할 수 있도록 했다. 총괄 기획의 일환으로 외부 공유 인프라를 "
    "직접 구성했다."
)


# ══════════════════════════════════════════════════════
# 5. 라이선스 준수 및 기여 사항
# ══════════════════════════════════════════════════════
add_h1("5. 라이선스 준수 사항")

add_body(
    "사용한 오픈소스는 모두 상용·비상용 사용이 모두 허용된 라이선스(Apache 2.0 · "
    "BSD-3-Clause · HPND/MIT 호환)이며 본 프로젝트는 학부 캡스톤디자인 결과물로 비영리 "
    "교육 목적에만 활용된다. 각 라이선스에서 요구하는 저작권 표시와 라이선스 고지 의무를 "
    "준수하며 사용 목록과 라이선스 정보를 본 보고서와 프로젝트 README에 명시하고 있다."
)

doc.add_paragraph()


# 저장
doc.save(OUTPUT)
print(f"[완료] 보고서 저장 → {OUTPUT}")

# 자동 열기
try:
    os.startfile(OUTPUT)
    print("[열기] Word에서 파일을 여는 중...")
except Exception as e:
    print(f"[실패] 파일 열기 실패: {e}")
