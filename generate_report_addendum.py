# generate_report_addendum.py — 결과보고서 추가/수정 사항 정리 워드
# 실행: python generate_report_addendum.py

import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


OUTPUT = os.path.join(os.path.dirname(__file__), "결과보고서_추가수정사항.docx")

doc = Document()

# ── 기본 스타일 ───────────────────────────────────────
style = doc.styles["Normal"]
style.font.name = "맑은 고딕"
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")

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
    set_run_font(run, size=15, bold=True, color=RGBColor(46, 125, 50))
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)


def add_h2(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=13, bold=True, color=RGBColor(33, 33, 33))
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)


def add_h3(text, color=RGBColor(200, 80, 0)):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=11, bold=True, color=color)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)


def add_body(text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    set_run_font(run, size=11)


def add_bullet(text):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(2)
    for r in p.runs:
        set_run_font(r, size=11)


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


def add_table(headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    if col_widths:
        for col_idx, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[col_idx].width = w
    for col_idx, h in enumerate(headers):
        fill_cell(table.rows[0].cells[col_idx], h, bold=True, size=10,
                  color=RGBColor(255, 255, 255), bg="2E7D32",
                  align=WD_ALIGN_PARAGRAPH.CENTER)
    for row_idx, row in enumerate(rows, start=1):
        for col_idx, val in enumerate(row):
            align = WD_ALIGN_PARAGRAPH.CENTER if col_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            fill_cell(table.rows[row_idx].cells[col_idx], val,
                      bold=(col_idx == 0), size=10, align=align)


# ══════════════════════════════════════════════════════
# 표지
# ══════════════════════════════════════════════════════
add_title("SAFEVIEW 결과보고서", size=18)
add_title("추가 / 수정 사항 정리", size=16)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(
    "이 문서는 기존 SAFEVIEW_결과보고서.docx 작성 이후 진행된 "
    "기능 추가·수정·버그 해결 사항을 섹션별로 정리한 것이다.\n"
    "각 항목은 원본 보고서의 어느 섹션에 추가/교체되는지를 [표시] 형태로 명시했다."
)
set_run_font(run, size=10, color=RGBColor(100, 100, 100))

doc.add_paragraph()


# ══════════════════════════════════════════════════════
# 4. 작품 개요 — 추가 사항
# ══════════════════════════════════════════════════════
add_h1("◆ 4. 작품 개요 — 추가 사항")

add_h2("4.1 작품의 특징 (추가 항목)")
add_h3("[기존 특징 목록 끝에 다음 항목을 추가]")
add_bullet("영상 파일 업로드 — PC 어디서나 드래그앤드롭 또는 클릭으로 영상 선택. data 폴더에 자동 저장되어 다음 실행 시에도 selectbox에서 그대로 선택 가능")
add_bullet("영상 파일 삭제 — 확인 다이얼로그를 거치는 안전 삭제 (모니터링·ROI 설정 페이지 모두 제공)")
add_bullet("영상 재생 컨트롤 — 재생/일시정지 버튼, 시크 슬라이더, 실시간 진행률 바 (파일 모드 한정)")
add_bullet("오토바이 통합 검출 — YOLOv8의 motorcycle 클래스를 자동으로 car로 매핑하여 위험 판단과 정지 차량 분리에 동일 적용")
add_bullet("적응형 처리 해상도 — 1080p 이상 영상은 자동으로 960px 폭으로 축소 처리, ROI 좌표도 같은 비율로 스케일 조정되어 위치 일치")
add_bullet("비동기 YOLO 추론 — 영상 표시(메인 루프)와 객체 검출(백그라운드 워커)을 분리해 모든 프레임을 매끄럽게 표시")

add_h2("4.2 기능 및 구조 (구조 보강)")
add_h3("[처리 단계 설명에 다음 한 줄을 추가]")
add_body(
    "메인 루프는 영상 디코딩과 화면 표시만 담당하고 YOLO 추론은 백그라운드 워커가 별도로 수행한다. "
    "메인 루프는 워커가 캐싱해 둔 가장 최근 검출 결과를 가져와 박스와 ROI를 오버레이한다. "
    "원본 해상도가 1080p를 넘으면 처리용 프레임을 960px 폭으로 자동 축소하여 메인 루프 부담을 줄인다."
)


# ══════════════════════════════════════════════════════
# 5. 제작 과정 — 추가 사항
# ══════════════════════════════════════════════════════
add_h1("◆ 5. 제작 과정 — 추가 사항")

add_h2("5.2 구현 및 제작 단계 (단계 추가)")
add_h3("[기존 11단계 뒤에 다음 단계를 추가]")
add_bullet("12단계 — 모니터링·ROI 설정 페이지에 영상 파일 업로드(st.file_uploader)와 영상 삭제(확인 다이얼로그 포함) 기능 추가")
add_bullet("13단계 — 모니터링 화면에 재생/일시정지 버튼, 시크 슬라이더, 진행률 바를 추가하고 시작/정지 버튼을 영상 선택 바로 아래로 이동해 동선 단축")
add_bullet("14단계 — ROI 매칭 디버깅 표시 개선 (어떤 이름으로 ROI를 찾고 있는지, 저장된 ROI 전체 목록을 화면에 안내) + ROI 설정 페이지에서 영상 변경 시 ROI 이름 자동 동기화")
add_bullet("15단계 — 비동기 YOLO 워커(AsyncDetectorWorker) 도입 + 처리 해상도 자동 축소(PROC_MAX_W=960) + fps 기반 sleep으로 영상 매끄러운 재생 확보")
add_bullet("16단계 — 오토바이 검출 추가 (TARGET_CLASS_IDS에 motorcycle 포함, class_name을 car로 통합 매핑)")
add_bullet("17단계 — 청각 경고음 시스템을 Web Audio API에서 HTML5 audio autoplay 방식으로 교체. wave 모듈로 880Hz 비프음을 코드에서 직접 생성해 base64로 임베드. 삑삑×3 묶음(총 6회) 패턴")
add_bullet("18단계 — Cloudflare Tunnel 외부 공유 자동화 (서버열기 슬래시 명령으로 Streamlit 실행 + 터널 생성 + URL 클립보드 자동 복사까지 한 번에 수행)")

add_h2("5.3 테스트 및 개선 (추가 발견 이슈)")
add_h3("[기존 이슈 목록 뒤에 다음 항목을 추가]")
add_bullet("청각 경고음이 들리지 않는 문제 → Streamlit이 markdown 내부의 script 태그를 보안상 차단해서 발생 → HTML5 audio autoplay + base64 wav 임베드 방식으로 우회")
add_bullet("영상 파일이 슬로우모션처럼 느리게 재생되는 문제 → CPU 환경 YOLO 추론 병목 + 큰 영상 데이터 전송 비용 → 비동기 YOLO 워커 + 처리 해상도 축소 + fps sleep 조합으로 해결")
add_bullet("오토바이가 인식되지 않는 문제 → TARGET_CLASS_IDS에 motorcycle ID(3)가 빠져 있어서 검출 단계부터 필터링 → 추가 후 class_name을 car로 매핑")
add_bullet("ROI 다각형이 화면에 보이지 않는 문제 → 영상 파일명과 저장된 ROI 이름이 어긋남 → ROI 설정 페이지에서 영상 변경 시 ROI 이름 자동 동기화 + 모니터링 페이지에서 저장된 ROI 목록 안내")


# ══════════════════════════════════════════════════════
# 6. 결과 분석 — 추가 사항
# ══════════════════════════════════════════════════════
add_h1("◆ 6. 결과 분석 — 추가 사항")

add_h2("6.1 기능별 결과 (표에 행 추가)")
add_h3("[기존 기능 결과 표에 다음 행을 추가]")

add_table(
    headers=["기능", "결과"],
    rows=[
        ["영상 파일 업로드", "드래그앤드롭으로 PC 어디서나 영상 선택, data 폴더에 자동 저장 및 selectbox 자동 연동"],
        ["영상 파일 삭제", "확인 다이얼로그 거친 안전 삭제 (재생 중 차단)"],
        ["재생 컨트롤", "재생/정지/시크 슬라이더/실시간 진행률 표시 정상"],
        ["비동기 YOLO 추론", "메인 루프는 매끄럽게 유지, 검출만 백그라운드 처리"],
        ["처리 해상도 축소", "1080p → 960px 처리 시 데이터량 약 44% 감소, 메인 루프 사이클 단축"],
        ["오토바이 검출", "YOLOv8n이 motorcycle 감지 시 car로 통합 매핑되어 위험 판단·정지 분리 정상 동작"],
        ["청각 경고음", "삑삑×3 묶음(총 6회) 자동 재생 정상"],
        ["외부 공유 자동화", "한 명령으로 Streamlit 실행 + Cloudflare 터널 + URL 자동 복사까지 완료"],
    ],
    col_widths=[Cm(4.5), Cm(11.5)],
)

add_h2("6.2 결과 비교 및 평가 (보강 문단)")
add_h3("[6.2 끝에 다음 문단을 추가]")
add_body(
    "비동기 YOLO 도입과 처리 해상도 축소 적용 전후로 영상 재생 매끄러움에 큰 차이가 있었다. "
    "기존 방식에서는 1080p 영상이 CPU 환경에서 5~10fps 수준으로 떨어져 슬로우모션이 됐지만 "
    "두 가지 최적화 도입 후에는 30fps 영상이 거의 원본 속도로 재생되었다. "
    "검출 박스는 백그라운드 추론 특성상 미세하게 지연되지만 시연 영상에서 사람 눈으로 인지하기는 어려운 수준이다."
)


# ══════════════════════════════════════════════════════
# 7. 문제점 및 해결 방안 — 추가 사항
# ══════════════════════════════════════════════════════
add_h1("◆ 7. 문제점 및 해결 방안 — 추가 사항")

add_h2("7.2 해결 방안 표 (행 추가)")
add_h3("[기존 문제-해결 매핑 표에 다음 행을 추가]")

add_table(
    headers=["문제", "해결 방안"],
    rows=[
        ["Streamlit이 markdown 내 script를 차단해 경고음이 재생되지 않음",
         "components.v1.html()로 새 iframe을 생성하고 HTML5 audio autoplay + base64 wav 임베드 방식으로 강제 재생"],
        ["CPU 환경 1080p 영상이 슬로우모션처럼 느림",
         "비동기 YOLO 워커(AsyncDetectorWorker) + 처리 해상도 자동 축소(PROC_MAX_W=960) + fps 기반 sleep 조합"],
        ["영상 파일명과 저장된 ROI 이름이 어긋나 ROI가 적용되지 않음",
         "ROI 설정 페이지에서 영상 변경 시 ROI 이름 자동 동기화 + 모니터링 페이지에서 저장된 ROI 목록을 화면에 표시해 매칭 어긋남을 즉시 확인"],
        ["오토바이가 검출되지 않음",
         "TARGET_CLASS_IDS에 motorcycle(3) 추가 + detector에서 class_name을 car로 통합 매핑"],
        ["영상 파일 관리(추가·삭제)가 번거로움",
         "st.file_uploader로 드래그앤드롭 업로드 + 확인 다이얼로그 거친 삭제 UI 추가"],
        ["로컬 영상 시연 시 일시정지·시크 불가",
         "재생/일시정지 버튼 + 시크 슬라이더 + 진행률 바 추가 (파일 모드)"],
        ["외부 공유 환경을 매번 수동으로 실행해야 함",
         "서버열기 슬래시 명령으로 Streamlit 실행 + Cloudflare Tunnel 생성 + URL 클립보드 자동 복사를 한 번에 수행"],
        ["위험 경고 텍스트가 좁은 박스에서 줄바꿈되어 어색함",
         "danger-title CSS에 white-space: nowrap 적용 + 폰트 크기 1.8rem으로 미세 조정"],
    ],
    col_widths=[Cm(7.5), Cm(8.5)],
)


# ══════════════════════════════════════════════════════
# 8. 결론 — 보강 사항
# ══════════════════════════════════════════════════════
add_h1("◆ 8. 결론 — 보강 사항")

add_h2("8.1 연구 결과 요약 (문단 보강)")
add_h3("[8.1 끝에 다음 문장을 추가]")
add_body(
    "이외에도 사용자 편의성과 시연 안정성을 높이기 위해 영상 파일 업로드·삭제 관리 기능, "
    "재생/일시정지/시크 컨트롤, ROI 매칭 디버깅 안내, 오토바이 통합 검출, "
    "삑삑×3 묶음의 청각 경고음, 비동기 YOLO 추론과 처리 해상도 적응 축소, "
    "Cloudflare Tunnel 외부 공유 자동화 등을 추가 구현했다."
)

add_h2("8.2 의의 및 한계점 (한계 항목 보강)")
add_h3("[한계 목록에 다음 항목을 추가]")
add_bullet("비동기 추론 구조 특성상 검출 박스가 영상 화면 대비 미세하게(약 100~200ms) 지연될 수 있다. 일반적인 시연 환경에서는 눈에 띄지 않는 수준이지만 매우 빠르게 움직이는 객체에서는 박스 위치가 약간 늦게 따라올 수 있다.")

doc.add_paragraph()


# 저장
doc.save(OUTPUT)
print(f"[완료] 추가/수정 사항 정리본 저장 → {OUTPUT}")

# 자동 열기
try:
    os.startfile(OUTPUT)
    print("[열기] Word에서 파일을 여는 중...")
except Exception as e:
    print(f"[실패] 파일 열기 실패: {e}")
