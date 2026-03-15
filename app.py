# app.py — Streamlit 홈 화면 (프로젝트 소개)
# `streamlit run app.py` 로 실행합니다.

import streamlit as st
import os, sys

# 프로젝트 루트를 sys.path에 추가 (하위 모듈 임포트 용)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR

# ── Streamlit 페이지 설정 ───────────────────────────────
st.set_page_config(
    page_title="보행자 위험 감지 시스템",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 필요한 폴더를 앱 시작 시 자동 생성
for d in [EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ── 메인 화면 ──────────────────────────────────────────
st.title("🚨 주차 차량 사각지대 기반 보행자 위험 감지 시스템")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ### 프로젝트 개요

    생활도로·골목·도로변 주차 구간에서 **주차 차량·담장·구조물**로 인해 시야가 제한되는 환경을 대상으로,
    CCTV 또는 저장 영상에서 **사람과 차량을 실시간 인식**하고
    사용자가 지정한 **ROI(관심구역) 내 위험 상황**을 감지하여
    화면 경고와 이벤트 저장을 제공하는 1차 프로토타입입니다.

    ---
    ### 사용 방법

    1. **👈 왼쪽 사이드바**에서 페이지를 선택하세요.
    2. **🗺️ ROI 설정** 페이지에서 관심구역을 먼저 설정하세요.
    3. **🎥 모니터링** 페이지에서 영상을 선택하고 감지를 시작하세요.

    ---
    ### 위험 판단 규칙

    | 조건 | 상태 |
    |------|------|
    | 아무것도 없음 | 🟢 정상 |
    | 사람만 있음 | 🟢 정상 |
    | 자동차만 있음 | 🟢 정상 |
    | 사람 + 자동차, 사람이 ROI 밖 | 🟢 정상 |
    | **사람 + 자동차, 사람이 ROI 안** | 🔴 **위험** |
    """)

with col2:
    st.markdown("### 시스템 상태")

    # 저장된 ROI 수
    roi_count = len([f for f in os.listdir(ROI_DIR) if f.endswith(".json")]) if os.path.exists(ROI_DIR) else 0
    st.metric("저장된 ROI", f"{roi_count}개")

    # 저장된 이벤트 수
    event_count = len([f for f in os.listdir(EVENTS_DIR) if f.endswith(".jpg")]) if os.path.exists(EVENTS_DIR) else 0
    st.metric("저장된 이벤트 이미지", f"{event_count}개")

    # 샘플 영상 수
    data_count = len([f for f in os.listdir(DATA_DIR) if f.endswith((".mp4", ".avi", ".mov"))]) if os.path.exists(DATA_DIR) else 0
    st.metric("샘플 영상 파일", f"{data_count}개")

    st.markdown("---")
    st.markdown("""
    **기술 스택**
    - 🐍 Python + Streamlit
    - 👁️ YOLOv8 (Ultralytics)
    - 📹 OpenCV
    """)

st.markdown("---")
st.info("💡 **시작 전 확인:** `data/` 폴더에 테스트용 영상 파일(.mp4)을 넣어두세요. YOLOv8 모델은 처음 실행 시 자동으로 다운로드됩니다.")
