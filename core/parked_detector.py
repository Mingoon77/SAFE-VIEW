# core/parked_detector.py — 정지 차량 자체 판단 모듈
#
# 동작 원리 (AI 추적 알고리즘 없이 좌표 비교만 사용):
#   1. 매 프레임마다 감지된 차량의 위치를 기록
#   2. 비슷한 위치에 있는 차량은 같은 차량으로 간주 (단순 거리 매칭)
#   3. 한 차량의 위치가 일정 시간(예: 10초) 동안 거의 안 움직였으면 정지로 판정
#   4. ByteTrack 같은 무거운 알고리즘 안 씀 → CPU 부하 거의 없음

import time
import math

# 추적 중인 차량 정보: [{ "positions": [(timestamp, (cx, cy)), ...], "last_seen": ts }]
_slots: list[dict] = []

# 설정값
MATCH_DISTANCE_PX  = 80.0    # 두 프레임의 차량을 같은 차로 보는 최대 거리 (px)
STATIONARY_SECONDS = 10.0    # 정지로 판정할 최소 시간 (초)
MOVE_THRESHOLD_PX  = 30.0    # 이 거리 이내로만 움직이면 "정지"로 봄
SLOT_EXPIRE_SEC    = 5.0     # 이 시간 동안 안 보이면 슬롯 삭제 (메모리 정리)


def _distance(p1, p2) -> float:
    """두 점 사이의 거리"""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def update(car_centers: list[tuple]) -> list[bool]:
    """
    현재 프레임의 차량 중심 좌표 리스트를 받아,
    각 차량이 "정지 상태"인지 여부를 같은 순서의 리스트로 반환합니다.

    car_centers: [(cx, cy), (cx, cy), ...]  현재 프레임의 모든 차량 중심점
    반환: [True/False, True/False, ...]      각 차량의 정지 여부
    """
    now = time.time()
    matched_slots = set()
    results = [False] * len(car_centers)

    # 1) 현재 프레임의 각 차량을 가장 가까운 기존 슬롯과 매칭
    for idx, center in enumerate(car_centers):
        best_slot_idx = -1
        best_distance = MATCH_DISTANCE_PX

        for s_idx, slot in enumerate(_slots):
            if s_idx in matched_slots:
                continue   # 이미 다른 차량에 매칭된 슬롯은 건너뜀
            last_pos = slot["positions"][-1][1]
            dist = _distance(last_pos, center)
            if dist < best_distance:
                best_distance = dist
                best_slot_idx = s_idx

        if best_slot_idx >= 0:
            # 기존 슬롯에 매칭 → 위치 추가
            slot = _slots[best_slot_idx]
            slot["positions"].append((now, center))
            slot["last_seen"] = now
            matched_slots.add(best_slot_idx)
            # 정지 여부 판정
            results[idx] = _is_stationary(slot, now)
        else:
            # 새 슬롯 생성
            _slots.append({
                "positions": [(now, center)],
                "last_seen": now,
            })
            # 새 차량은 당연히 정지 아님

    # 2) 오래된 슬롯 정리 (메모리 누수 방지)
    _slots[:] = [s for s in _slots if now - s["last_seen"] <= SLOT_EXPIRE_SEC]

    # 3) 각 슬롯의 위치 이력 중 너무 오래된 것은 잘라냄
    cutoff = now - (STATIONARY_SECONDS * 1.5)
    for slot in _slots:
        slot["positions"] = [(t, p) for t, p in slot["positions"] if t >= cutoff]

    return results


def _is_stationary(slot: dict, now: float) -> bool:
    """슬롯의 위치 이력을 보고 정지 여부 판단"""
    positions = slot["positions"]
    if len(positions) < 2:
        return False

    # STATIONARY_SECONDS 이전 시점의 위치 찾기
    cutoff = now - STATIONARY_SECONDS
    old_pos = None
    for ts, pos in positions:
        if ts <= cutoff:
            old_pos = pos
        else:
            break

    if old_pos is None:
        return False   # 아직 그만큼 데이터가 없음

    # 현재 위치와 비교
    current_pos = positions[-1][1]
    return _distance(old_pos, current_pos) < MOVE_THRESHOLD_PX


def reset() -> None:
    """모니터링 시작/정지 시 모든 상태 초기화"""
    _slots.clear()


def get_slot_count() -> int:
    """현재 추적 중인 차량 슬롯 수 (디버그용)"""
    return len(_slots)
