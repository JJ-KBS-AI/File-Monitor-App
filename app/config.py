from __future__ import annotations

import os
import sys

"""
전역 설정 및 상수 모듈.
"""

# 프리셋 파일
PRESET_FILE = "mxf_monitor_preset.json"
PRESET_KEYS = ("paths", "extensions", "interval")

# 감시 주기(초) 기본값
DEFAULT_INTERVAL = 30

# 용량 안정 시간(입고 완료 판정용) 기본값/허용 범위(초)
DEFAULT_STABLE_SECONDS = 60
MIN_STABLE_SECONDS = 10
MAX_STABLE_SECONDS = 300

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


# 기본 알림음 (입고 시작/완료 시 각각 사용)
# 설계 참고: 설치 파일에 assets/sounds/start.wav, complete.wav 포함 필요
SOUND_START = get_resource_path(os.path.join("assets", "sounds", "start.wav"))
SOUND_COMPLETE = get_resource_path(os.path.join("assets", "sounds", "complete.wav"))

