# pages/2_ROI_설정.py — ROI(관심구역) 직접 그리기 화면
#
# 사용 흐름:
#   1. 영상 소스 선택 → 첫 프레임 불러오기
#   2. 영상 위에 마우스로 클릭 → 꼭짓점 추가
#   3. 꼭짓점 3개 이상 → 💾 ROI 저장 클릭

import streamlit as st
import cv2
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import DATA_DIR
from core.video_source import VideoSource
from core.roi_manager  import save_roi, load_roi, list_saved_rois

try:
    from streamlit_image_coordinates import streamlit_image_coordinates
    LIB_OK = True
except ImportError:
    LIB_OK = False

# st.set_page_config는 app.py에서 1회만 호출

if not LIB_OK:
    st.error(
        "❌ `streamlit-image-coordinates` 라이브러리가 없습니다.\n\n"
        "터미널에서 실행하세요:\n```\npip install streamlit-image-coordinates\n```"
    )
    st.stop()

st.title("🗺️ ROI(관심구역) 설정")
st.markdown("영상 위에서 **마우스로 클릭**하면 꼭짓점이 추가됩니다. 3개 이상 찍은 뒤 **💾 저장** 버튼을 누르세요.")
st.markdown("---")

# ══════════════════════════════════════════════════════
# session_state 초기화
# ══════════════════════════════════════════════════════
if "roi_points"   not in st.session_state: st.session_state.roi_points   = []
if "roi_frame"    not in st.session_state: st.session_state.roi_frame    = None
if "last_click"   not in st.session_state: st.session_state.last_click   = None
if "roi_src_label" not in st.session_state: st.session_state.roi_src_label = ""

# ══════════════════════════════════════════════════════
# 헬퍼: 프레임에 현재까지 찍은 꼭짓점 + 다각형 그리기
# ══════════════════════════════════════════════════════
DISPLAY_W = 800   # 화면 표시 너비 (픽셀)

def render_frame(frame_bgr, points: list, scale: float) -> Image.Image:
    """
    원본 프레임(BGR)에 현재 ROI 꼭짓점과 다각형을 그려
    PIL Image(RGB)로 반환합니다.
    scale: 표시 크기 / 원본 크기 비율
    """
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)

    # 표시 크기로 리사이즈
    orig_h, orig_w = frame_bgr.shape[:2]
    disp_w = DISPLAY_W
    disp_h = int(orig_h * scale)
    pil = pil.resize((disp_w, disp_h), Image.LANCZOS)

    if not points:
        return pil

    draw = ImageDraw.Draw(pil)

    # 표시 좌표로 변환 (원본 → 표시 크기)
    disp_pts = [(int(x * scale), int(y * scale)) for x, y in points]

    # 다각형 채우기 (3개 이상일 때)
    if len(disp_pts) >= 3:
        draw.polygon(disp_pts, fill=(0, 255, 180, 60), outline=(0, 255, 180))

    # 선 연결
    for i in range(len(disp_pts) - 1):
        draw.line([disp_pts[i], disp_pts[i+1]], fill=(0, 255, 180), width=2)

    # 꼭짓점 원 + 번호
    for i, (px, py) in enumerate(disp_pts):
        r = 7
        draw.ellipse([(px-r, py-r), (px+r, py+r)], fill=(255, 80, 80), outline="white")
        draw.text((px + 9, py - 8), f"P{i+1}", fill="white")

    return pil


def get_video_files() -> list:
    if not os.path.exists(DATA_DIR):
        return []
    return [f for f in os.listdir(DATA_DIR)
            if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))]


