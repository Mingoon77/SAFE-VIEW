# core/video_source.py — 영상 입력 소스 관리 모듈
# RTSP 스트림 및 로컬 영상 파일을 일관된 인터페이스로 처리합니다.
#
# [RTSP 연동 핵심 사항]
# - OPENCV_FFMPEG_CAPTURE_OPTIONS 환경변수로 TCP 전송 + 타임아웃 설정
# - 연결 타임아웃 5초, 읽기 타임아웃 5초 (기본값은 수십 초로 UI 멈춤 유발)
# - CAP_PROP_BUFFERSIZE=1로 버퍼 최소화 → 최신 프레임 위주 처리
# - grab()+read() 이중 호출 제거 → read() 단독 사용 (안정성↑)

import cv2
import os
import time


# ── RTSP 전역 설정 (모듈 임포트 시 1회 적용) ──────────────
# TCP 전송: UDP보다 안정적 (패킷 손실 방지)
# timeout: 마이크로초 단위 → 5,000,000 = 5초
os.environ.setdefault(
    "OPENCV_FFMPEG_CAPTURE_OPTIONS",
    "rtsp_transport;tcp|timeout;5000000",
)


class VideoSource:
    """
    RTSP 또는 로컬 파일을 감싸는 영상 입력 클래스.

    사용 예시:
        src = VideoSource("rtsp://admin:1234@192.168.1.100:554/Streaming/Channels/402")
        src = VideoSource("C:/videos/test.mp4")
    """

    def __init__(self, source: str):
        self.source       = source
        self.cap          = None
        self.is_rtsp      = source.lower().startswith("rtsp://")
        self._frame_count = 0
        self._consec_fail = 0    # 연속 읽기 실패 횟수 (자동 재연결 판단용)

    # ── 열기 ──────────────────────────────────────────────
    def open(self, timeout_sec: float = 5.0) -> bool:
        """
        영상 소스를 엽니다.
        RTSP: TCP 전송 + 5초 타임아웃 적용
        파일: 경로 존재 확인 후 열기
        반환: 성공 True / 실패 False
        """
        try:
            if self.is_rtsp:
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                # 버퍼 크기 1 → 가장 최신 프레임만 유지
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            else:
                if not os.path.exists(self.source):
                    print(f"[VideoSource] 파일 없음: {self.source}")
                    return False
                self.cap = cv2.VideoCapture(self.source)

            if not self.cap.isOpened():
                print(f"[VideoSource] 열기 실패: {self.source}")
                return False

            self._frame_count = 0
            self._consec_fail = 0
            return True

        except Exception as e:
            print(f"[VideoSource] open() 예외: {e}")
            return False

    # ── 프레임 읽기 ───────────────────────────────────────
    def read_frame(self):
        """
        다음 프레임을 읽어 반환합니다.
        반환: (success: bool, frame: ndarray | None)

        [이전 버그 수정]
        grab() + read() 이중 호출 제거.
        read() = 내부적으로 grab() + retrieve() 를 함께 수행.
        grab() 후 read() 하면 grab이 두 번 되어 프레임이 건너뜀.
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None

        try:
            ret, frame = self.cap.read()
            if ret:
                self._frame_count += 1
                self._consec_fail = 0
            else:
                self._consec_fail += 1
            return ret, frame
        except Exception as e:
            print(f"[VideoSource] read_frame() 예외: {e}")
            self._consec_fail += 1
            return False, None

    # ── 재연결 ────────────────────────────────────────────
    def reconnect(self, max_attempts: int = 3, wait_sec: float = 2.0) -> bool:
        """
        RTSP 스트림 재연결을 시도합니다.
        max_attempts번 시도하고 성공하면 True 반환.
        """
        if not self.is_rtsp:
            return False

        self.release()
        for attempt in range(1, max_attempts + 1):
            print(f"[VideoSource] RTSP 재연결 시도 {attempt}/{max_attempts}...")
            time.sleep(wait_sec)
            if self.open():
                print(f"[VideoSource] RTSP 재연결 성공 (시도 {attempt}회)")
                return True
        print("[VideoSource] RTSP 재연결 최종 실패")
        return False

    # ── 유틸리티 ──────────────────────────────────────────
    def get_fps(self) -> float:
        """소스 FPS 반환. 알 수 없으면 25.0 (기본값)."""
        if self.cap and self.cap.isOpened():
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            return fps if fps > 0 else 25.0
        return 25.0

    def get_frame_size(self) -> tuple[int, int]:
        """(width, height) 반환."""
        if self.cap and self.cap.isOpened():
            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if w > 0 and h > 0:
                return w, h
        return 640, 480

    def get_total_frames(self) -> int:
        """총 프레임 수 (파일 전용, RTSP는 -1)."""
        if self.cap and not self.is_rtsp:
            return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return -1

    def get_first_frame(self):
        """
        첫 번째 프레임 한 장만 읽어 반환합니다.
        소스를 열고 한 장 읽은 뒤 닫습니다.
        ROI 설정 화면에서 기준 프레임을 얻을 때 사용합니다.
        """
        vs = VideoSource(self.source)
        try:
            if not vs.open():
                return None
            ret, frame = vs.cap.read()
            return frame if ret else None
        finally:
            vs.release()  # 예외 발생해도 반드시 해제

    def reset(self):
        """파일 소스를 처음으로 되감습니다 (RTSP는 무시)."""
        if self.cap and not self.is_rtsp:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self._frame_count = 0

    def release(self):
        """VideoCapture를 해제합니다."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self._frame_count = 0
        self._consec_fail = 0

    def is_open(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def consecutive_failures(self) -> int:
        return self._consec_fail


# ── RTSP 주소 유효성 검사 함수 ────────────────────────────
def validate_rtsp_url(url: str) -> tuple[bool, str]:
    """
    RTSP URL 기본 형식 검사.
    반환: (유효 여부, 오류 메시지)

    올바른 형식 예시:
        rtsp://admin:1234@192.168.0.100:554/Streaming/Channels/402
    """
    if not url.strip():
        return False, "RTSP 주소를 입력하세요."

    if not url.lower().startswith("rtsp://"):
        return False, "주소는 rtsp:// 로 시작해야 합니다."

    # 플레이스홀더 텍스트 감지 (대괄호 포함)
    if "[" in url or "]" in url:
        return False, "예시 주소의 [ID], [PW], [IP] 부분을 실제 값으로 교체하세요."

    # 최소 구조: rtsp://x@x:x/x
    body = url[7:]  # rtsp:// 제거
    if "@" not in body:
        return False, "주소에 계정 정보(ID:PW@IP)가 필요합니다. 계정 없이 접속하는 경우는 rtsp://IP:포트/경로 형식을 사용하세요."

    return True, ""


def test_rtsp_connection(url: str, timeout_sec: float = 5.0) -> tuple[bool, str]:
    """
    실제로 RTSP에 연결해 첫 프레임을 받아보고 결과를 반환합니다.
    반환: (성공 여부, 메시지)
    """
    valid, err = validate_rtsp_url(url)
    if not valid:
        return False, err

    vs = VideoSource(url)
    if not vs.open():
        return False, "연결 실패: DVR/카메라가 꺼져있거나, IP/포트/경로가 잘못되었거나, 방화벽이 차단 중일 수 있습니다."

    ret, frame = vs.cap.read()
    vs.release()

    if ret and frame is not None:
        h, w = frame.shape[:2]
        return True, f"연결 성공! 해상도: {w}×{h}"
    else:
        return False, "연결은 됐지만 프레임을 받지 못했습니다. 채널 경로를 확인하세요."
