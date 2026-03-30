# app.py — Streamlit 앱 진입점
# `streamlit run app.py` 로 실행합니다.

import streamlit as st
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR

# ── 페이지 설정 (앱 전체에서 1번만) ──────────────────────
st.set_page_config(
    page_title="보행자 위험 감지 시스템",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 필요한 폴더 자동 생성
for d in [EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ── 사이드바 네비게이션 (페이지 이름 직접 지정) ─────────────
pg = st.navigation([
    st.Page("pages/0_대시보드.py",          title="대시보드",         icon="🏠"),
    st.Page("pages/1_모니터링.py",          title="모니터링",         icon="🎥"),
    st.Page("pages/2_ROI_설정.py",          title="ROI 설정",        icon="🗺️"),
    st.Page("pages/3_이벤트_다시보기.py",    title="이벤트 다시보기",   icon="📋"),
])

pg.run()
