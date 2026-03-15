# pages/2_ROI_설정.py — ROI(관심구역) 설정 화면
#
# 사용 흐름:
#   1. 영상 소스 선택 → 첫 프레임 미리보기
#   2. 다각형 꼭짓점 좌표를 텍스트로 입력 (또는 예시 ROI 선택)
#   3. 미리보기에서 ROI 확인
#   4. 저장 버튼 클릭 → roi_configs/<소스명>.json 저장

import streamlit as st
import cv2
import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import DATA_DIR
from core.video_source import VideoSource
from core.roi_manager  import (
    save_roi, load_roi, parse_roi_text,
    draw_roi_on_frame, list_saved_rois
)

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="ROI 설정 | 보행자 위험 감지",
    page_icon="🗺️",
    layout="wide",
)

st.title("🗺️ ROI(관심구역) 설정")
st.markdown("""
ROI(Region of Interest)는 보행자 위험을 감지할 **위험 구역**입니다.
사람의 발 위치가 이 구역 안에 들어오면 위험 상태로 판단합니다.
""")
st.markdown("---")

# ── 헬퍼 ──────────────────────────────────────────────
def get_video_files() -> list[str]:
    if not os.path.exists(DATA_DIR):
        return []
    return [
        f for f in os.listdir(DATA_DIR)
        if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    ]

def get_frame_from_source(source_path: str):
    """소스에서 첫 프레임을 가져옵니다."""
    vs = VideoSource(source_path)
    frame = vs.get_first_frame()
    return frame

# ── 예시 ROI 정의 (화면 크기별 상대 좌표로 자동 계산) ─
def make_preset_roi(w: int, h: int, preset: str) -> list:
    """
    영상 해상도에 맞춰 예시 ROI 좌표를 생성합니다.
    """
    presets = {
        "화면 중앙 사각형 (기본)": [
            [int(w * 0.25), int(h * 0.30)],
            [int(w * 0.75), int(h * 0.30)],
            [int(w * 0.75), int(h * 0.90)],
            [int(w * 0.25), int(h * 0.90)],
        ],
        "하단 횡단보도 영역": [
            [int(w * 0.10), int(h * 0.55)],
            [int(w * 0.90), int(h * 0.55)],
            [int(w * 0.90), int(h * 0.95)],
            [int(w * 0.10), int(h * 0.95)],
        ],
        "좌측 골목 입구 삼각형": [
            [int(w * 0.05), int(h * 0.20)],
            [int(w * 0.40), int(h * 0.20)],
            [int(w * 0.20), int(h * 0.90)],
        ],
        "우측 골목 입구 삼각형": [
            [int(w * 0.60), int(h * 0.20)],
            [int(w * 0.95), int(h * 0.20)],
            [int(w * 0.80), int(h * 0.90)],
        ],
        "전체 하단 절반": [
            [0,            int(h * 0.50)],
            [w - 1,        int(h * 0.50)],
            [w - 1,        h - 1],
            [0,            h - 1],
        ],
    }
    return presets.get(preset, presets["화면 중앙 사각형 (기본)"])

# ── 레이아웃 ───────────────────────────────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("① 영상 소스 선택")

    source_type = st.radio(
        "소스 유형",
        ["📁 로컬 영상 파일", "📡 RTSP 스트림"],
        key="roi_source_type",
    )

    selected_source = None
    source_label    = ""

    if source_type == "📁 로컬 영상 파일":
        video_files = get_video_files()
        if video_files:
            chosen = st.selectbox("파일 선택", video_files)
            selected_source = os.path.join(DATA_DIR, chosen)
            source_label    = os.path.splitext(chosen)[0]
        else:
            st.warning("`data/` 폴더에 영상 파일이 없습니다.")
    else:
        rtsp_input = st.text_input(
            "RTSP 주소",
            value="rtsp://[ID]:[PW]@[IP]:554/Streaming/Channels/402",
        )
        if rtsp_input.startswith("rtsp://"):
            selected_source = rtsp_input
            source_label    = "rtsp_stream"

    # 커스텀 소스 이름 (저장 키로 사용)
    source_label = st.text_input(
        "ROI 저장 이름 (영문/숫자)",
        value=source_label,
        help="이 이름으로 ROI가 저장됩니다. 모니터링 페이지에서 같은 이름을 선택해야 ROI가 로드됩니다.",
    )

    # 첫 프레임 가져오기 버튼
    load_btn = st.button("📷 기준 프레임 불러오기", type="primary",
                         disabled=selected_source is None)

    if load_btn:
        with st.spinner("프레임 로딩 중..."):
            frame = get_frame_from_source(selected_source)
        if frame is not None:
            st.session_state["roi_frame"] = frame
            st.session_state["roi_h"], st.session_state["roi_w"] = frame.shape[:2]
            st.success(f"프레임 로드 완료 ({st.session_state['roi_w']}×{st.session_state['roi_h']})")
        else:
            st.error("❌ 프레임을 가져올 수 없습니다. 소스를 확인하세요.")

    st.markdown("---")
    st.subheader("② ROI 좌표 입력")

    # 예시 ROI 사용 옵션
    use_preset = st.checkbox("예시 ROI 사용", value=True)

    if use_preset:
        preset_name = st.selectbox(
            "예시 ROI 선택",
            [
                "화면 중앙 사각형 (기본)",
                "하단 횡단보도 영역",
                "좌측 골목 입구 삼각형",
                "우측 골목 입구 삼각형",
                "전체 하단 절반",
            ],
        )
        if "roi_w" in st.session_state:
            preset_pts = make_preset_roi(
                st.session_state["roi_w"],
                st.session_state["roi_h"],
                preset_name,
            )
            # 텍스트 박스에 자동으로 좌표 채우기
            auto_text = "\n".join(f"{p[0]},{p[1]}" for p in preset_pts)
        else:
            auto_text = "먼저 기준 프레임을 불러오세요."
    else:
        auto_text = st.session_state.get("roi_coord_text", "")

    roi_text = st.text_area(
        "꼭짓점 좌표 (한 줄에 x,y 형식으로 입력, 최소 3점)",
        value=auto_text,
        height=160,
        help="예시:\n100,200\n500,200\n500,450\n100,450",
        key="roi_coord_text_area",
    )

    # 기존 저장된 ROI 불러오기
    st.markdown("---")
    st.subheader("③ 기존 ROI 불러오기")
    saved_list = list_saved_rois()
    if saved_list:
        load_existing = st.selectbox("저장된 ROI 목록", ["선택 안 함"] + saved_list)
        if load_existing != "선택 안 함":
            existing_pts = load_roi(load_existing)
            if existing_pts is not None:
                loaded_text = "\n".join(f"{p[0]},{p[1]}" for p in existing_pts)
                st.code(loaded_text, language=None)
                st.info(f"'{load_existing}' ROI: {len(existing_pts)}개 꼭짓점")
    else:
        st.caption("저장된 ROI 없음")

    # 저장 버튼
    st.markdown("---")
    save_btn = st.button("💾 ROI 저장", type="primary",
                         disabled=(not source_label or not roi_text.strip()))

    if save_btn:
        if not source_label:
            st.error("ROI 저장 이름을 입력하세요.")
        else:
            pts = parse_roi_text(roi_text)
            if pts is None:
                st.error("좌표 형식 오류. 각 줄에 `x,y` 형식으로 입력하세요. 최소 3점 필요.")
            else:
                path = save_roi(source_label, pts.tolist())
                st.success(f"✅ ROI 저장 완료: `{path}`")
                st.session_state["roi_saved_pts"] = pts

