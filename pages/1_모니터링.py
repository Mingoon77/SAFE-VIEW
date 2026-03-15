# pages/1_모니터링.py — 실시간 위험 감지 메인 화면
#
# 동작 방식:
#   시작 버튼 → 프레임 1장 처리 → st.rerun() → 반복
#   정지 버튼 클릭 시 session_state.running = False → 루프 종료
#
# RTSP 안정화 처리:
#   - validate_rtsp_url(): 플레이스홀더/형식 오류 사전 차단
#   - test_rtsp_connection(): 연결 테스트 버튼으로 사전 확인 가능
#   - 프레임 읽기 실패 시 reconnect() 자동 호출 (최대 3회 시도)
#   - 재연결 성공 시 st.rerun()으로 스트리밍 즉시 재개

import streamlit as st
import cv2
import os
import sys
import time
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import (
    DATA_DIR, FRAME_SKIP, CLIP_BUFFER_SEC, MAX_CLIP_FPS
)
from core.detector     import Detector
from core.roi_manager  import load_roi
from core.video_source import VideoSource, validate_rtsp_url, test_rtsp_connection
from core.danger_logic import check_danger, draw_detections
from core.event_saver  import (
    save_event_image, save_event_clip,
    log_event, get_recent_events,
)

# ── 페이지 설정 ────────────────────────────────────────
st.set_page_config(
    page_title="모니터링 | 보행자 위험 감지",
    page_icon="🎥",
    layout="wide",
)

