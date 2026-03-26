# pages/1_모니터링.py — 실시간 위험 감지 메인 화면
#
# ★ 깜빡임 해결 구조 ★
#   RTSP : 백그라운드 스레드가 프레임을 계속 읽음
#           → 메인 루프는 스레드에서 꺼내기만 해서 네트워크 대기 없음
#   파일 : while 루프에서 직접 읽기 (이미 안정적)
#   공통 : last_good_frame 캐시 → 새 프레임 없어도 절대 빈 화면 안 됨

import streamlit as st
import cv2, os, sys, time, threading
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import DATA_DIR, FRAME_SKIP, CLIP_PRE_SEC, CLIP_POST_SEC, MAX_CLIP_FPS
from core.detector     import Detector
from core.roi_manager  import load_roi
from core.video_source import VideoSource, validate_rtsp_url, test_rtsp_connection
from core.danger_logic import check_danger, draw_detections
from core.event_saver  import (
    save_event_image, save_event_clip,
    log_event, get_recent_events,
)


# ══════════════════════════════════════════════════════
# RTSP 백그라운드 스레드 리더
# ══════════════════════════════════════════════════════
class RTSPThreadReader:
    """
    RTSP 프레임을 별도 스레드에서 지속적으로 읽어
    항상 최신 프레임을 메인 루프에 제공합니다.

    [왜 필요한가?]
    RTSP는 네트워크 상태에 따라 cap.read()가 수십 ms 동안 블로킹됩니다.
    메인 루프(UI 스레드)가 이걸 직접 호출하면 그 순간 화면이 멈추고
    frame_ph가 잠깐 비어 흰 깜빡임이 발생합니다.
    스레드 분리 후 메인 루프는 즉시 반환되는 get_latest_frame()만 호출하므로
    블로킹이 없어 깜빡임이 사라집니다.
    """

    def __init__(self, url: str):
        self._url           = url
        self._latest_frame  = None          # 가장 최신 프레임
        self._lock          = threading.Lock()
        self._stop_event    = threading.Event()
        self._thread        = threading.Thread(target=self._run, daemon=True)
        self._connected     = False
        self._error         = ""
        self._frame_count   = 0

    # ── 시작 ────────────────────────────────────────────
    def start(self) -> tuple[bool, str]:
        """
        스레드를 시작하고 첫 프레임이 올 때까지 최대 6초 대기.
        반환: (성공 여부, 오류 메시지)
        """
        self._thread.start()
        for _ in range(60):          # 0.1초 × 60 = 최대 6초 대기
            time.sleep(0.1)
            with self._lock:
                if self._latest_frame is not None:
                    return True, ""
            if self._error:
                return False, self._error
        return False, "타임아웃: 6초 내에 첫 프레임을 받지 못했습니다."

    # ── 스레드 본체 ──────────────────────────────────────
    def _run(self):
        vs = VideoSource(self._url)
        if not vs.open():
            self._error = (
                "RTSP 연결 실패 — IP/포트/채널 경로·포트포워딩·방화벽을 확인하세요."
            )
            return

        self._connected = True
        fail_streak = 0   # 연속 실패 횟수

        while not self._stop_event.is_set():
            ret, frame = vs.cap.read()   # cap.read() 직접 호출 (grab 중복 방지)

            if ret and frame is not None:
                fail_streak = 0
                with self._lock:
                    self._latest_frame = frame   # 최신 프레임으로 교체
                    self._frame_count += 1
            else:
                fail_streak += 1
                if fail_streak >= 20:            # 약 1초 연속 실패 → 재연결
                    vs.release()
                    time.sleep(2.0)
                    if vs.open():
                        fail_streak = 0
                    else:
                        self._error = "재연결 실패"
                        break
                time.sleep(0.05)                 # 실패 시 잠시 대기

        vs.release()
        self._connected = False

    # ── 최신 프레임 꺼내기 ───────────────────────────────
    def get_latest_frame(self):
        """메인 루프에서 호출. 즉시 반환 (블로킹 없음)."""
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def stop(self):
        self._stop_event.set()

    @property
    def is_alive(self) -> bool:
        return self._thread.is_alive()

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def error(self) -> str:
        return self._error


# ══════════════════════════════════════════════════════
# 페이지 설정 & session_state 초기화
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="모니터링 | 보행자 위험 감지",
    page_icon="🎥",
    layout="wide",
)

