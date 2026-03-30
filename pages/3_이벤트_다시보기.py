# pages/3_이벤트_다시보기.py — 이벤트 캘린더 조회 및 미리보기

import streamlit as st
import cv2
import os
import sys
import csv
import calendar
import subprocess
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import EVENTS_DIR, LOG_FILE

# ── 페이지 설정 ────────────────────────────────────────
# st.set_page_config는 app.py에서 1회만 호출 (여기서는 제거)

st.title("📋 이벤트 다시보기")
st.markdown("캘린더에서 날짜를 선택하면 해당 날짜에 기록된 위험 이벤트를 확인할 수 있습니다.")
st.markdown("---")


# ══════════════════════════════════════════════════════
# 데이터 로딩
# ══════════════════════════════════════════════════════
def load_all_events():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def get_events_by_date(events, target):
    s = target.strftime("%Y-%m-%d")
    return [ev for ev in events if ev.get("timestamp", "").startswith(s)]

def get_dates_with_events(events):
    dates = set()
    for ev in events:
        ts = ev.get("timestamp", "")
        if len(ts) >= 10:
            try:
                dates.add(datetime.strptime(ts[:10], "%Y-%m-%d").date())
            except ValueError:
                pass
    return dates


# ── 영상 변환: mp4v → H.264 (브라우저 재생 가능) ──────
CONVERTED_DIR = os.path.join(EVENTS_DIR, "_converted")
os.makedirs(CONVERTED_DIR, exist_ok=True)

