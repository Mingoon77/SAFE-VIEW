# pages/1_모니터링.py — 실시간 위험 감지 메인 화면

import streamlit as st
import cv2, os, sys, time, threading
import numpy as np
from PIL import Image, ImageDraw, ImageFont
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
# 페이지 설정 & CSS 애니메이션
# ══════════════════════════════════════════════════════
# st.set_page_config는 app.py에서 1회만 호출

st.markdown("""
    <style>
    @keyframes pulse-danger {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }
        70% { box-shadow: 0 0 0 25px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    @keyframes flash-text {
        0%, 100% { opacity: 1; text-shadow: 0 0 20px #ef4444; }
        50% { opacity: 0.6; text-shadow: none; }
    }
    .status-box-danger {
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 100%);
        padding: 25px 20px; border-radius: 15px; text-align: center;
        border: 4px solid #ef4444; animation: pulse-danger 1s infinite;
    }
    .danger-title {
        color: #f87171; margin: 0; font-size: 2.2rem; font-weight: 900;
        animation: flash-text 1s infinite;
    }
    .danger-sub { color: #fca5a5; margin: 5px 0 0; font-size: 1.1rem; font-weight: bold; }
    
    .status-box-safe {
        background: linear-gradient(135deg, #022c22 0%, #064e3b 100%);
        padding: 25px 20px; border-radius: 15px; text-align: center;
        border: 2px solid #10b981;
    }
    /* 정상 글씨가 눈에 확 띄도록 밝은 초록색과 굵기 추가 */
    .safe-title { color: #4ade80 !important; margin: 0; font-size: 2.2rem; font-weight: 900; }
    .safe-sub { color: #a7f3d0 !important; margin: 5px 0 0; font-size: 1.1rem; font-weight: bold; }
    </style>
    <script>
    // 경고음 생성 (Web Audio API — 외부 파일 불필요)
    function playAlertSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            // 비프음 2회
            [0, 0.25].forEach(delay => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.frequency.value = 880;  // A5 음
                osc.type = 'square';
                gain.gain.value = 0.3;
                osc.start(ctx.currentTime + delay);
                osc.stop(ctx.currentTime + delay + 0.15);
            });
        } catch(e) {}
    }
    </script>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# 🎯 중앙 정렬 & 굵은 한글 출력 도우미 함수
# ══════════════════════════════════════════════════════
# 폰트 캐시 (매 프레임 디스크 로드 방지)
_font_cache = {}
def _get_font(size):
    if size not in _font_cache:
        try:
            _font_cache[size] = ImageFont.truetype("malgunbd.ttf", size)
        except:
            try:
                _font_cache[size] = ImageFont.truetype("malgun.ttf", size)
            except:
                _font_cache[size] = ImageFont.load_default()
    return _font_cache[size]

def draw_text_korean_centered(img, text, y_pos, font_size, color_bgr):
    """OpenCV 이미지의 가로 중앙에 한글을 굵고 선명하게 그리는 함수"""
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = _get_font(font_size)
            
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = (img_pil.width - text_width) // 2
    
    b, g, r = color_bgr
    
    draw.text((x_pos, y_pos), text, font=font, fill=(r, g, b), stroke_width=5, stroke_fill=(0, 0, 0))
    
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# ══════════════════════════════════════════════════════
# RTSP 백그라운드 스레드 리더
# ══════════════════════════════════════════════════════
class RTSPThreadReader:
    def __init__(self, url: str):
        self._url           = url
        self._latest_frame  = None
        self._lock          = threading.Lock()
        self._stop_event    = threading.Event()
        self._thread        = threading.Thread(target=self._run, daemon=True)
        self._connected     = False
        self._error         = ""
        self._frame_count   = 0

    def start(self) -> tuple[bool, str]:
        self._thread.start()
        for _ in range(60):
            time.sleep(0.1)
            with self._lock:
                if self._latest_frame is not None:
                    return True, ""
            if self._error:
                return False, self._error
        return False, "타임아웃: 6초 내에 첫 프레임을 받지 못했습니다."

    def _run(self):
        vs = VideoSource(self._url)
        if not vs.open():
            self._error = "RTSP 연결 실패 — IP/포트/채널 경로·포트포워딩·방화벽을 확인하세요."
            return

        self._connected = True
        fail_streak = 0

        while not self._stop_event.is_set():
            ret, frame = vs.cap.read()
            if ret and frame is not None:
                fail_streak = 0
                with self._lock:
                    self._latest_frame = frame
                    self._frame_count += 1
            else:
                fail_streak += 1
                if fail_streak >= 20:
                    vs.release()
                    time.sleep(2.0)
                    if vs.open(): fail_streak = 0
                    else:
                        self._error = "재연결 실패"
                        break
                time.sleep(0.05)

        vs.release()
        self._connected = False

    def get_latest_frame(self):
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def stop(self): self._stop_event.set()
    @property
    def is_alive(self) -> bool: return self._thread.is_alive()
    @property
    def error(self) -> str: return self._error


def init_state():
    defaults = {
        "running":        False,
        "prev_danger":    False,
        "frame_idx":      0,
        "last_event_ts":  0.0,
        "fps_timer":      time.time(),
        "fps_count":      0,
        "fps_display":    0.0,
        "video_source":   None,
        "rtsp_reader":    None,
        "detector":       None,
        "frame_buffer":   deque(),
        "source_name":    "",
        "is_rtsp":        False,
        "alert_msg":      "",
        "alert_expires":  0.0,
        "last_good_frame": None,
        "last_detections": [],
        "post_recording":  False,
        "post_rec_start":  0.0,
        "pre_frames":      [],
        "post_frames":     [],
        "pending_img_name": "",
        "rtsp_url_saved": "",
        "rtsp_cam_name":  "rtsp_stream",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def get_video_files() -> list:
    if not os.path.exists(DATA_DIR): return []
    return [f for f in os.listdir(DATA_DIR) if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))]

def update_fps():
    """1초 단위로 FPS 계산 및 session_state 갱신"""
    st.session_state.fps_count += 1
    elapsed = time.time() - st.session_state.fps_timer
    if elapsed >= 1.0:
        st.session_state.fps_display = round(st.session_state.fps_count / elapsed, 1)
        st.session_state.fps_count = 0
        st.session_state.fps_timer = time.time()

def stop_all():
    if st.session_state.rtsp_reader:
        st.session_state.rtsp_reader.stop()
        st.session_state.rtsp_reader = None
    if st.session_state.video_source:
        st.session_state.video_source.release()
        st.session_state.video_source = None
    st.session_state.running        = False
    st.session_state.last_good_frame = None


# ══════════════════════════════════════════════════════
# 메인 레이아웃: 설정(왼쪽) + 영상(가운데) + 상태(오른쪽)
# ══════════════════════════════════════════════════════
# 진행상황 메시지 표시 영역 (배너 바로 아래, 제목 위)
progress_ph = st.empty()

st.title("🎥 실시간 모니터링")

settings_col, main_col, status_col = st.columns([1, 2.5, 1])

# ── 왼쪽: 영상 소스 설정 ──────────────────────────────
with settings_col:
    st.markdown("### 영상 소스 설정")
    source_type = st.radio("소스", ["📁 파일", "📡 RTSP"], horizontal=True, disabled=st.session_state.running, label_visibility="collapsed")
    selected_source, source_label, source_ready = None, "", False

    if source_type == "📁 파일":
        video_files = get_video_files()
        if video_files:
            chosen = st.selectbox("영상 파일 선택", video_files, disabled=st.session_state.running)
            selected_source = os.path.join(DATA_DIR, chosen)
            source_label    = os.path.splitext(chosen)[0]
            source_ready    = True
        else:
            st.warning("data/ 폴더에 .mp4 파일을 넣어주세요.")
    else:
        rtsp_url = st.text_input("RTSP 주소", value=st.session_state.rtsp_url_saved, placeholder="rtsp://admin:1234@IP:554/...", disabled=st.session_state.running)
        st.session_state.rtsp_url_saved = rtsp_url

        cam_name = st.text_input("카메라 이름 (ROI 이름)", value=st.session_state.rtsp_cam_name, disabled=st.session_state.running)
        st.session_state.rtsp_cam_name = cam_name

        valid, err = validate_rtsp_url(rtsp_url)
        if rtsp_url and not valid: st.error(f"⛔ {err}")
        elif valid: st.success("✅ 주소 형식 OK")

        if st.button("🔌 연결 테스트", disabled=not valid or st.session_state.running):
            with st.spinner("연결 테스트 중..."):
                ok, msg = test_rtsp_connection(rtsp_url)
            (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {msg}")

        if valid:
            selected_source, source_label, source_ready = rtsp_url, cam_name, True

    st.markdown("---")

    # 시스템 상태
    st.markdown("### 시스템 상태")
    roi_polygon = load_roi(source_label) if source_label else None
    if roi_polygon is not None: st.success(f"✅ ROI 로드됨 ({len(roi_polygon)}개)")
    else: st.warning("⚠️ ROI 미설정 — 위험 판단 비활성화")

    if st.session_state.running:
        # placeholder로 만들어 while 루프에서 실시간 갱신
        fps_ph   = st.empty()
        frame_ph_count = st.empty()
        fps_ph.markdown(f"**FPS** &nbsp; {st.session_state.fps_display}")
        frame_ph_count.markdown(f"**프레임** &nbsp; {st.session_state.frame_idx}")
        st.session_state["__fps_ph"]   = fps_ph
        st.session_state["__frame_ph_count"] = frame_ph_count

    # 원격 공유 모드 자동 감지 (수동 체크박스 제거)
    # → Streamlit 헤더의 Host 정보로 localhost 여부 판별

    # 시작/정지 버튼
    start_btn = st.button("▶ 시작", use_container_width=True, disabled=st.session_state.running or not source_ready, type="primary")
    stop_btn  = st.button("⏹ 정지", use_container_width=True, disabled=not st.session_state.running)

    st.markdown("---")

    conf_threshold = st.slider("감지 신뢰도", 0.1, 0.9, 0.4, 0.05, disabled=st.session_state.running)

# ══════════════════════════════════════════════════════
# 시작/정지 처리
# ══════════════════════════════════════════════════════
if start_btn and selected_source:
    if st.session_state.detector is None:
        progress_ph.info("🔄 YOLOv8 모델 로딩 중... (첫 실행 시 다운로드가 있을 수 있습니다)")
        st.session_state.detector = Detector()
        if not st.session_state.detector.loaded:
            progress_ph.error(f"❌ 모델 로드 실패: {st.session_state.detector.load_error}")
            st.stop()

    is_rtsp = source_type == "📡 RTSP (자택 CCTV)"
    buf_size = max(int(25 * CLIP_PRE_SEC), 30)

    if is_rtsp:
        valid, err = validate_rtsp_url(selected_source)
        if not valid: progress_ph.error(f"❌ {err}"); st.stop()

        progress_ph.info("📡 RTSP 연결 중...")
        reader = RTSPThreadReader(selected_source)
        ok, err_msg = reader.start()

        if not ok:
            progress_ph.error(f"❌ RTSP 연결 실패: {err_msg}")
            reader.stop(); st.stop()

        st.session_state.rtsp_reader   = reader
        st.session_state.video_source  = None
    else:
        vs = VideoSource(selected_source)
        progress_ph.info("📂 영상 파일 열기 중...")
        opened = vs.open()
        if not opened: progress_ph.error("❌ 영상 파일을 열 수 없습니다."); st.stop()
        st.session_state.video_source = vs
        st.session_state.rtsp_reader  = None

    progress_ph.success("✅ 시작 준비 완료!")
    st.session_state.update({
        "is_rtsp":        is_rtsp,
        "source_name":    source_label,
        "frame_idx":      0,
        "prev_danger":    False,
        "frame_buffer":   deque(maxlen=buf_size),
        "running":        True,
        "last_good_frame": None,
        "alert_msg":      "",
        "alert_expires":  0.0,
    })
    st.rerun()

if stop_btn:
    stop_all()
    st.rerun()


# ══════════════════════════════════════════════════════
# 영상/상태 플레이스홀더 (위에서 만든 columns 사용)
# ══════════════════════════════════════════════════════
with main_col:
    frame_ph = st.empty()
    info_ph  = st.empty()

with status_col:
    status_ph = st.empty()
    alert_ph  = st.empty()
    events_ph = st.empty()


# ══════════════════════════════════════════════════════
# 대기 화면 (검은색 스크린 박스 적용)
# ══════════════════════════════════════════════════════
if not st.session_state.running:
    # 대기화면: PIL로 이미지 생성 (테마 무관, 외부 접속에서도 동일 표시)
    from PIL import Image as PILImage, ImageDraw as PILDraw, ImageFont as PILFont
    _wi = PILImage.new("RGB", (960, 540), (17, 24, 39))
    _wd = PILDraw.Draw(_wi)
    try:
        _f1 = PILFont.truetype("malgunbd.ttf", 28)
        _f2 = PILFont.truetype("malgun.ttf", 22)
    except:
        _f1 = _f2 = PILFont.load_default()
    _t1, _t2 = "▶ 왼쪽에서 소스를 선택하고", "시작 버튼을 누르세요"
    _b1 = _wd.textbbox((0, 0), _t1, font=_f1)
    _b2 = _wd.textbbox((0, 0), _t2, font=_f2)
    _wd.text(((960 - _b1[2]) // 2, 230), _t1, fill=(156, 163, 175), font=_f1)
    _wd.text(((960 - _b2[2]) // 2, 275), _t2, fill=(96, 165, 250), font=_f2)
    frame_ph.image(_wi, use_container_width=True)
    
    status_ph.markdown("""
    <div class='status-box-safe' style='background: #1e293b; border-color: #475569;'>
        <h2 style='color:#cbd5e1;margin:0'>⏸ 대기 중</h2>
        <p style='color:#94a3b8;margin:4px 0 0'>모니터링을 시작해주세요</p>
    </div>""", unsafe_allow_html=True)
    recent = get_recent_events(5)
    if recent:
        lines = "### 📋 최근 이벤트\n"
        for ev in recent: lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}** `{ev['source']}`\n"
        events_ph.markdown(lines)
    else:
        events_ph.caption("저장된 이벤트 없음")
    st.stop()


# ══════════════════════════════════════════════════════
# 프레임 처리 루프 (실행 중)
# ══════════════════════════════════════════════════════
is_rtsp      = st.session_state.is_rtsp
rtsp_reader  = st.session_state.rtsp_reader
vs           = st.session_state.video_source
detector     = st.session_state.detector

if is_rtsp and (rtsp_reader is None or not rtsp_reader.is_alive):
    stop_all(); st.warning("⚠️ RTSP 스레드가 종료됐습니다."); st.stop()

if not is_rtsp and (vs is None or not vs.is_open()):
    stop_all(); st.warning("⚠️ 영상 소스 연결이 끊어졌습니다."); st.stop()

roi_polygon = load_roi(st.session_state.source_name)

while st.session_state.running:
    if is_rtsp:
        frame = rtsp_reader.get_latest_frame()
        ret   = frame is not None
        if not ret and rtsp_reader.error:
            stop_all(); st.error(f"❌ RTSP 오류: {rtsp_reader.error}"); break
    else:
        ret, frame = vs.read_frame()
        if not ret:
            vs.reset(); continue

    if not ret or frame is None:
        frame = st.session_state.last_good_frame
        if frame is None:
            time.sleep(0.02); continue
        is_new_frame = False
    else:
        st.session_state.last_good_frame = frame
        is_new_frame = True

    st.session_state.frame_idx += 1
    frame_idx = st.session_state.frame_idx
    update_fps()
    # 사이드바 FPS/프레임 표시 갱신
    if "__fps_ph" in st.session_state:
        st.session_state["__fps_ph"].markdown(f"**FPS** &nbsp; {st.session_state.fps_display}")
        st.session_state["__frame_ph_count"].markdown(f"**프레임** &nbsp; {frame_idx}")

    if is_new_frame and (frame_idx % FRAME_SKIP == 0 or frame_idx == 1):
        detections = detector.detect(frame, conf=conf_threshold)
        st.session_state.last_detections = detections
    else:
        detections = st.session_state.last_detections

    danger_result = check_danger(detections, roi_polygon)
    is_danger     = danger_result["is_danger"]

    now = time.time()
    event_triggered = False
    if is_danger and not st.session_state.prev_danger:
        if now - st.session_state.last_event_ts > 15.0:
            event_triggered                = True
            st.session_state.last_event_ts = now
            st.session_state.alert_msg     = "🚨 보안 구역 내 위험 감지!"
            st.session_state.alert_expires = now + 4.0
            # 경고음 재생
            alert_ph.markdown("<script>playAlertSound();</script>", unsafe_allow_html=True)

    st.session_state.prev_danger = is_danger

    # ── 🚨 프레임 시각화 ───────────────────────
    annotated = frame.copy()
    annotated = draw_detections(annotated, danger_result, roi_polygon)

    if is_danger:
        # 화면 전체를 붉게 덮는 틴트 효과
        overlay = annotated.copy()
        overlay[:] = (0, 0, 255)
        cv2.addWeighted(overlay, 0.25, annotated, 0.75, 0, annotated)
        
        # 가장자리 빨간색 두꺼운 테두리
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], annotated.shape[0]), (0, 0, 255), 25)
        
        # 화면 상단(Y: 50) 정중앙에 "경고" 아주 굵고 크게(160) 출력
        annotated = draw_text_korean_centered(annotated, "경고", 50, 160, (0, 0, 255))

    # ── 이벤트 저장 ──────────────────────────────────────
    if event_triggered and not st.session_state.post_recording:
        img_name, _ = save_event_image(annotated, st.session_state.source_name)
        st.session_state.pending_img_name = img_name
        st.session_state.pre_frames       = list(st.session_state.frame_buffer)
        st.session_state.post_frames      = []
        st.session_state.post_recording   = True
        st.session_state.post_rec_start   = now

    if st.session_state.post_recording:
        st.session_state.post_frames.append(annotated.copy())
        if now - st.session_state.post_rec_start >= CLIP_POST_SEC:
            all_clip_frames = st.session_state.pre_frames + st.session_state.post_frames
            clip_name, _ = save_event_clip(all_clip_frames, st.session_state.source_name, fps=MAX_CLIP_FPS)
            log_event(st.session_state.source_name, st.session_state.pending_img_name, clip_name)

            # 메모리 즉시 해제
            del all_clip_frames
            st.session_state.post_recording = False
            st.session_state.pre_frames.clear()
            st.session_state.post_frames    = []
            st.session_state.pending_img_name = ""

    st.session_state.frame_buffer.append(annotated.copy())

    # 원격 접속 자동 감지: localhost가 아니면 해상도 축소
    display_frame = annotated
    try:
        host = st.context.headers.get("Host", "localhost")
    except Exception:
        host = "localhost"
    is_remote = "localhost" not in host and "127.0.0.1" not in host
    if is_remote:
        h_orig, w_orig = display_frame.shape[:2]
        max_w = 640
        if w_orig > max_w:
            ratio = max_w / w_orig
            display_frame = cv2.resize(display_frame, (max_w, int(h_orig * ratio)), interpolation=cv2.INTER_AREA)

    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    frame_ph.image(rgb, channels="RGB", use_container_width=True)

    persons = len(danger_result["all_persons"])
    cars    = len(danger_result["all_cars"])
    info_ph.caption(f"사람 {persons}명 | 자동차 {cars}대 | ROI {'✅' if roi_polygon is not None else '⚠️ 미설정'} | {st.session_state.source_name}")

    # ── 오른쪽 상태창 업데이트 ────────────────────────────
    if is_danger:
        status_ph.markdown("""
        <div class='status-box-danger'>
            <h2 class='danger-title'>🚨 위험 경고</h2>
            <p class='danger-sub'>보행자 감지됨!</p>
        </div>""", unsafe_allow_html=True)
    else:
        status_ph.markdown("""
        <div class='status-box-safe'>
            <h2 class='safe-title'>🟢 정상</h2>
            <p class='safe-sub'>안전 구역</p>
        </div>""", unsafe_allow_html=True)

    if now < st.session_state.alert_expires: alert_ph.error(st.session_state.alert_msg)
    else: alert_ph.empty()

    if event_triggered:
        recent = get_recent_events(5)
        if recent:
            lines = "### 📋 최근 이벤트\n"
            for ev in recent: lines += f"- `{ev['timestamp'][:19]}` **{ev['status']}**\n"
            events_ph.markdown(lines)

    if is_remote: time.sleep(0.2)
    else: time.sleep(0.001 if is_rtsp else 0.020)