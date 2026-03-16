# tests/test_constants.py — 상수 및 매핑 검증
from MXFMonitorApp import (
    DEFAULT_INTERVAL,
    NOTIFICATION_MESSAGES,
    NOTIFICATION_TITLE,
    PRESET_FILE,
    PRESET_KEYS,
    SOUND_ATTR_MAP,
    WATCH_EXTENSIONS,
)


def test_watch_extensions():
    assert ".mxf" in WATCH_EXTENSIONS
    assert ".mov" in WATCH_EXTENSIONS
    assert ".xmp" in WATCH_EXTENSIONS
    assert len(WATCH_EXTENSIONS) == 3


def test_preset_keys():
    assert "paths" in PRESET_KEYS
    assert "sound_mxf" in PRESET_KEYS
    assert "sound_mov" in PRESET_KEYS
    assert "sound_xmp" in PRESET_KEYS
    assert "interval" in PRESET_KEYS


def test_notification_messages():
    assert NOTIFICATION_MESSAGES["mxf"]
    assert NOTIFICATION_MESSAGES["mov"]
    assert NOTIFICATION_MESSAGES["xmp"]
    assert NOTIFICATION_TITLE == "파일 입고 알림"


def test_sound_attr_map():
    assert SOUND_ATTR_MAP["mxf"] == "sound_path_mxf"
    assert SOUND_ATTR_MAP["mov"] == "sound_path_mov"
    assert SOUND_ATTR_MAP["xmp"] == "sound_path_xmp"


def test_default_interval():
    assert DEFAULT_INTERVAL >= 1
    assert isinstance(DEFAULT_INTERVAL, int)


def test_preset_file_name():
    assert PRESET_FILE.endswith(".json")
