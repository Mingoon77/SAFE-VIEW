# config.py — 전역 설정값 모음
# 여기서 모델명, 폴더 경로, 감지 임계값 등을 한곳에서 관리합니다.

import os

# ── 모델 설정 ──────────────────────────────────────────
YOLO_MODEL = "yolov8n.pt"          # 가장 가벼운 YOLOv8 nano 모델 (자동 다운로드)
CONFIDENCE_THRESHOLD = 0.4         # 객체 인식 최소 신뢰도 (0~1)

# COCO 데이터셋 클래스 ID (YOLOv8 기본값)
CLASS_IDS = {
    0: "person",
    2: "car",
    3: "motorcycle",
    7: "truck",
}
# 이번 프로토타입에서 실제로 감지할 클래스
TARGET_CLASS_IDS = [0, 2]          # person, car

# ── 폴더 경로 ──────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
EVENTS_DIR      = os.path.join(BASE_DIR, "saved_events")
ROI_DIR         = os.path.join(BASE_DIR, "roi_configs")
LOGS_DIR        = os.path.join(BASE_DIR, "logs")
LOG_FILE        = os.path.join(LOGS_DIR, "events_log.csv")

# ── 영상 처리 설정 ─────────────────────────────────────
FRAME_SKIP      = 2       # N 프레임마다 1번 YOLO 실행 (부하 감소)
CLIP_PRE_SEC    = 5       # 이벤트 발생 전 몇 초 저장
CLIP_POST_SEC   = 10      # 이벤트 발생 후 몇 초 저장
MAX_CLIP_FPS    = 10      # 저장 클립 FPS

# ── ROI 박스 색상 (BGR) ────────────────────────────────
COLOR_ROI        = (0, 255, 255)   # 노란색 (ROI 테두리)
COLOR_NORMAL     = (0, 200, 0)     # 초록색 (정상 바운딩 박스)
COLOR_DANGER     = (0, 0, 220)     # 빨간색 (위험 바운딩 박스)
COLOR_WARNING_BG = (0, 0, 180)     # 경고 오버레이 색상

# ── 미리 정의된 예시 소스 (드롭다운에서 선택 가능) ─────
PRESET_SOURCES = {
    "샘플 영상 (data 폴더에서 선택)": "__file__",
    "자택 CCTV (RTSP 직접 입력)":    "__rtsp__",
}
