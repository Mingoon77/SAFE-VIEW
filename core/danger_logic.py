# core/danger_logic.py — 위험 상태 판단 로직
# 단순한 규칙 기반: person + car 동시 존재 & person이 ROI 내부 → 위험

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.roi_manager import is_point_in_roi


def check_danger(detections: list, roi_polygon) -> dict:
    """
    탐지 결과와 ROI를 받아 위험 상태 여부를 판단합니다.

    반환 dict:
    {
        "is_danger":         bool,   # 위험 상태 여부
        "has_person":        bool,
        "has_car":           bool,
        "dangerous_persons": list,   # ROI 내부에 있는 person 탐지 목록
        "all_persons":       list,
        "all_cars":          list,
    }
    """
    persons = [d for d in detections if d["class_name"] == "person"]
    cars    = [d for d in detections if d["class_name"] == "car"]

    result = {
        "is_danger":         False,
        "has_person":        len(persons) > 0,
        "has_car":           len(cars) > 0,
        "dangerous_persons": [],
        "all_persons":       persons,
        "all_cars":          cars,
    }

    # 위험 판단 조건:
    # 1) person 존재
    # 2) car 존재
    # 3) person의 발 위치(bottom_center)가 ROI 내부
    if not persons or not cars:
        return result

    if roi_polygon is None:
        # ROI 미설정 시 위험 판단 불가 → 정상 처리
        return result

    dangerous = []
    for person in persons:
        # 발 위치(bottom_center)로 ROI 판단
        if is_point_in_roi(person["bottom_center"], roi_polygon):
            dangerous.append(person)

    if dangerous:
        result["is_danger"] = True
        result["dangerous_persons"] = dangerous

    return result


def draw_detections(frame, danger_result: dict, roi_polygon=None):
    """
    프레임 위에 바운딩 박스, 레이블, ROI를 그립니다.
    위험 상태이면 빨간색, 정상이면 초록색 박스.
    """
    import cv2
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import COLOR_NORMAL, COLOR_DANGER
    from core.roi_manager import draw_roi_on_frame

    is_danger = danger_result["is_danger"]

    # ROI 그리기
    frame = draw_roi_on_frame(frame, roi_polygon, danger=is_danger)

    # 위험한 person ID 집합 (비교용)
    dangerous_ids = {id(p) for p in danger_result["dangerous_persons"]}

    # 모든 탐지 박스 그리기
    all_detections = danger_result["all_persons"] + danger_result["all_cars"]
    for det in all_detections:
        x1, y1, x2, y2 = det["bbox"]
        # 위험 상태일 때는 모든 박스를 빨간색으로
        color = COLOR_DANGER if is_danger else COLOR_NORMAL
        # 박스
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # 레이블 배경
        label = f"{det['class_name']} {det['confidence']:.2f}"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - lh - 6), (x1 + lw, y1), color, -1)
        # 레이블 텍스트
        cv2.putText(frame, label, (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    # 위험 상태: 빨간 테두리 오버레이
    if is_danger:
        h, w = frame.shape[:2]
        thickness = 8
        cv2.rectangle(frame, (0, 0), (w - 1, h - 1), COLOR_DANGER, thickness)

    return frame