# ── session_state 초기화 ───────────────────────────────
def init_state():
    defaults = {
        "running":       False,
        "prev_danger":   False,
        "frame_idx":     0,
        "last_event_ts": 0.0,
        "fps_timer":     time.time(),
        "fps_count":     0,
        "fps_display":   0.0,
        "video_source":  None,
        "detector":      None,
        "frame_buffer":  deque(),
        "source_name":   "",
        "alert_msg":     "",
        "alert_expires": 0.0,
        "reconnect_msg": "",   # 재연결 상태 메시지
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── 헬퍼 함수 ─────────────────────────────────────────
def get_video_files() -> list:
    if not os.path.exists(DATA_DIR):
        return []
    return [
        f for f in os.listdir(DATA_DIR)
        if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
    ]

def update_fps():
    st.session_state.fps_count += 1
    elapsed = time.time() - st.session_state.fps_timer
    if elapsed >= 1.0:
        st.session_state.fps_display = round(
            st.session_state.fps_count / elapsed, 1
        )
        st.session_state.fps_count = 0
        st.session_state.fps_timer = time.time()

# ── 사이드바 ───────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    source_type = st.radio(
        "영상 소스 선택",
        ["📁 로컬 영상 파일", "📡 RTSP 스트림 (자택 CCTV)"],
        key="source_type",
        disabled=st.session_state.running,
    )

    selected_source = None
    source_label    = ""
    rtsp_ready      = False   # RTSP URL이 유효한지 여부

    # ── 로컬 파일 ────────────────────────────────────
    if source_type == "📁 로컬 영상 파일":
        video_files = get_video_files()
        if video_files:
            chosen = st.selectbox(
                "영상 파일 선택",
                video_files,
                disabled=st.session_state.running,
            )
            selected_source = os.path.join(DATA_DIR, chosen)
            source_label    = os.path.splitext(chosen)[0]
            rtsp_ready      = True
        else:
            st.warning(
                "⚠️ `data/` 폴더에 영상 파일이 없습니다.\n"
                "`.mp4` 파일을 넣어주세요."
            )

    # ── RTSP ─────────────────────────────────────────
    else:
        st.markdown("**RTSP 주소 입력**")
        st.caption(
            "형식: `rtsp://아이디:비밀번호@IP주소:554/경로`\n\n"
            "예: `rtsp://admin:1234@192.168.0.100:554/Streaming/Channels/402`"
        )

        rtsp_url = st.text_input(
            "RTSP 주소",
            value=st.session_state.get("rtsp_url_saved", ""),
            placeholder="rtsp://admin:1234@192.168.0.100:554/Streaming/Channels/402",
            disabled=st.session_state.running,
            label_visibility="collapsed",
        )
        # 입력값을 session_state에 저장 (페이지 리렌더링 시 유지)
        st.session_state["rtsp_url_saved"] = rtsp_url

        # 카메라 이름 (ROI 연결용)
        cam_name = st.text_input(
            "카메라 이름 (ROI 저장 이름과 동일하게)",
            value=st.session_state.get("rtsp_cam_name", "rtsp_stream"),
            disabled=st.session_state.running,
            help="ROI 설정 페이지에서 지정한 이름과 동일해야 ROI가 자동 로드됩니다.",
        )
        st.session_state["rtsp_cam_name"] = cam_name

        # URL 유효성 실시간 표시
        valid, err_msg = validate_rtsp_url(rtsp_url)
        if rtsp_url and not valid:
            st.error(f"⛔ {err_msg}")
        elif valid:
            st.success("✅ 주소 형식 OK")

        # 연결 테스트 버튼
        test_btn = st.button(
            "🔌 연결 테스트",
            disabled=not valid or st.session_state.running,
            help="실제로 연결해서 첫 프레임을 받아봅니다 (최대 5초 소요)",
        )
        if test_btn:
            with st.spinner("RTSP 연결 테스트 중... (최대 5초)"):
                ok, msg = test_rtsp_connection(rtsp_url)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

        if valid:
            selected_source = rtsp_url
            source_label    = cam_name
            rtsp_ready      = True

    st.markdown("---")

    # ── ROI 상태 ──────────────────────────────────────
    roi_polygon = load_roi(source_label) if source_label else None
    if roi_polygon is not None:
        st.success(f"✅ ROI 로드됨 ({len(roi_polygon)}개 꼭짓점)")
    else:
        st.warning(
            "⚠️ ROI 미설정\n\n"
            "ROI 없이도 실행되지만 위험 판단이 비활성화됩니다.\n"
            "**ROI 설정** 페이지에서 먼저 설정하세요."
        )

    st.markdown("---")

    # ── 신뢰도 슬라이더 ──────────────────────────────
    conf_threshold = st.slider(
        "탐지 신뢰도 임계값",
        min_value=0.1, max_value=0.9, value=0.4, step=0.05,
        disabled=st.session_state.running,
    )

    st.markdown("---")

    # ── 시작 / 정지 버튼 ─────────────────────────────
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        start_btn = st.button(
            "▶ 시작",
            use_container_width=True,
            disabled=st.session_state.running or not rtsp_ready,
            type="primary",
        )
    with btn_col2:
        stop_btn = st.button(
            "⏹ 정지",
            use_container_width=True,
            disabled=not st.session_state.running,
        )

    # ── 실행 중 상태 표시 ─────────────────────────────
    if st.session_state.running:
        st.metric("실시간 FPS",  f"{st.session_state.fps_display}")
        st.metric("처리 프레임", f"{st.session_state.frame_idx}")
        if st.session_state.reconnect_msg:
            st.warning(st.session_state.reconnect_msg)

# ── 시작 버튼 처리 ────────────────────────────────────
if start_btn and selected_source:

    # 1) 모델 로드 (처음 한 번만)
    if st.session_state.detector is None:
        with st.spinner("🔄 YOLOv8 모델 로딩 중... (첫 실행 시 자동 다운로드)"):
            st.session_state.detector = Detector()
        if not st.session_state.detector.loaded:
            st.error(
                f"❌ 모델 로드 실패: {st.session_state.detector.load_error}\n\n"
                "`pip install ultralytics` 를 실행하세요."
            )
            st.stop()

    # 2) RTSP면 URL 재검증
    if source_type == "📡 RTSP 스트림 (자택 CCTV)":
        valid, err_msg = validate_rtsp_url(selected_source)
        if not valid:
            st.error(f"❌ RTSP 주소 오류: {err_msg}")
            st.stop()

    # 3) VideoSource 열기
    vs = VideoSource(selected_source)
    with st.spinner(
        "📡 RTSP 연결 중..." if vs.is_rtsp else "📂 영상 파일 열기 중..."
    ):
        opened = vs.open()

    if not opened:
        if vs.is_rtsp:
            st.error(
                "❌ RTSP 연결 실패\n\n"
                "**체크리스트:**\n"
                "- DVR/NVR이 켜져 있는지 확인\n"
                "- 공인 IP와 포트(554) 포워딩 설정 확인\n"
                "- ID·비밀번호·채널 경로 재확인\n"
                "- 방화벽에서 TCP 554 포트 허용 확인\n\n"
                "위 **연결 테스트** 버튼으로 먼저 확인해보세요."
            )
        else:
            st.error("❌ 영상 파일을 열 수 없습니다. 경로를 확인하세요.")
        st.stop()

    # 4) 세션 상태 초기화 후 실행 시작
    buf_fps  = vs.get_fps()
    buf_size = int(buf_fps * CLIP_BUFFER_SEC * 2)

    st.session_state.update({
        "video_source":  vs,
        "source_name":   source_label,
        "frame_idx":     0,
        "prev_danger":   False,
        "frame_buffer":  deque(maxlen=max(buf_size, 20)),
        "fps_timer":     time.time(),
        "fps_count":     0,
        "fps_display":   0.0,
        "running":       True,
        "reconnect_msg": "",
    })
    st.rerun()