# ── 오른쪽: 프레임 미리보기 ────────────────────────────
with right_col:
    st.subheader("④ ROI 미리보기")

    frame = st.session_state.get("roi_frame", None)

    if frame is None:
        st.info("왼쪽에서 **기준 프레임 불러오기**를 클릭하면 영상 첫 프레임이 여기에 표시됩니다.")
    else:
        # 현재 텍스트 영역의 좌표로 ROI 그리기
        preview_frame = frame.copy()
        current_pts   = parse_roi_text(roi_text)

        # 저장된 ROI가 있으면 함께 표시
        if current_pts is not None:
            preview_frame = draw_roi_on_frame(preview_frame, current_pts, danger=False)

            # 꼭짓점 번호와 좌표 표시
            for i, pt in enumerate(current_pts):
                label = f"P{i+1}({int(pt[0])},{int(pt[1])})"
                cv2.putText(preview_frame, label,
                            (int(pt[0]) + 6, int(pt[1]) - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 255), 1, cv2.LINE_AA)
        else:
            cv2.putText(preview_frame, "ROI 미설정",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (100, 100, 100), 2, cv2.LINE_AA)

        # 프레임 크기 정보 오버레이
        h, w = frame.shape[:2]
        cv2.putText(preview_frame, f"{w}x{h}",
                    (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (200, 200, 200), 1, cv2.LINE_AA)

        # BGR → RGB 변환
        rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
        st.image(rgb, caption="ROI 미리보기 (노란선=ROI 경계)", use_container_width=True)

        # 현재 좌표 정보
        if current_pts is not None:
            st.success(f"현재 ROI: {len(current_pts)}개 꼭짓점")
            pts_df_data = {
                "꼭짓점": [f"P{i+1}" for i in range(len(current_pts))],
                "X": [int(p[0]) for p in current_pts],
                "Y": [int(p[1]) for p in current_pts],
            }
            import pandas as pd
            st.dataframe(pd.DataFrame(pts_df_data), use_container_width=True)
        else:
            if roi_text.strip():
                st.error("좌표 형식이 잘못되었습니다. 각 줄에 `x,y` 형식으로 입력하세요.")

    # ── 좌표 입력 가이드 ─────────────────────────────
    with st.expander("📖 좌표 입력 방법 안내"):
        st.markdown("""
        ### 좌표 입력 규칙

        - 각 줄에 꼭짓점 하나를 `X,Y` 형식으로 입력합니다.
        - 최소 **3개** 꼭짓점이 필요합니다.
        - 좌표는 영상의 픽셀 위치입니다.
          - 좌상단이 (0, 0)
          - 우하단이 (영상너비-1, 영상높이-1)

        ### 예시 (640×480 영상 기준)

        ```
        160,144
        480,144
        480,432
        160,432
        ```

        ### 좌표 확인 방법

        1. **기준 프레임 불러오기**로 첫 프레임을 표시합니다.
        2. **예시 ROI**를 선택해서 대략적인 위치를 잡습니다.
        3. 수치를 직접 수정하여 정확한 구역을 지정합니다.
        4. 미리보기로 확인 후 **ROI 저장** 버튼을 누릅니다.

        > 💡 영상에 마우스를 올리면 픽셀 좌표가 표시되지 않아 불편할 수 있습니다.
        > 예시 ROI를 기반으로 조금씩 조정하는 방법을 권장합니다.
        """)
