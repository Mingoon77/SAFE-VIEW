# core/event_saver.py — 이벤트 저장 모듈
# 위험 이벤트 발생 시 이미지, 영상 클립, CSV 로그를 저장합니다.

import cv2
import os
import csv
from datetime import datetime
from collections import deque
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EVENTS_DIR, LOGS_DIR, LOG_FILE, MAX_CLIP_FPS


def ensure_dirs():
    """필요한 폴더가 없으면 자동으로 생성합니다."""
    os.makedirs(EVENTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)


def save_event_image(frame, source_name: str) -> tuple[str, str]:
    """
    이벤트 발생 시점 프레임을 이미지로 저장합니다.
    반환: (파일명, 전체경로)
    """
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in source_name)
    filename = f"event_{safe_name}_{timestamp}.jpg"
    filepath = os.path.join(EVENTS_DIR, filename)
    cv2.imwrite(filepath, frame)
    return filename, filepath


def save_event_clip(frame_buffer: deque, source_name: str, fps: float = MAX_CLIP_FPS) -> tuple[str | None, str | None]:
    """
    프레임 버퍼(deque)에 담긴 프레임을 MP4 클립으로 저장합니다.
    반환: (파일명, 전체경로) 또는 (None, None)
    """
    ensure_dirs()
    if not frame_buffer:
        return None, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in source_name)
    filename = f"clip_{safe_name}_{timestamp}.mp4"
    filepath = os.path.join(EVENTS_DIR, filename)

    frames = list(frame_buffer)
    h, w = frames[0].shape[:2]

    # H.264(avc1) 코덱 → 브라우저에서 바로 재생 가능
    # avc1 실패 시 mp4v로 폴백
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    writer = cv2.VideoWriter(filepath, fourcc, float(fps), (w, h))
    if not writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(filepath, fourcc, float(fps), (w, h))
    for f in frames:
        writer.write(f)
    writer.release()

    return filename, filepath


def log_event(source_name: str, image_filename: str, clip_filename: str = None):
    """
    이벤트 정보를 CSV 로그 파일에 한 행 추가합니다.
    """
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        # 파일이 없으면 헤더 추가
        if not file_exists:
            writer.writerow(["timestamp", "source", "status", "image_file", "clip_file"])
        writer.writerow([timestamp, source_name, "위험", image_filename, clip_filename or ""])


def get_recent_events(n: int = 10) -> list[dict]:
    """
    최근 N건의 이벤트 로그를 반환합니다.
    반환: list of dict (CSV 행)
    """
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return rows[-n:][::-1]  # 최신 순으로 반환
    except Exception as e:
        print(f"[EventSaver] 로그 읽기 오류: {e}")
        return []


def get_event_image_path(filename: str) -> str | None:
    """이벤트 이미지 파일의 전체 경로를 반환합니다."""
    path = os.path.join(EVENTS_DIR, filename)
    return path if os.path.exists(path) else None


def delete_event(timestamp: str):
    """
    특정 timestamp의 이벤트를 CSV 로그에서 삭제하고,
    연결된 이미지/클립 파일도 함께 삭제합니다.
    """
    if not os.path.exists(LOG_FILE):
        return False

    # CSV에서 해당 이벤트 찾기
    rows = []
    deleted_files = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row.get("timestamp") == timestamp:
                    # 삭제 대상: 연결된 파일 기록
                    for key in ["image_file", "clip_file"]:
                        fname = row.get(key, "")
                        if fname:
                            fpath = os.path.join(EVENTS_DIR, fname)
                            if os.path.exists(fpath):
                                os.remove(fpath)
                                deleted_files.append(fname)
                            # 변환된 클립도 삭제
                            converted = os.path.join(EVENTS_DIR, "_converted", fname)
                            if os.path.exists(converted):
                                os.remove(converted)
                else:
                    rows.append(row)

        # CSV 다시 쓰기 (삭제된 행 제외)
        with open(LOG_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return True
    except Exception as e:
        print(f"[EventSaver] 삭제 오류: {e}")
        return False
