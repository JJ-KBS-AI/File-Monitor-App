# tests/test_folder_checker.py — FolderCheckerWorker 스캔 로직 테스트
import os

import pytest
from pytestqt.qtbot import QtBot

from MXFMonitorApp import WATCH_EXTENSIONS, FolderCheckerWorker


def test_worker_finds_mxf_mov_xmp_in_directory(qtbot: QtBot, sample_watch_dir):
    """감시 디렉터리 내 .mxf, .mov, .xmp 파일을 찾아 시그널로 전달하는지 검사."""
    results = []

    def on_found(lst):
        results.append(lst)

    worker = FolderCheckerWorker([str(sample_watch_dir)])
    worker.files_found.connect(on_found)
    worker.start()
    qtbot.waitUntil(lambda: not worker.isRunning(), timeout=5000)

    assert len(results) == 1
    raw = results[0]
    assert len(raw) >= 4  # test.mxf, test.mov, test.xmp, subdir/nested.mxf

    full_paths = {r[0] for r in raw}
    names = {os.path.basename(r[0]) for r in raw}
    assert "test.mxf" in names
    assert "test.mov" in names
    assert "test.xmp" in names
    assert "nested.mxf" in names

    for full_path, watch_path, filename, ctime, ext in raw:
        assert os.path.isfile(full_path)
        assert watch_path == str(sample_watch_dir)
        assert filename.lower().endswith(WATCH_EXTENSIONS)
        assert ext in ("mxf", "mov", "xmp")


def test_worker_ignores_non_watch_extensions(qtbot: QtBot, sample_watch_dir_ignore):
    """감시 확장자가 아닌 파일만 있는 디렉터리는 0건으로 반환."""
    results = []

    def on_found(lst):
        results.append(lst)

    worker = FolderCheckerWorker([str(sample_watch_dir_ignore)])
    worker.files_found.connect(on_found)
    worker.start()
    qtbot.waitUntil(lambda: not worker.isRunning(), timeout=5000)

    assert len(results) == 1
    assert len(results[0]) == 0


def test_worker_empty_paths(qtbot: QtBot):
    """감시 경로가 비어 있으면 빈 리스트를 emit."""
    results = []

    def on_found(lst):
        results.append(lst)

    worker = FolderCheckerWorker([])
    worker.files_found.connect(on_found)
    worker.start()
    qtbot.waitUntil(lambda: not worker.isRunning(), timeout=3000)

    assert len(results) == 1
    assert results[0] == []
