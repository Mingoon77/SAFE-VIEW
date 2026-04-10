# app.py — Streamlit 앱 진입점
# `streamlit run app.py` 로 실행합니다.

import streamlit as st
import os, sys, base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="SAFEVIEW — AI 기반 사각지대 위험 감지 시스템",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 필요한 폴더 자동 생성
for d in [EVENTS_DIR, LOGS_DIR, ROI_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ── 로고 이미지 base64 로드 ──────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

# ── 사이드바 로고 (CSS 가상 요소) + Streamlit 헤더 숨기기 ──
st.markdown(f"""
<style>
header[data-testid="stHeader"] {{
    display: none !important;
}}
.block-container {{
    padding-top: 0.5rem !important;
}}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* 사이드바 상단 로고 */
[data-testid="stSidebar"] > div:first-child::before {{
    content: "";
    display: block;
    width: 70px; height: 70px;
    margin: 18px auto 8px auto;
    background-image: url("data:image/png;base64,{LOGO_B64}");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
}}
[data-testid="stSidebar"] > div:first-child::after {{
    content: "SAFEVIEW";
    display: block;
    text-align: center;
    font-size: 1.1rem;
    font-weight: 800;
    color: #1a1a1a;
    padding-bottom: 14px;
    margin-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
}}

/* ── 버튼 글자 가운데 정렬 + 여백 제거 ────────────── */
[data-testid="stButton"] > button {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 38px !important;
    padding: 6px 16px !important;
    line-height: 1 !important;
}}
</style>
""", unsafe_allow_html=True)

# ── 최상단 배너 ──────────────────────────────────────────
st.markdown(f"""
<div style="background:#FFFFFF; border-bottom:2px solid #E2E8F0; padding:10px 24px;
            display:flex; align-items:center; gap:14px; margin:0 0 1.5rem 0; border-radius:8px;">
    <img src="data:image/png;base64,{LOGO_B64}" style="width:38px; height:38px; border-radius:6px;">
    <div>
        <span style="font-size:1.15rem; font-weight:800; color:#1a1a1a;">SAFE<span style="color:#4CAF50;">VIEW</span></span>
        <span style="color:#64748B; font-size:0.9rem; margin-left:4px;">AI 기반 사각지대 위험 감지 시스템</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 네비게이션 ───────────────────────────────────────────
pg = st.navigation([
    st.Page("pages/0_대시보드.py",          title="홈",             icon="🏠"),
    st.Page("pages/1_모니터링.py",          title="모니터링",        icon="🎥"),
    st.Page("pages/2_ROI_설정.py",          title="ROI 설정",       icon="🗺️"),
    st.Page("pages/3_이벤트_다시보기.py",    title="이벤트",          icon="📋"),
])

pg.run()