# ── 정지 버튼 처리 ────────────────────────────────────
if stop_btn:
    vs = st.session_state.video_source
    if vs:
        vs.release()
    st.session_state.update({
        "running":      False,
        "video_source": None,
        "reconnect_msg": "",
    })
    st.rerun()

# ── 메인 레이아웃 ──────────────────────────────────────
st.title("🎥 실시간 모니터링")

main_col, status_col = st.columns([3, 1])

with status_col:
    status_ph = st.empty()
    alert_ph  = st.empty()
    events_ph = st.empty()

with main_col:
    frame_ph  = st.empty()
    info_ph   = st.empty()

# ── 대기 화면 (실행 중 아닐 때) ───────────────────────
if not st.session_state.running:
    frame_ph.info(
        "▶ 왼쪽 사이드바에서 영상 소스를 선택하고 **시작** 버튼을 누르세요.\n\n"
        "RTSP 사용 시 **연결 테스트** 버튼으로 먼저 연결을 확인하세요."
    )
    status_ph.markdown("""
    <div style='background:#1e3a1e;padding:20px;border-radius:10px;text-align:center;'>
        <h2 style='color:#4caf50;margin:0'>🟢 대기 중</h2>
    </div>
    """, unsafe_allow_html=True)
    events_ph.markdown("### 📋 최근 이벤트")
    recent = get_recent_events(5)
    if recent:
        for ev in recent:
            events_ph.markdown(
                f"- `{ev['timestamp'][:19]}` — **{ev['status']}** — `{ev['source']}`"
            )
    else:
        events_ph.caption("이벤트 없음")
    st.stop()

# ── 프레임 처리 (실행 중) ──────────────────────────────
vs       = st.session_state.video_source
detector = st.session_state.detector

# VideoSource가 사라진 경우 (비정상 종료 등)
if vs is None or not vs.is_open():
    st.session_state.running = False
    st.warning("⚠️ 영상 소스 연결이 끊어졌습니다. 다시 시작하세요.")
    st.stop()

# 프레임 읽기
ret, frame = vs.read_frame()

# ── 프레임 읽기 실패 처리 ──────────────────────────────
if not ret:
    if vs.is_rtsp:
        # RTSP: 자동 재연결 시도
        st.session_state.reconnect_msg = "⚠️ 스트림 끊김 — 재연결 시도 중..."
        reconnected = vs.reconnect(max_attempts=3, wait_sec=2.0)
        if reconnected:
            st.session_state.reconnect_msg = "✅ 재연결 성공"
            st.rerun()
        else:
            st.session_state.running = False
            st.session_state.reconnect_msg = ""
            st.error(
                "❌ RTSP 재연결 실패 (3회 시도)\n\n"
                "DVR/카메라 상태와 네트워크를 확인 후 다시 시작하세요."
            )
            st.stop()
    else:
        # 파일: 처음으로 되감기
        vs.reset()
        ret, frame = vs.read_frame()
        if not ret:
            st.session_state.running = False
            st.error("❌ 영상 파일 읽기 실패.")
            st.stop()

