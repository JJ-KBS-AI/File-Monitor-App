# tests/test_preset.py — 프리셋 저장/불러오기 검증
import json
from unittest.mock import patch

import pytest
from PyQt5.QtWidgets import QTableWidgetItem
from pytestqt.qtbot import QtBot

from MXFMonitorApp import DEFAULT_INTERVAL, MXFMonitorApp


def test_preset_save_and_load_roundtrip(qtbot: QtBot, tmp_path, monkeypatch):
    """프리셋 저장 후 불러오기 시 경로·주기가 복원되는지 검사."""
    preset_path = tmp_path / "test_preset.json"
    monkeypatch.setattr("MXFMonitorApp.PRESET_FILE", str(preset_path))

    app = MXFMonitorApp()
    qtbot.addWidget(app)

    app.watch_paths = [str(tmp_path / "watch1"), str(tmp_path / "watch2")]
    app.sound_path_mxf = ""
    app.sound_path_mov = ""
    app.sound_path_xmp = ""
    app.interval_input.setText("15")
    app.path_table.setRowCount(0)
    for i, path in enumerate(app.watch_paths):
        app.path_table.insertRow(i)
        app.path_table.setItem(i, 0, QTableWidgetItem(path))
        app.path_table.setItem(i, 1, QTableWidgetItem("대기 중"))

    with patch("MXFMonitorApp.QMessageBox.information"):
        app.save_preset()
    assert preset_path.exists()
    with open(preset_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["paths"] == app.watch_paths
    assert data["interval"] == 15

    # 초기화 후 불러오기
    app.watch_paths = []
    app.interval_input.setText("10")
    app.path_table.setRowCount(0)
    with patch("MXFMonitorApp.QMessageBox.information"):
        app.load_preset()
    assert app.watch_paths == data["paths"]
    assert app.interval_input.text() == "15"


def test_preset_file_structure(qtbot: QtBot, tmp_path, monkeypatch):
    """저장된 JSON에 paths, interval, sound_* 키가 포함되는지 검사."""
    preset_path = tmp_path / "preset.json"
    monkeypatch.setattr("MXFMonitorApp.PRESET_FILE", str(preset_path))

    app = MXFMonitorApp()
    qtbot.addWidget(app)
    app.watch_paths = ["C:\\Watch"]
    app.interval_input.setText(str(DEFAULT_INTERVAL))
    app.path_table.setRowCount(0)
    app.path_table.insertRow(0)
    app.path_table.setItem(0, 0, QTableWidgetItem(app.watch_paths[0]))
    app.path_table.setItem(0, 1, QTableWidgetItem("대기 중"))

    with patch("MXFMonitorApp.QMessageBox.information"):
        app.save_preset()
    with open(preset_path, encoding="utf-8") as f:
        data = json.load(f)
    assert "paths" in data
    assert "interval" in data
    assert "sound_mxf" in data
    assert "sound_mov" in data
    assert "sound_xmp" in data


def test_load_preset_missing_file(qtbot: QtBot, tmp_path, monkeypatch):
    """프리셋 파일이 없을 때 load_preset이 경고만 하고 기존 상태를 유지하는지."""
    preset_path = tmp_path / "nonexistent.json"
    assert not preset_path.exists()
    monkeypatch.setattr("MXFMonitorApp.PRESET_FILE", str(preset_path))

    app = MXFMonitorApp()
    qtbot.addWidget(app)
    app.watch_paths = ["C:\\Existing"]
    with patch("MXFMonitorApp.QMessageBox.warning"):
        app.load_preset()
    assert app.watch_paths == ["C:\\Existing"]