# ══════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ 소스 선택")

    source_type = st.radio("영상 소스", ["📁 로컬 영상 파일", "📡 RTSP 스트림"])

    selected_source = None
    auto_label      = ""

    if source_type == "📁 로컬 영상 파일":
        files = get_video_files()
        if files:
            chosen         = st.selectbox("파일 선택", files)
            selected_source = os.path.join(DATA_DIR, chosen)
            auto_label      = os.path.splitext(chosen)[0]
        else:
            st.warning("`data/` 폴더에 영상 파일을 넣어주세요.")
    else:
        rtsp = st.text_input(
            "RTSP 주소",
            placeholder="rtsp://admin:1234@192.168.0.100:554/Streaming/Channels/402"
        )
        if rtsp.startswith("rtsp://"):
            selected_source = rtsp

    # ROI 저장 이름
    label_input = st.text_input(
        "ROI 저장 이름",
        value=st.session_state.roi_src_label or auto_label,
        help="모니터링 페이지에서 같은 이름의 소스를 선택하면 자동 로드됩니다."
    )
    st.session_state.roi_src_label = label_input

    st.markdown("---")

    # 기준 프레임 불러오기
    if st.button("📷 기준 프레임 불러오기", type="primary",
                 disabled=selected_source is None, use_container_width=True):
        with st.spinner("프레임 불러오는 중..."):
            vs    = VideoSource(selected_source)
            frame = vs.get_first_frame()
        if frame is not None:
            st.session_state.roi_frame  = frame
            st.session_state.roi_points = []   # 새 프레임이면 점 초기화
            st.session_state.last_click = None
            h, w = frame.shape[:2]
            st.success(f"✅ 완료 ({w}×{h})")
        else:
            st.error("❌ 프레임을 가져올 수 없습니다.")

    st.markdown("---")

    # 기존 ROI 불러오기
    st.subheader("📂 저장된 ROI")
    saved = list_saved_rois()
    if saved:
        sel = st.selectbox("불러올 ROI", ["— 선택 —"] + saved)
        if sel != "— 선택 —":
            pts = load_roi(sel)
            if pts is not None:
                st.success(f"{len(pts)}개 꼭짓점")
                for i, p in enumerate(pts):
                    st.caption(f"P{i+1}: ({p[0]}, {p[1]})")
    else:
        st.caption("저장된 ROI 없음")

    st.markdown("---")

    with st.expander("❓ 사용 방법"):
        st.markdown("""
        1. 영상 소스 선택 후 **📷 기준 프레임 불러오기**
        2. 오른쪽 영상을 **클릭**해서 꼭짓점을 추가
        3. 꼭짓점 3개 이상 → **💾 ROI 저장**
        4. 잘못 찍었으면 **↩️ 마지막 점 취소** 또는 **🗑️ 전체 초기화**
        """)


# ══════════════════════════════════════════════════════
# 메인 영역
# ══════════════════════════════════════════════════════
frame = st.session_state.roi_frame

if frame is None:
    st.info(
        "👈 왼쪽에서 영상 소스를 선택하고\n\n"
        "**📷 기준 프레임 불러오기** 버튼을 누르면 여기에 영상이 표시됩니다."
    )
    st.stop()

orig_h, orig_w = frame.shape[:2]
scale = DISPLAY_W / orig_w

# ── 상단 버튼 행 ─────────────────────────────────────
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

if c1.button("↩️ 마지막 점 취소", use_container_width=True):
    if st.session_state.roi_points:
        st.session_state.roi_points.pop()
        st.session_state.last_click = None
    st.rerun()

if c2.button("🗑️ 전체 초기화", use_container_width=True):
    st.session_state.roi_points = []
    st.session_state.last_click = None
    st.rerun()

save_clicked = c3.button("💾 ROI 저장", type="primary", use_container_width=True)

pts = st.session_state.roi_points
c4.markdown(
    f"**꼭짓점:** {len(pts)}개  |  "
    f"**저장 이름:** `{st.session_state.roi_src_label or '(미입력)'}`  |  "
    f"{'✅ 저장 가능' if len(pts) >= 3 else '⚠️ 3개 이상 클릭하세요'}"
)

# ── 프레임 렌더링 & 클릭 이벤트 ───────────────────────
pil_img = render_frame(frame, st.session_state.roi_points, scale)

st.markdown("##### ✏️ 영상을 클릭해서 ROI 꼭짓점을 추가하세요")
click = streamlit_image_coordinates(pil_img, key="roi_click")

# 새로운 클릭이 들어오면 꼭짓점 추가
if click is not None:
    # 같은 좌표 중복 방지
    new_coord = (click["x"], click["y"])
    if new_coord != st.session_state.last_click:
        st.session_state.last_click = new_coord
        # 표시 좌표 → 원본 좌표로 역변환
        orig_x = int(click["x"] / scale)
        orig_y = int(click["y"] / scale)
        st.session_state.roi_points.append([orig_x, orig_y])
        st.rerun()

# ── 꼭짓점 현황 표시 ──────────────────────────────────
if pts:
    st.markdown("**현재 꼭짓점 좌표 (원본 기준)**")
    cols = st.columns(min(len(pts), 6))
    for i, p in enumerate(pts):
        cols[i % 6].metric(f"P{i+1}", f"({p[0]}, {p[1]})")
else:
    st.caption("아직 찍은 꼭짓점이 없습니다. 위 영상을 클릭하세요.")

# ── 저장 처리 ────────────────────────────────────────
if save_clicked:
    label = st.session_state.roi_src_label
    if not label:
        st.error("❌ 사이드바에서 **ROI 저장 이름**을 입력하세요.")
    elif len(pts) < 3:
        st.error("❌ 꼭짓점이 3개 이상이어야 합니다. 영상을 더 클릭하세요.")
    else:
        path = save_roi(label, pts)
        st.success(
            f"✅ ROI 저장 완료!\n\n"
            f"- 이름: **{label}**\n"
            f"- 꼭짓점: {len(pts)}개\n"
            f"- 파일: `{path}`\n\n"
            f"모니터링 페이지에서 **{label}** 소스를 선택하면 자동으로 적용됩니다."
        )