# ── 프레임 분석 ────────────────────────────────────────
st.session_state.frame_idx += 1
frame_idx   = st.session_state.frame_idx
roi_polygon = load_roi(st.session_state.source_name)

# FRAME_SKIP마다 한 번 YOLO 실행 (성능 최적화)
if frame_idx % FRAME_SKIP == 0 or frame_idx == 1:
    detections = detector.detect(frame, conf=conf_threshold)
else:
    detections = []

danger_result = check_danger(detections, roi_polygon)
is_danger     = danger_result["is_danger"]

# ── 이벤트 감지 (정상 → 위험 전환) ───────────────────
event_triggered = False
now = time.time()

if is_danger and not st.session_state.prev_danger:
    if now - st.session_state.last_event_ts > 1.0:   # 1초 중복 방지
        event_triggered                    = True
        st.session_state.last_event_ts     = now
        st.session_state.alert_msg         = "🚨 위험! 보행자 감지"
        st.session_state.alert_expires     = now + 3.0

st.session_state.prev_danger = is_danger

# ── 프레임 시각화 ──────────────────────────────────────
annotated = frame.copy()
annotated = draw_detections(annotated, danger_result, roi_polygon)

if is_danger:
    cv2.putText(
        annotated, "DANGER - PEDESTRIAN DETECTED",
        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
        (0, 0, 220), 2, cv2.LINE_AA,
    )

# FPS + 프레임 번호 오버레이
update_fps()
cv2.putText(
    annotated,
    f"FPS:{st.session_state.fps_display}  F:{frame_idx}"
    + ("  [RTSP]" if vs.is_rtsp else "  [FILE]"),
    (10, annotated.shape[0] - 10),
    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA,
)

# ── 이벤트 저장 ────────────────────────────────────────
if event_triggered:
    img_name, _  = save_event_image(annotated, st.session_state.source_name)
    clip_name, _ = save_event_clip(
        st.session_state.frame_buffer,
        st.session_state.source_name,
        fps=MAX_CLIP_FPS,
    )
    log_event(st.session_state.source_name, img_name, clip_name)

# 클립 버퍼에 현재 프레임 추가
st.session_state.frame_buffer.append(annotated.copy())

# ── 화면 출력 ──────────────────────────────────────────
rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
frame_ph.image(rgb, channels="RGB", use_container_width=True)

persons = len(danger_result["all_persons"])
cars    = len(danger_result["all_cars"])
info_ph.caption(
    f"탐지: 사람 {persons}명 | 자동차 {cars}대 | "
    f"ROI {'설정됨' if roi_polygon is not None else '⚠️ 미설정'} | "
    f"소스: {st.session_state.source_name} | "
    f"{'📡 RTSP' if vs.is_rtsp else '📁 파일'}"
)

# ── 상태창 ─────────────────────────────────────────────
with status_col:
    if is_danger:
        status_ph.markdown("""
        <div style='background:#3a1e1e;padding:20px;border-radius:10px;
                    text-align:center;border:3px solid #dc3545;'>
            <h2 style='color:#ff4444;margin:0'>🔴 경고</h2>
            <p style='color:#ffaaaa;margin:4px 0 0 0'>보행자 위험 감지!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        status_ph.markdown("""
        <div style='background:#1e3a1e;padding:20px;border-radius:10px;
                    text-align:center;border:2px solid #28a745;'>
            <h2 style='color:#4caf50;margin:0'>🟢 정상</h2>
            <p style='color:#aaffaa;margin:4px 0 0 0'>위험 없음</p>
        </div>
        """, unsafe_allow_html=True)

    # 경고 배너 (이벤트 후 3초간)
    if now < st.session_state.alert_expires:
        alert_ph.error(st.session_state.alert_msg)
    else:
        alert_ph.empty()

    # 최근 이벤트 목록
    recent = get_recent_events(5)
    if recent:
        lines = "### 📋 최근 이벤트\n"
        for ev in recent:
            lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}**\n"
        events_ph.markdown(lines)

# 다음 프레임으로
if st.session_state.running:
    time.sleep(0.01)
    st.rerun()
