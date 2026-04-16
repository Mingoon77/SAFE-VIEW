# generate_diagram.py — 발표용 시스템 구조도 생성
# 실행: python generate_diagram.py

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.font_manager as fm
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 색상 팔레트
C_INPUT      = "#60A5FA"   # 파랑 - 입력
C_TRANSMIT   = "#A78BFA"   # 보라 - 전송
C_PROCESS    = "#4CAF50"   # 초록 - 처리 (메인)
C_OUTPUT     = "#F59E0B"   # 주황 - 출력
C_STORAGE    = "#6B7280"   # 회색 - 저장
C_TEXT       = "#1a1a1a"
C_WHITE      = "#FFFFFF"
C_BG         = "#F4F7F9"
C_BORDER     = "#CBD5E1"


def draw_box(ax, x, y, w, h, color, title, items=None, title_color=C_WHITE):
    """둥근 박스 + 제목 + 항목 리스트"""
    # 박스 외곽
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        linewidth=1.5, edgecolor=color, facecolor=C_WHITE, zorder=2
    )
    ax.add_patch(box)

    # 제목 배경
    title_h = 0.5
    title_bar = FancyBboxPatch(
        (x, y + h - title_h), w, title_h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        linewidth=0, facecolor=color, zorder=3
    )
    ax.add_patch(title_bar)

    # 제목 텍스트
    ax.text(x + w/2, y + h - title_h/2, title,
            ha="center", va="center", fontsize=13, fontweight="bold",
            color=title_color, zorder=4)

    # 항목 리스트
    if items:
        for i, item in enumerate(items):
            ax.text(x + 0.15, y + h - title_h - 0.35 - i*0.4, f"• {item}",
                    ha="left", va="center", fontsize=10, color=C_TEXT, zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, color=C_PROCESS):
    """화살표"""
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="->,head_width=0.3,head_length=0.4",
        color=color, linewidth=2.5, zorder=1
    )
    ax.add_patch(arrow)


# ══════════════════════════════════════════════════════
# 다이어그램 생성
# ══════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(18, 10))
ax.set_xlim(0, 20)
ax.set_ylim(0, 11)
ax.axis("off")
fig.patch.set_facecolor(C_BG)

# 제목
ax.text(10, 10.5, "SAFEVIEW 시스템 구조도",
        ha="center", va="center", fontsize=22, fontweight="bold", color=C_TEXT)
ax.text(10, 10.0, "AI 기반 사각지대 위험 감지 시스템",
        ha="center", va="center", fontsize=13, color="#64748B")

# ── 1. Input (입력) ────────────────────────────────────
draw_box(ax, 0.5, 6.5, 3.2, 2.8, C_INPUT, "1. Input (입력)",
         ["CCTV 카메라 (RTSP)", "H.264 코덱", "영상 파일 (.mp4)", "첫 프레임 추출"])

# ── 2. Transmission (전송) ─────────────────────────────
draw_box(ax, 4.3, 6.5, 3.2, 2.8, C_TRANSMIT, "2. Transmission (전송)",
         ["RTSP 스트림", "백그라운드 스레드", "버퍼 최소화", "로컬 파일 I/O"])

# ── 3. Processing (처리) — 메인 ──────────────────────────
draw_box(ax, 8.1, 4.5, 5.0, 4.8, C_PROCESS, "3. Processing (핵심 처리)",
         ["OpenCV: 프레임 획득 · BGR 변환",
          "YOLOv8n: Person / Car 탐지",
          "바운딩 박스 + 신뢰도 출력",
          "ROI 다각형 내부 판정",
          "위험 상태 판단 (규칙 기반)",
          "이벤트 발생 감지 (정상→위험)"])

# ── 4. Output (출력) ───────────────────────────────────
draw_box(ax, 13.7, 6.5, 5.8, 2.8, C_OUTPUT, "4. Output (시청각 경고)",
         ["Streamlit UI: 실시간 영상 표시",
          "바운딩 박스 오버레이",
          "상태창: [정상] / [경고]",
          "위험 시 빨간 테두리 + DANGER 텍스트"])

# ── 5. Storage (저장) ──────────────────────────────────
draw_box(ax, 13.7, 3.0, 5.8, 3.0, C_STORAGE, "5. Storage (저장/기록)",
         ["이벤트 캡처 이미지 (.jpg)",
          "클립 영상 (전 5초 + 후 10초)",
          "H.264 변환 (_converted/)",
          "CSV 로그 (events_log.csv)"])

# ── 6. User Interaction (사용자) ───────────────────────
draw_box(ax, 0.5, 3.0, 7.0, 3.0, "#EC4899", "6. User Interaction (사용자)",
         ["ROI 관심구역 마우스로 직접 설정",
          "영상 소스 선택 (CCTV / 파일)",
          "이벤트 다시보기 (캘린더 조회)",
          "원격 공유 모드 (Cloudflare Tunnel)"])

# ── 화살표 (데이터 흐름) ───────────────────────────────
# Input → Transmission
draw_arrow(ax, 3.7, 7.9, 4.3, 7.9, C_INPUT)
# Transmission → Processing
draw_arrow(ax, 7.5, 7.9, 8.1, 7.5, C_TRANSMIT)
# Processing → Output
draw_arrow(ax, 13.1, 7.9, 13.7, 7.9, C_OUTPUT)
# Processing → Storage
draw_arrow(ax, 13.1, 5.5, 13.7, 4.5, C_STORAGE)
# User → Processing (ROI 설정)
draw_arrow(ax, 7.5, 4.5, 8.1, 5.5, "#EC4899")
# Storage → User (다시보기)
draw_arrow(ax, 13.7, 3.8, 7.5, 3.8, "#6B7280")

# ── 기술 스택 라벨 (하단) ──────────────────────────────
ax.text(10, 1.8, "기술 스택",
        ha="center", va="center", fontsize=14, fontweight="bold", color=C_TEXT)

tech_items = [
    ("Python", 2.0),
    ("YOLOv8", 5.0),
    ("OpenCV", 8.0),
    ("Streamlit", 11.0),
    ("RTSP", 14.0),
    ("Cloudflare Tunnel", 17.0),
]
for label, x in tech_items:
    tech_box = FancyBboxPatch(
        (x - 1.3, 0.7), 2.6, 0.6,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        linewidth=1, edgecolor=C_BORDER, facecolor=C_WHITE
    )
    ax.add_patch(tech_box)
    ax.text(x, 1.0, label, ha="center", va="center",
            fontsize=10, fontweight="bold", color=C_TEXT)

# 저장
output_path = os.path.join(os.path.dirname(__file__), "system_diagram.png")
plt.savefig(output_path, dpi=200, bbox_inches="tight",
            facecolor=C_BG, edgecolor="none")
plt.close()

print(f"구조도 생성 완료: {output_path}")
