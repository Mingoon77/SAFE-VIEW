# core/roi_manager.py — ROI(관심구역) 저장·불러오기·판단 모듈
# ROI는 다각형 좌표 리스트로 관리하며, 소스명 기준으로 JSON 파일에 저장됩니다.

import os
import json
import numpy as np
import cv2
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ROI_DIR, COLOR_ROI


def _roi_path(source_name: str) -> str:
    """소스명에 대응하는 ROI JSON 파일 경로를 반환합니다."""
    # 파일명에 사용할 수 없는 문자 제거
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in source_name)
    return os.path.join(ROI_DIR, f"{safe_name}.json")


def save_roi(source_name: str, points: list) -> str:
    """
    ROI 좌표를 JSON 파일로 저장합니다.
    points: [[x1,y1], [x2,y2], ...] 형태의 리스트
    반환: 저장된 파일 경로
    """
    os.makedirs(ROI_DIR, exist_ok=True)
    path = _roi_path(source_name)
    data = {
        "source": source_name,
        "points": [[int(p[0]), int(p[1])] for p in points],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_roi(source_name: str):
    """
    JSON 파일에서 ROI 좌표를 불러옵니다.
    반환: numpy array (N,2) or None (파일 없으면)
    """
    path = _roi_path(source_name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pts = np.array(data["points"], dtype=np.int32)
        if len(pts) < 3:
            return None
        return pts
    except Exception as e:
        print(f"[ROI] 불러오기 실패: {e}")
        return None


def list_saved_rois() -> list[str]:
    """저장된 ROI 파일 목록(소스명)을 반환합니다."""
    if not os.path.exists(ROI_DIR):
        return []
    names = []
    for fname in os.listdir(ROI_DIR):
        if fname.endswith(".json"):
            path = os.path.join(ROI_DIR, fname)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                names.append(data.get("source", fname.replace(".json", "")))
            except Exception:
                names.append(fname.replace(".json", ""))
    return names


def is_point_in_roi(point: tuple, roi_polygon) -> bool:
    """
    주어진 점(x, y)이 ROI 다각형 내부에 있는지 판단합니다.
    roi_polygon: numpy array (N,2) or None
    """
    if roi_polygon is None or len(roi_polygon) < 3:
        return False
    # pointPolygonTest: 양수=내부, 0=경계, 음수=외부
    result = cv2.pointPolygonTest(
        roi_polygon.reshape((-1, 1, 2)).astype(np.int32),
        (float(point[0]), float(point[1])),
        False,
    )
    return result >= 0


def draw_roi_on_frame(frame, roi_polygon, danger: bool = False):
    """
    프레임 위에 ROI를 반투명 다각형으로 그립니다.
    danger=True 이면 빨간색 강조, 아니면 노란색.
    """
    if roi_polygon is None or len(roi_polygon) < 3:
        return frame

    pts = roi_polygon.reshape((-1, 1, 2)).astype(np.int32)
    color = (0, 0, 200) if danger else COLOR_ROI

    # 반투명 채우기
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

    # 테두리
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

    # 꼭짓점 번호 표시
    for i, pt in enumerate(roi_polygon):
        cv2.circle(frame, (int(pt[0]), int(pt[1])), 5, color, -1)

    return frame


def parse_roi_text(text: str):
    """
    텍스트 형식 "x1,y1; x2,y2; x3,y3 ..." 을 numpy array 로 변환합니다.
    실패하면 None 을 반환합니다.
    """
    try:
        points = []
        # 세미콜론 또는 줄바꿈으로 분리
        for token in text.replace("\n", ";").split(";"):
            token = token.strip()
            if not token:
                continue
            parts = token.split(",")
            if len(parts) != 2:
                return None
            x, y = int(parts[0].strip()), int(parts[1].strip())
            points.append([x, y])
        if len(points) < 3:
            return None
        return np.array(points, dtype=np.int32)
    except Exception:
        return None
