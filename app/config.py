from __future__ import annotations

import os
import sys

"""
전역 설정 및 상수 모듈.
"""

# 프리셋 파일
# 설치본(Program Files)에서도 저장 가능하도록 사용자 쓰기 경로(AppData)를 사용한다.
APP_DATA_DIR = os.path.join(
    os.getenv("LOCALAPPDATA", os.path.expanduser("~")),
    "KBS",
    "MXFMonitorApp",
)
PRESET_FILE = os.path.join(APP_DATA_DIR, "mxf_monitor_preset.json")
# 개발/구버전 호환용 상대 경로
LEGACY_PRESET_FILE = "mxf_monitor_preset.json"
PRESET_KEYS = ("paths", "extensions", "interval")

# 감시 주기(초) 기본값
DEFAULT_INTERVAL = 30

# 용량 안정 시간(입고 완료 판정용) 기본값/허용 범위(초)
DEFAULT_STABLE_SECONDS = 60
MIN_STABLE_SECONDS = 10
MAX_STABLE_SECONDS = 300
# 완료 판정 전, 연속으로 "변화 없음"을 만족해야 하는 최소 스캔 횟수
# 네트워크 스토리지의 일시 정체 구간에서 조기 완료 오탐을 줄인다.
MIN_STABLE_CHECKS = 3

# 기본 감시 확장자 목록
DEFAULT_WATCH_EXTENSIONS = [
    ".mxf",
    ".mov",
    ".mp4"
]

# 알림 타이틀 및 메시지
NOTIFICATION_TITLE = "파일 입고 알림"
NOTIFICATION_MESSAGES = {
    "started": "파일 입고가 시작되었습니다.",
    "completed": "파일 입고가 완료되었습니다.",
}


def get_resource_path(relative_path: str) -> str:
    """
    PyInstaller로 패키징했을 때와 개발 환경 모두에서 동작하는 리소스 경로 헬퍼.
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def _first_existing_resource(paths: list[str]) -> str:
    """후보 리소스 경로 중 실제 존재하는 첫 경로를 반환."""
    for rel in paths:
        candidate = get_resource_path(rel)
        if os.path.exists(candidate):
            return candidate
    return get_resource_path(paths[0])


# 기본 알림음 (입고 시작/완료 시 각각 사용)
# 패키징/개발 경로 차이를 모두 커버하도록 다중 후보를 검사한다.
SOUND_START = _first_existing_resource(
    [
        os.path.join("assets", "sounds", "start.wav"),
        os.path.join("app", "assets", "sounds", "start.wav"),
        "start.wav",
    ]
)
SOUND_COMPLETE = _first_existing_resource(
    [
        os.path.join("assets", "sounds", "complete.wav"),
        os.path.join("app", "assets", "sounds", "complete.wav"),
        "complete.wav",
    ]
)

# KBS_CI 폰트 (패키징/개발 경로 모두 지원)
KBS_CI_FONT = _first_existing_resource(
    [
        "KBS_CI.ttf",
        os.path.join("assets", "fonts", "KBS_CI.ttf"),
        os.path.join("app", "assets", "fonts", "KBS_CI.ttf"),
    ]
)

