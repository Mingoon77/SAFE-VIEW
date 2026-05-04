# core/rtsp_presets.py — RTSP 카메라 프리셋 관리
# JSON 파일에 카메라별 RTSP 주소를 저장하고 로드하는 기능

import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR

PRESETS_FILE = os.path.join(BASE_DIR, "rtsp_presets.json")


def load_presets() -> list:
    """저장된 RTSP 프리셋 목록을 반환합니다.
    반환 형식: [{"name": "주차장", "url": "rtsp://..."}]
    """
    if not os.path.exists(PRESETS_FILE):
        return []
    try:
        with open(PRESETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [p for p in data if "name" in p and "url" in p]
        return []
    except Exception as e:
        print(f"[RTSP Presets] 로드 실패: {e}")
        return []


def save_presets(presets: list) -> bool:
    """프리셋 목록을 JSON 파일에 저장합니다."""
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[RTSP Presets] 저장 실패: {e}")
        return False


def add_preset(name: str, url: str) -> tuple[bool, str]:
    """새 프리셋을 추가합니다.
    반환: (성공 여부, 메시지)
    """
    name = name.strip()
    url  = url.strip()

    if not name:
        return False, "카메라 이름을 입력하세요."
    if not url.lower().startswith("rtsp://"):
        return False, "RTSP 주소는 rtsp:// 로 시작해야 합니다."

    presets = load_presets()

    # 중복 이름 검사
    if any(p["name"] == name for p in presets):
        return False, f"'{name}' 이름이 이미 존재합니다."

    presets.append({"name": name, "url": url})
    if save_presets(presets):
        return True, f"'{name}' 프리셋이 추가되었습니다."
    return False, "저장 중 오류가 발생했습니다."


def delete_preset(name: str) -> bool:
    """이름으로 프리셋을 삭제합니다."""
    presets = load_presets()
    new_presets = [p for p in presets if p["name"] != name]
    if len(new_presets) == len(presets):
        return False  # 삭제할 항목 없음
    return save_presets(new_presets)


def get_preset_by_name(name: str) -> dict | None:
    """이름으로 프리셋을 찾아 반환합니다."""
    for p in load_presets():
        if p["name"] == name:
            return p
    return None