def init_state():
    defaults = {
        "running":        False,
        "prev_danger":    False,
        "frame_idx":      0,
        "last_event_ts":  0.0,
        "fps_timer":      time.time(),
        "fps_count":      0,
        "fps_display":    0.0,
        "video_source":   None,   # 파일용 VideoSource
        "rtsp_reader":    None,   # RTSP용 RTSPThreadReader
        "detector":       None,
        "frame_buffer":   deque(),
        "source_name":    "",
        "is_rtsp":        False,
        "alert_msg":      "",
        "alert_expires":  0.0,
        "last_good_frame": None,  # 깜빡임 방지용 마지막 정상 프레임
        "last_detections": [],    # 바운딩 박스 깜빡임 방지용 직전 탐지 결과
        "post_recording":  False, # 이벤트 후 녹화 중 여부
        "post_rec_start":  0.0,   # 후속 녹화 시작 시각
        "pre_frames":      [],    # 이벤트 전 5초 프레임 스냅샷
        "post_frames":     [],    # 이벤트 후 10초 프레임 수집
        "pending_img_name": "",   # 저장 대기 중인 이미지 파일명
        "rtsp_url_saved": "",
        "rtsp_cam_name":  "rtsp_stream",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════
# 헬퍼
# ══════════════════════════════════════════════════════
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

def stop_all():
    """영상 소스와 스레드를 모두 정리합니다."""
    if st.session_state.rtsp_reader:
        st.session_state.rtsp_reader.stop()
        st.session_state.rtsp_reader = None
    if st.session_state.video_source:
        st.session_state.video_source.release()
        st.session_state.video_source = None
    st.session_state.running        = False
    st.session_state.last_good_frame = None


# ══════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ 설정")

    source_type = st.radio(
        "영상 소스",
        ["📁 로컬 영상 파일", "📡 RTSP (자택 CCTV)"],
        disabled=st.session_state.running,
    )

    selected_source = None
    source_label    = ""
    source_ready    = False

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
            source_ready    = True
        else:
            st.warning("⚠️ `data/` 폴더에 `.mp4` 파일을 넣어주세요.")

    # ── RTSP ─────────────────────────────────────────
    else:
        st.caption(
            "형식: `rtsp://아이디:비밀번호@IP:554/경로`\n\n"
            "예시: `rtsp://admin:1234@192.168.0.100:554/Streaming/Channels/402`"
        )
        rtsp_url = st.text_input(
            "RTSP 주소",
            value=st.session_state.rtsp_url_saved,
            placeholder="rtsp://admin:1234@192.168.0.100:554/Streaming/Channels/402",
            disabled=st.session_state.running,
            label_visibility="collapsed",
        )
        st.session_state.rtsp_url_saved = rtsp_url

        cam_name = st.text_input(
            "카메라 이름 (ROI 저장 이름과 동일)",
            value=st.session_state.rtsp_cam_name,
            disabled=st.session_state.running,
            help="ROI 설정 페이지의 이름과 같아야 ROI가 자동 로드됩니다.",
        )
        st.session_state.rtsp_cam_name = cam_name

        valid, err = validate_rtsp_url(rtsp_url)
        if rtsp_url and not valid:
            st.error(f"⛔ {err}")
        elif valid:
            st.success("✅ 주소 형식 OK")

        if st.button("🔌 연결 테스트", disabled=not valid or st.session_state.running):
            with st.spinner("연결 테스트 중... (최대 5초)"):
                ok, msg = test_rtsp_connection(rtsp_url)
            (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {msg}")

        if valid:
            selected_source = rtsp_url
            source_label    = cam_name
            source_ready    = True

    st.markdown("---")

    # ── ROI 상태 ──────────────────────────────────────
    roi_polygon = load_roi(source_label) if source_label else None
    if roi_polygon is not None:
        st.success(f"✅ ROI 로드됨 ({len(roi_polygon)}개 꼭짓점)")
    else:
        st.warning("⚠️ ROI 미설정 — 위험 판단 비활성화\n\nROI 설정 페이지에서 먼저 설정하세요.")

    st.markdown("---")

    conf_threshold = st.slider(
        "탐지 신뢰도",
        0.1, 0.9, 0.4, 0.05,
        disabled=st.session_state.running,
    )

    st.markdown("---")

    # ── 원격 공유 모드 (ngrok 등) ─────────────────────
    remote_mode = st.checkbox(
        "📡 원격 공유 모드 (ngrok)",
        value=st.session_state.get("remote_mode", False),
        help="ngrok 등으로 외부 공유 시 체크하세요. 프레임 크기와 전송 속도를 줄여 안정적으로 스트리밍합니다.",
    )
    st.session_state.remote_mode = remote_mode
    if remote_mode:
        st.caption("해상도 축소 + 5 FPS 제한 적용 중")

    st.markdown("---")

    # ── 시작 / 정지 ───────────────────────────────────
    c1, c2 = st.columns(2)
    start_btn = c1.button(
        "▶ 시작",
        use_container_width=True,
        disabled=st.session_state.running or not source_ready,
        type="primary",
    )
    stop_btn  = c2.button(
        "⏹ 정지",
        use_container_width=True,
        disabled=not st.session_state.running,
    )

    if st.session_state.running:
        st.metric("FPS",  st.session_state.fps_display)
        st.metric("프레임", st.session_state.frame_idx)


# ══════════════════════════════════════════════════════
# 시작 처리
# ══════════════════════════════════════════════════════
if start_btn and selected_source:

    # 1) 모델 로드 (최초 1회)
    if st.session_state.detector is None:
        with st.spinner("🔄 YOLOv8 모델 로딩 중... (첫 실행 시 자동 다운로드, 1~2분 소요)"):
            st.session_state.detector = Detector()
        if not st.session_state.detector.loaded:
            st.error(f"❌ 모델 로드 실패: {st.session_state.detector.load_error}\n\n`pip install ultralytics` 실행 후 재시도하세요.")
            st.stop()

    is_rtsp = source_type == "📡 RTSP (자택 CCTV)"
    buf_size = max(int(25 * CLIP_PRE_SEC), 30)  # 이벤트 전 5초 버퍼

    if is_rtsp:
        # RTSP: 백그라운드 스레드 방식
        valid, err = validate_rtsp_url(selected_source)
        if not valid:
            st.error(f"❌ {err}")
            st.stop()

        with st.spinner("📡 RTSP 연결 중... (최대 6초)"):
            reader = RTSPThreadReader(selected_source)
            ok, err_msg = reader.start()

        if not ok:
            st.error(
                f"❌ RTSP 연결 실패: {err_msg}\n\n"
                "**체크리스트:**\n"
                "- DVR/NVR 전원 확인\n"
                "- 공인 IP·포트 포워딩(554) 확인\n"
                "- ID·비밀번호·채널 경로 확인\n"
                "- 방화벽 TCP 554 허용 확인\n\n"
                "사이드바 **연결 테스트** 버튼으로 먼저 확인하세요."
            )
            reader.stop()
            st.stop()

        st.session_state.rtsp_reader   = reader
        st.session_state.video_source  = None

    else:
        # 파일: 직접 VideoSource
        vs = VideoSource(selected_source)
        with st.spinner("📂 영상 파일 열기 중..."):
            opened = vs.open()
        if not opened:
            st.error("❌ 영상 파일을 열 수 없습니다. data/ 폴더 경로를 확인하세요.")
            st.stop()
        st.session_state.video_source = vs
        st.session_state.rtsp_reader  = None

    st.session_state.update({
        "is_rtsp":        is_rtsp,
        "source_name":    source_label,
        "frame_idx":      0,
        "prev_danger":    False,
        "frame_buffer":   deque(maxlen=buf_size),
        "fps_timer":      time.time(),
        "fps_count":      0,
        "fps_display":    0.0,
        "running":        True,
        "last_good_frame": None,
        "alert_msg":      "",
        "alert_expires":  0.0,
    })
    st.rerun()


# ══════════════════════════════════════════════════════
# 정지 처리
# ══════════════════════════════════════════════════════
if stop_btn:
    stop_all()
    st.rerun()


# ══════════════════════════════════════════════════════
# 메인 레이아웃 플레이스홀더
# ══════════════════════════════════════════════════════
st.title("🎥 실시간 모니터링")
main_col, status_col = st.columns([3, 1])

with main_col:
    frame_ph = st.empty()
    info_ph  = st.empty()

with status_col:
    status_ph = st.empty()
    alert_ph  = st.empty()
    events_ph = st.empty()


# ══════════════════════════════════════════════════════
# 대기 화면
# ══════════════════════════════════════════════════════
if not st.session_state.running:
    frame_ph.info("▶ 왼쪽 사이드바에서 소스를 선택하고 **시작**을 누르세요.")
    status_ph.markdown("""
    <div style='background:#1e3a1e;padding:20px;border-radius:10px;text-align:center;'>
        <h2 style='color:#4caf50;margin:0'>🟢 대기 중</h2>
    </div>""", unsafe_allow_html=True)
    recent = get_recent_events(5)
    if recent:
        lines = "### 📋 최근 이벤트\n"
        for ev in recent:
            lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}** `{ev['source']}`\n"
        events_ph.markdown(lines)
    else:
        events_ph.caption("저장된 이벤트 없음")
    st.stop()


# ══════════════════════════════════════════════════════
# ★ 프레임 처리 루프 (실행 중)
# ★ while 루프 사용 → 페이지 새로고침 없음 → 깜빡임 없음
# ══════════════════════════════════════════════════════
is_rtsp      = st.session_state.is_rtsp
rtsp_reader  = st.session_state.rtsp_reader
vs           = st.session_state.video_source
detector     = st.session_state.detector

# 소스가 사라진 경우 안전하게 종료
if is_rtsp and (rtsp_reader is None or not rtsp_reader.is_alive):
    stop_all()
    st.warning("⚠️ RTSP 스레드가 종료됐습니다. 다시 시작하세요.")
    st.stop()

if not is_rtsp and (vs is None or not vs.is_open()):
    stop_all()
    st.warning("⚠️ 영상 소스 연결이 끊어졌습니다. 다시 시작하세요.")
    st.stop()

# ROI는 루프 밖에서 한 번만 로드 (매 프레임마다 파일 읽기 방지)
roi_polygon = load_roi(st.session_state.source_name)

while st.session_state.running:

    # ── 프레임 획득 ────────────────────────────────────
    if is_rtsp:
        # 스레드에서 최신 프레임 꺼내기 — 즉시 반환, 블로킹 없음
        frame = rtsp_reader.get_latest_frame()
        ret   = frame is not None
        if not ret and rtsp_reader.error:
            stop_all()
            st.error(f"❌ RTSP 오류: {rtsp_reader.error}")
            break
    else:
        ret, frame = vs.read_frame()
        if not ret:
            vs.reset()   # 파일 끝 → 처음으로 되감고 계속 재생
            continue

    # ── 새 프레임이 없을 때: 마지막 프레임 재사용 (빈 화면 방지) ──
    if not ret or frame is None:
        frame = st.session_state.last_good_frame
        if frame is None:
            time.sleep(0.02)
            continue
        is_new_frame = False
    else:
        st.session_state.last_good_frame = frame
        is_new_frame = True

    # ── 객체 탐지 (FRAME_SKIP마다 실행) ─────────────────
    st.session_state.frame_idx += 1
    frame_idx = st.session_state.frame_idx

    if is_new_frame and (frame_idx % FRAME_SKIP == 0 or frame_idx == 1):
        detections = detector.detect(frame, conf=conf_threshold)
        st.session_state.last_detections = detections   # 최신 결과 저장
    else:
        detections = st.session_state.last_detections    # 직전 결과 유지 (박스 깜빡임 방지)

    # ── 위험 판단 ──────────────────────────────────────
    danger_result = check_danger(detections, roi_polygon)
    is_danger     = danger_result["is_danger"]

    # ── 이벤트 감지 (정상 → 위험 전환 순간만) ─────────────
    now = time.time()
    event_triggered = False
    if is_danger and not st.session_state.prev_danger:
        if now - st.session_state.last_event_ts > 15.0:   # 15초 쿨다운 (후속 녹화 겹침 방지)
            event_triggered                = True
            st.session_state.last_event_ts = now
            st.session_state.alert_msg     = "🚨 위험! 보행자 감지"
            st.session_state.alert_expires = now + 3.0

    st.session_state.prev_danger = is_danger

    # ── 프레임 시각화 ──────────────────────────────────
    annotated = frame.copy()
    annotated = draw_detections(annotated, danger_result, roi_polygon)

    if is_danger:
        cv2.putText(
            annotated, "DANGER - PEDESTRIAN DETECTED",
            (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
            (0, 0, 220), 2, cv2.LINE_AA,
        )

    update_fps()
    src_tag = "[RTSP]" if is_rtsp else "[FILE]"
    cv2.putText(
        annotated,
        f"FPS:{st.session_state.fps_display}  F:{frame_idx}  {src_tag}",
        (10, annotated.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA,
    )

    # ── 이벤트 저장 (전 5초 + 후 10초) ─────────────────
    # 1단계: 이벤트 발생 → 이미지 즉시 저장 + 전 5초 프레임 스냅샷 + 후속 녹화 시작
    if event_triggered and not st.session_state.post_recording:
        img_name, _ = save_event_image(annotated, st.session_state.source_name)
        st.session_state.pending_img_name = img_name
        st.session_state.pre_frames       = list(st.session_state.frame_buffer)
        st.session_state.post_frames      = []
        st.session_state.post_recording   = True
        st.session_state.post_rec_start   = now

    # 2단계: 후속 녹화 중 → 프레임 수집 (10초간)
    if st.session_state.post_recording:
        st.session_state.post_frames.append(annotated.copy())

        # 10초 경과 → 전+후 프레임 합쳐서 클립 저장
        if now - st.session_state.post_rec_start >= CLIP_POST_SEC:
            all_clip_frames = st.session_state.pre_frames + st.session_state.post_frames
            clip_name, _ = save_event_clip(
                deque(all_clip_frames),
                st.session_state.source_name,
                fps=MAX_CLIP_FPS,
            )
            log_event(
                st.session_state.source_name,
                st.session_state.pending_img_name,
                clip_name,
            )
            # 후속 녹화 종료 & 정리
            st.session_state.post_recording = False
            st.session_state.pre_frames     = []
            st.session_state.post_frames    = []
            st.session_state.pending_img_name = ""

    # 프레임 버퍼에 현재 프레임 추가 (이벤트 전 5초 순환 버퍼)
    st.session_state.frame_buffer.append(annotated.copy())

    # ── 화면 출력 ─────────────────────────────────────
    # 원격 모드: 해상도 축소하여 전송 데이터량 대폭 감소
    display_frame = annotated
    if st.session_state.get("remote_mode", False):
        h_orig, w_orig = display_frame.shape[:2]
        max_w = 640
        if w_orig > max_w:
            ratio = max_w / w_orig
            display_frame = cv2.resize(
                display_frame, (max_w, int(h_orig * ratio)),
                interpolation=cv2.INTER_AREA,
            )

    # BGR → RGB 변환 후 표시
    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    frame_ph.image(rgb, channels="RGB", use_container_width=True)

    persons = len(danger_result["all_persons"])
    cars    = len(danger_result["all_cars"])
    info_ph.caption(
        f"사람 {persons}명 | 자동차 {cars}대 | "
        f"ROI {'✅' if roi_polygon is not None else '⚠️ 미설정'} | "
        f"{st.session_state.source_name}"
    )

    # ── 상태창 ────────────────────────────────────────
    if is_danger:
        status_ph.markdown("""
        <div style='background:#3a1e1e;padding:20px;border-radius:10px;
                    text-align:center;border:3px solid #dc3545;'>
            <h2 style='color:#ff4444;margin:0'>🔴 경고</h2>
            <p style='color:#ffaaaa;margin:4px 0 0'>보행자 위험 감지!</p>
        </div>""", unsafe_allow_html=True)
    else:
        status_ph.markdown("""
        <div style='background:#1e3a1e;padding:20px;border-radius:10px;
                    text-align:center;border:2px solid #28a745;'>
            <h2 style='color:#4caf50;margin:0'>🟢 정상</h2>
            <p style='color:#aaffaa;margin:4px 0 0'>위험 없음</p>
        </div>""", unsafe_allow_html=True)

    if now < st.session_state.alert_expires:
        alert_ph.error(st.session_state.alert_msg)
    else:
        alert_ph.empty()

    # 최근 이벤트 (이벤트 발생 시에만 갱신 — 매 프레임 갱신 불필요)
    if event_triggered:
        recent = get_recent_events(5)
        if recent:
            lines = "### 📋 최근 이벤트\n"
            for ev in recent:
                lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}**\n"
            events_ph.markdown(lines)

    # 원격 모드: 0.2초 간격(5FPS) → ngrok 대역폭 내에서 안정적 전송
    # 로컬 모드: RTSP 0.001초 / 파일 0.02초 → 최대 성능
    if st.session_state.get("remote_mode", False):
        time.sleep(0.2)
    else:
        time.sleep(0.001 if is_rtsp else 0.020)
