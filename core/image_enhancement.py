# core/image_enhancement.py — 야간/저조도 영상 자동 밝기 보정
#
# 동작 방식:
#   1. 프레임의 평균 밝기를 측정
#   2. 일정 임계값 이하면 "저조도"로 판단
#   3. CLAHE(Contrast Limited Adaptive Histogram Equalization)로 보정
#      → 단순 히스토그램 평활화보다 자연스럽고, 노이즈 증폭 적음

import cv2
import numpy as np

# 설정값
DARK_THRESHOLD     = 80     # 평균 밝기가 이 값 이하면 저조도로 판정 (0~255)
CLAHE_CLIP_LIMIT   = 2.5    # CLAHE 대비 제한값 (높을수록 강한 대비)
CLAHE_TILE_SIZE    = (8, 8) # CLAHE 타일 크기

# CLAHE 객체는 한 번만 생성해서 재사용 (매 프레임 생성 비용 절감)
_clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_SIZE)


def get_brightness(frame) -> float:
    """프레임의 평균 밝기를 반환합니다 (0~255)."""
    if frame is None:
        return 0.0
    # BGR → 그레이스케일로 변환 후 평균
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def is_low_light(frame) -> bool:
    """저조도 여부 판단"""
    return get_brightness(frame) < DARK_THRESHOLD


def enhance_low_light(frame):
    """
    저조도 프레임 자동 보정.
    LAB 색공간으로 변환 후 L(밝기) 채널에만 CLAHE 적용 → 색상 왜곡 최소화.
    """
    if frame is None:
        return frame

    # BGR → LAB
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # 밝기(L) 채널에만 CLAHE 적용
    l_enhanced = _clahe.apply(l)

    # 다시 합치고 BGR로 복원
    lab_enhanced = cv2.merge((l_enhanced, a, b))
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)


def auto_enhance(frame, force: bool = False):
    """
    프레임 자동 보정 (저조도일 때만 적용).
    force=True 면 밝기와 무관하게 항상 보정.
    반환: (보정된 프레임, 보정 적용 여부)
    """
    if frame is None:
        return frame, False
    if force or is_low_light(frame):
        return enhance_low_light(frame), True
    return frame, False
