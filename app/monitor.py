from __future__ import annotations

import os
import time
from typing import Iterable, List, Sequence, Set, Tuple

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .config import DEFAULT_STABLE_SECONDS, MIN_STABLE_CHECKS
from .models import FileStatus, MonitoredFile

ScanResult = Tuple[str, str, str, float, str]  # full_path, watch_path, filename, ctime, ext


class FolderCheckerWorker(QThread):
    """감시 경로를 백그라운드에서 스캔하고 결과를 시그널로 전달한다."""

    files_found = pyqtSignal(list)  # list[ScanResult]

    def __init__(self, watch_paths: Sequence[str], extensions: Iterable[str]):
        super().__init__()
        self.watch_paths: List[str] = list(watch_paths) if watch_paths else []
        self.extensions: Set[str] = {ext.lower() for ext in (extensions or [])}

    def run(self) -> None:
        results: List[ScanResult] = []
        if not self.extensions:
            self.files_found.emit(results)
            return

        for path in self.watch_paths:
            try:
                for root, _, files in os.walk(path):
                    for filename in files:
                        lower_name = filename.lower()
                        if not any(lower_name.endswith(ext) for ext in self.extensions):
                            continue
                        full_path = os.path.join(root, filename)
                        if os.path.isfile(full_path):
                            ctime = os.path.getctime(full_path)
                            ext = filename.split(".")[-1].lower() if "." in filename else ""
                            results.append((full_path, path, filename, ctime, ext))
            except Exception as e:  # pragma: no cover - 로깅만
                print(f"스캔 오류 ({path}): {e}")
        self.files_found.emit(results)


class MonitorController(QObject):
    """
    폴더 스캔 결과를 받아 파일별 상태를 관리하고,
    입고 시작/완료 이벤트를 시그널로 내보낸다.
    """

    file_started = pyqtSignal(MonitoredFile)
    file_completed = pyqtSignal(MonitoredFile)
    path_status_changed = pyqtSignal(str, str)  # watch_path, status

    def __init__(self, stable_seconds: int = DEFAULT_STABLE_SECONDS):
        super().__init__()
        self.stable_seconds = stable_seconds
        # full_path -> MonitoredFile
        self.files: dict[str, MonitoredFile] = {}

    def reset(self, stable_seconds: int) -> None:
        self.stable_seconds = stable_seconds
        self.files.clear()

    def process_scan_results(self, results: Sequence[ScanResult], start_time: float) -> None:
        now = time.time()
        for full_path, watch_path, filename, ctime, ext in results:
            # 감시 시작 이전에 생성된 파일은 처음 한 번만 걸러낸다
            mf = self.files.get(full_path)
            if mf is None and ctime < start_time:
                continue

            try:
                size = os.path.getsize(full_path)
                mtime = os.path.getmtime(full_path)
            except OSError:
                continue

            if mf is None:
                # 새 파일
                mf = MonitoredFile(
                    path=full_path,
                    name=filename,
                    watch_root=watch_path,
                    size=size,
                    last_mtime=mtime,
                    last_changed_at=now,
                    unchanged_checks=0,
                    status=FileStatus.IN_PROGRESS,
                )
                self.files[full_path] = mf
                self.path_status_changed.emit(watch_path, "입고 중")
                self.file_started.emit(mf)
                continue

            # 네트워크 복사 환경 오탐 방지를 위해 크기/mtime 모두 추적한다.
            # 둘 중 하나라도 변하면 아직 입고 진행 중으로 본다.
            if size != mf.size or mtime != mf.last_mtime:
                mf.size = size
                mf.last_mtime = mtime
                mf.last_changed_at = now
                mf.unchanged_checks = 0
                if mf.status is not FileStatus.IN_PROGRESS:
                    mf.status = FileStatus.IN_PROGRESS
                    self.path_status_changed.emit(watch_path, "입고 중")
            else:
                mf.unchanged_checks += 1

            # 안정 시간이 지났는지 검사
            if (
                now - mf.last_changed_at >= self.stable_seconds
                and mf.unchanged_checks >= MIN_STABLE_CHECKS
                and mf.status is not FileStatus.COMPLETED
            ):
                mf.status = FileStatus.COMPLETED
                self.path_status_changed.emit(watch_path, "입고 완료")
                self.file_completed.emit(mf)