def get_playable_video(clip_path: str) -> str | None:
    """
    브라우저에서 재생 가능한 H.264 영상 경로를 반환합니다.
    이미 변환된 파일이 있으면 캐시된 파일을 반환합니다.
    """
    filename = os.path.basename(clip_path)
    converted_path = os.path.join(CONVERTED_DIR, filename)

    # 이미 변환된 파일이 있으면 바로 반환
    if os.path.exists(converted_path):
        return converted_path

    # ffmpeg로 H.264 변환
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg = get_ffmpeg_exe()
    except ImportError:
        return None

    try:
        result = subprocess.run(
            [
                ffmpeg, "-y",
                "-i", clip_path,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-movflags", "+faststart",   # 웹 스트리밍 최적화
                "-an",                        # 오디오 없음 (CCTV)
                converted_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode == 0 and os.path.exists(converted_path):
            return converted_path
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════
# 전체 이벤트 로드
# ══════════════════════════════════════════════════════
all_events = load_all_events()
event_dates = get_dates_with_events(all_events)

if not all_events:
    st.info("📭 저장된 이벤트가 없습니다.\n\n모니터링에서 위험 감지가 발생하면 여기에 기록됩니다.")
    st.stop()

st.success(f"총 **{len(all_events)}건**의 이벤트가 기록되어 있습니다.")


# ══════════════════════════════════════════════════════
# session_state 초기화
# ══════════════════════════════════════════════════════
if "sel_date" not in st.session_state:
    st.session_state.sel_date = date.today()


# ══════════════════════════════════════════════════════
# 사이드바: 날짜 선택
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.header("📅 날짜 선택")

    new_date = st.date_input(
        "날짜 선택",
        value=st.session_state.sel_date,
    )
    if new_date != st.session_state.sel_date:
        st.session_state.sel_date = new_date
        st.rerun()

    st.markdown("---")
    st.subheader("📊 통계")
    st.metric("전체 이벤트", f"{len(all_events)}건")
    st.metric("기록된 날짜 수", f"{len(event_dates)}일")


# ══════════════════════════════════════════════════════
# 캘린더 그리드
# ══════════════════════════════════════════════════════
sel = st.session_state.sel_date
st.subheader(f"📅 {sel.year}년 {sel.month}월")

cal_obj = calendar.Calendar(firstweekday=6)
weeks = cal_obj.monthdayscalendar(sel.year, sel.month)

day_names = ["일", "월", "화", "수", "목", "금", "토"]
hcols = st.columns(7)
for i, name in enumerate(day_names):
    color = "#ff6b6b" if i == 0 else ("#6ba3ff" if i == 6 else "#ffffff")
    hcols[i].markdown(
        f"<div style='text-align:center;font-weight:bold;color:{color}'>{name}</div>",
        unsafe_allow_html=True,
    )

for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].markdown("")
            continue
        d = date(sel.year, sel.month, day)
        has = d in event_dates
        is_sel = d == sel
        label = f"🔴 {day}" if has else f"{day}"

        if cols[i].button(
            label,
            key=f"c_{sel.year}_{sel.month}_{day}",
            use_container_width=True,
            type="primary" if is_sel else "secondary",
        ):
            st.session_state.sel_date = d
            st.rerun()

st.caption("🔴 = 이벤트 있음  |  강조 = 선택된 날짜")


# ══════════════════════════════════════════════════════
# 이벤트 목록
# ══════════════════════════════════════════════════════
st.markdown("---")
st.subheader(f"📂 {sel.strftime('%Y년 %m월 %d일')} 이벤트")

day_events = get_events_by_date(all_events, sel)

if not day_events:
    st.info(f"{sel.strftime('%Y-%m-%d')}에 기록된 이벤트가 없습니다.")
    st.stop()

st.markdown(f"**{len(day_events)}건**의 이벤트")

for idx, ev in enumerate(day_events):
    timestamp = ev.get("timestamp", "")
    source    = ev.get("source", "")
    status    = ev.get("status", "")
    img_file  = ev.get("image_file", "")
    clip_file = ev.get("clip_file", "")
    time_str  = timestamp[11:19] if len(timestamp) >= 19 else timestamp

    # ── 썸네일 + 정보 한 줄 ──────────────────────────
    thumb_col, info_col = st.columns([1, 3])

    with thumb_col:
        img_path = os.path.join(EVENTS_DIR, img_file) if img_file else ""
        has_img = img_file and os.path.exists(img_path)
        if has_img:
            st.image(img_path, width=200)

    with info_col:
        st.markdown(f"**⏱ {time_str}** — 🔴 {status} — 소스: `{source}`")
        if clip_file:
            cp = os.path.join(EVENTS_DIR, clip_file)
            if os.path.exists(cp):
                size_mb = os.path.getsize(cp) / (1024 * 1024)
                st.caption(f"🎬 클립 {size_mb:.1f} MB")

    # ── 상세 보기 (expander) ─────────────────────────
    with st.expander(f"🔍 상세 보기 — {time_str}", expanded=False):
        tab_img, tab_clip, tab_info = st.tabs(["📷 사진", "🎬 영상 클립", "ℹ️ 정보"])

        with tab_img:
            if has_img:
                st.image(img_path, caption=img_file, use_container_width=True)
            else:
                st.caption("이미지 없음")

        with tab_clip:
            if clip_file:
                clip_path = os.path.join(EVENTS_DIR, clip_file)
                if os.path.exists(clip_path):
                    # H.264로 변환하여 브라우저에서 바로 재생
                    with st.spinner("영상 준비 중..."):
                        playable = get_playable_video(clip_path)

                    if playable:
                        with open(playable, "rb") as vf:
                            st.video(vf.read())
                        st.caption("💡 우클릭 → 재생 속도에서 1.5x~2x 설정 가능")
                    else:
                        st.warning(
                            "브라우저 재생을 위한 변환에 실패했습니다.\n"
                            "아래 버튼으로 다운로드 후 VLC 등으로 재생하세요."
                        )
                        with open(clip_path, "rb") as vf:
                            st.download_button(
                                "💾 원본 다운로드",
                                data=vf,
                                file_name=clip_file,
                                mime="video/mp4",
                                key=f"dl_{idx}",
                            )
                else:
                    st.warning(f"파일 없음: {clip_file}")
            else:
                st.caption("영상 클립 없음")

        with tab_info:
            st.markdown(f"""
| 항목 | 내용 |
|------|------|
| **시간** | {timestamp} |
| **소스** | {source} |
| **상태** | {status} |
| **이미지** | `{img_file or '없음'}` |
| **클립** | `{clip_file or '없음'}` |
            """)

    st.markdown("---")


# ══════════════════════════════════════════════════════
# 파일 관리
# ══════════════════════════════════════════════════════
with st.expander("🗂️ 파일 관리", expanded=False):
    st.code(f"이벤트: {EVENTS_DIR}")
    st.code(f"로그: {LOG_FILE}")
    if os.path.exists(EVENTS_DIR):
        files = [f for f in os.listdir(EVENTS_DIR) if not f.startswith("_")]
        total = sum(
            os.path.getsize(os.path.join(EVENTS_DIR, f))
            for f in files if os.path.isfile(os.path.join(EVENTS_DIR, f))
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("이미지", f"{len([f for f in files if f.endswith('.jpg')])}개")
        c2.metric("클립", f"{len([f for f in files if f.endswith('.mp4')])}개")
        c3.metric("용량", f"{total/(1024*1024):.1f} MB")
