# core/detector.py — YOLOv8 객체 인식 모듈
# YOLOv8 모델을 불러오고, 프레임에서 person / car 를 탐지합니다.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import YOLO_MODEL, CONFIDENCE_THRESHOLD, CLASS_IDS, TARGET_CLASS_IDS

class Detector:
    """
    YOLOv8 기반 객체 탐지기.
    처음 생성 시 모델을 로드합니다(시간이 걸릴 수 있습니다).
    """

    def __init__(self, model_name: str = YOLO_MODEL):
        # ultralytics 임포트는 여기서 해서 로딩 오류를 한 곳에서 처리
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_name)
            self.loaded = True
        except Exception as e:
            self.loaded = False
            self.load_error = str(e)
            print(f"[Detector] 모델 로드 실패: {e}")

    def detect(self, frame, conf: float = CONFIDENCE_THRESHOLD) -> list[dict]:
        """
        프레임에서 객체를 탐지하고 결과 리스트를 반환합니다.

        반환 형식 (각 항목):
        {
            'class_id':      int,        # COCO 클래스 ID
            'class_name':    str,        # 'person' 또는 'car' 등
            'confidence':    float,      # 신뢰도 0~1
            'bbox':          (x1,y1,x2,y2),
            'center':        (cx, cy),   # 박스 중심점
            'bottom_center': (cx, y2),   # 박스 하단 중심점 (발 위치)
        }
        """
        if not self.loaded:
            return []

        try:
            results = self.model(frame, verbose=False)[0]
        except Exception as e:
            print(f"[Detector] 추론 오류: {e}")
            return []

        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in TARGET_CLASS_IDS:
                continue
            confidence = float(box.conf[0])
            if confidence < conf:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            detections.append({
                "class_id":      cls_id,
                "class_name":    CLASS_IDS.get(cls_id, "unknown"),
                "confidence":    round(confidence, 2),
                "bbox":          (x1, y1, x2, y2),
                "center":        (cx, cy),
                "bottom_center": (cx, y2),   # 발 위치로 ROI 판단에 사용
            })

        return detections
