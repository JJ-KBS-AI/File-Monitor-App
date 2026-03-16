from __future__ import annotations

import time
from typing import List

from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .config import (
    DEFAULT_INTERVAL,
    DEFAULT_STABLE_SECONDS,
    DEFAULT_WATCH_EXTENSIONS,
    MAX_STABLE_SECONDS,
    MIN_STABLE_SECONDS,
)
from .monitor import FolderCheckerWorker, MonitorController
from .notifications import notify_completed, notify_started
from .presets import PresetData, load_preset, save_preset
from .styles import KBS_GREY_GRID, KBS_GREY_LIGHT, KBS_PURPLE_BLUE
from .ui_extensions_dialog import ExtensionsDialog


class MainWindow(QWidget):
    """
    파일 입고 모니터링 메인 윈도우.
    UI를 담당하고, MonitorController/Worker 와 연결한다.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("파일 입고 모니터링 시스템")
        self.resize(700, 600)

        self.watch_paths: List[str] = []
        self.start_time: float | None = None
        self._scanner_worker: FolderCheckerWorker | None = None

        # 상태/로직 컨트롤러
        self.monitor = MonitorController(stable_seconds=DEFAULT_STABLE_SECONDS)
        self.monitor.file_started.connect(self.on_file_started)
        self.monitor.file_completed.connect(self.on_file_completed)
        self.monitor.path_status_changed.connect(self.update_path_status)

        # 확장자 상태 (기본값: 예시 확장자 전체)
        self.active_extensions = set(DEFAULT_WATCH_EXTENSIONS)

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_scan)

        self._build_ui()

    # UI 구성 --------------------------------------------------------------

    def _build_ui(self) -> None:
        self.layout = QVBoxLayout()

        # 경로 테이블
        self.path_table = QTableWidget(0, 2)
        self.path_table.setShowGrid(True)
        self._apply_table_grid_style(self.path_table)
        self.path_table.setHorizontalHeaderLabels(["경로", "상태"])
        self.path_table.horizontalHeader().setSectionResizeMode(0, self.path_table.horizontalHeader().Stretch)
        self.layout.addWidget(QLabel("감시 중인 폴더:"))
        self.layout.addWidget(self.path_table)

        path_buttons = QHBoxLayout()
        for label, handler in [
            ("+ 폴더 추가", self.add_path),
            ("- 폴더 삭제", self.remove_selected_paths),
            ("💾 프리셋 저장", self.save_preset_clicked),
            ("📂 프리셋 불러오기", self.load_preset_clicked),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            path_buttons.addWidget(btn)
        self.layout.addLayout(path_buttons)

        # 감시 주기 / 안정 시간
        cycle_layout = QHBoxLayout()
        cycle_layout.addWidget(QLabel("감시 주기 (초):"))
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText(f"예: {DEFAULT_INTERVAL}")
        self.interval_input.setText(str(DEFAULT_INTERVAL))
        cycle_layout.addWidget(self.interval_input)
        self.layout.addLayout(cycle_layout)

        stable_layout = QHBoxLayout()
        stable_layout.addWidget(QLabel("입고 완료 판정 대기시간 (초):"))
        self.stable_input = QLineEdit()
        self.stable_input.setPlaceholderText(str(DEFAULT_STABLE_SECONDS))
        self.stable_input.setText(str(DEFAULT_STABLE_SECONDS))
        stable_layout.addWidget(self.stable_input)
        self.layout.addLayout(stable_layout)

        # 확장자 관리 버튼
        ext_btn = QPushButton("📋 확장자 관리")
        ext_btn.clicked.connect(self.open_extensions_dialog)
        self.layout.addWidget(ext_btn)

        # 시작/정지 버튼
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("감시 시작")
        self.stop_button = QPushButton("감시 정지")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        self.layout.addLayout(button_layout)

        # 입고 완료 리스트
        list_control = QHBoxLayout()
        list_control.addWidget(QLabel("입고 완료된 파일:"))
        clear_btn = QPushButton("초기화")
        clear_btn.clicked.connect(self.clear_completed_list)
        list_control.addWidget(clear_btn)
        self.layout.addLayout(list_control)

        self.completed_list = QTableWidget(0, 3)
        self.completed_list.setShowGrid(True)
        self._apply_table_grid_style(self.completed_list)
        self.completed_list.setHorizontalHeaderLabels(["파일명", "입고 시각", "상태"])
        self.completed_list.horizontalHeader().setSectionResizeMode(0, self.completed_list.horizontalHeader().Stretch)
        self.layout.addWidget(self.completed_list)

        self.setLayout(self.layout)

    def _apply_table_grid_style(self, table: QTableWidget) -> None:
        """테이블 그리드선 스타일 적용 (구분선이 보이도록)."""
        table.setStyleSheet(
            f"QTableWidget {{ background-color: white; border: 1px solid {KBS_GREY_LIGHT}; "
            f"border-radius: 6px; }} "
            f"QTableWidget::item {{ border-right: 1px solid {KBS_GREY_GRID}; "
            f"border-bottom: 1px solid {KBS_GREY_GRID}; padding: 6px; }} "
            f"QHeaderView::section {{ background-color: {KBS_PURPLE_BLUE}; color: white; "
            f"padding: 10px; font-weight: 600; border: 1px solid {KBS_GREY_GRID}; }}"
        )

    # 확장자 관련 ----------------------------------------------------------

    def open_extensions_dialog(self) -> None:
        dlg = ExtensionsDialog(self.active_extensions, self)
        if dlg.exec_():
            self.active_extensions = dlg.get_extensions()

    # 경로/프리셋 ----------------------------------------------------------

    def add_path(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "감시할 폴더 선택")
        if folder and folder not in self.watch_paths:
            self.watch_paths.append(folder)
            row = self.path_table.rowCount()
            self.path_table.insertRow(row)
            self.path_table.setItem(row, 0, QTableWidgetItem(folder))
            self.path_table.setItem(row, 1, QTableWidgetItem("대기 중"))

    def remove_selected_paths(self) -> None:
        rows = {idx.row() for idx in self.path_table.selectedIndexes()}
        for row in sorted(rows, reverse=True):
            item = self.path_table.item(row, 0)
            if not item:
                continue
            path = item.text()
            if path in self.watch_paths:
                self.watch_paths.remove(path)
            self.path_table.removeRow(row)

    def update_path_status(self, path: str, status: str) -> None:
        for row in range(self.path_table.rowCount()):
            item = self.path_table.item(row, 0)
            if item and item.text() == path:
                self.path_table.setItem(row, 1, QTableWidgetItem(status))
                break

    def save_preset_clicked(self) -> None:
        raw = self.interval_input.text()
        interval = int(raw) if raw.isdigit() else DEFAULT_INTERVAL
        preset = PresetData(
            paths=list(self.watch_paths),
            extensions=list(self.active_extensions),
            interval=interval,
        )
        save_preset(preset)
        QMessageBox.information(self, "저장됨", "프리셋이 저장되었습니다.")

    def load_preset_clicked(self) -> None:
        data = load_preset()
        if data is None:
            QMessageBox.warning(self, "없음", "프리셋 파일이 없습니다.")
            return
        self.watch_paths = list(data.paths)
        self.active_extensions = set(data.extensions) if data.extensions else set(DEFAULT_WATCH_EXTENSIONS)
        self.interval_input.setText(str(data.interval))

        self.path_table.setRowCount(0)
        for path in self.watch_paths:
            row = self.path_table.rowCount()
            self.path_table.insertRow(row)
            self.path_table.setItem(row, 0, QTableWidgetItem(path))
            self.path_table.setItem(row, 1, QTableWidgetItem("대기 중"))
        QMessageBox.information(self, "불러옴", "프리셋을 불러왔습니다.")

    # 감시 시작/정지 -------------------------------------------------------

    def start_monitoring(self) -> None:
        if not self.watch_paths:
            QMessageBox.warning(self, "경고", "감시할 폴더를 하나 이상 추가하세요.")
            return
        self.start_time = time.time()
        try:
            interval = max(1, int(self.interval_input.text()))
        except ValueError:
            QMessageBox.warning(self, "오류", "감시 주기는 숫자로 입력해야 합니다.")
            return

        try:
            stable_seconds = int(self.stable_input.text())
        except ValueError:
            stable_seconds = DEFAULT_STABLE_SECONDS
        stable_seconds = max(MIN_STABLE_SECONDS, min(MAX_STABLE_SECONDS, stable_seconds))
        self.monitor.reset(stable_seconds)

        self.completed_list.setRowCount(0)

        self._start_timer(interval)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        QMessageBox.information(self, "알림", "감시를 시작합니다.")
        for path in self.watch_paths:
            self.update_path_status(path, "감시 중")

    def _start_timer(self, interval: int) -> None:
        self.timer.stop()
        self.timer.start(interval * 1000)
        self.start_scan()

    def stop_monitoring(self) -> None:
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.information(self, "알림", "감시를 중지했습니다.")
        for path in self.watch_paths:
            self.update_path_status(path, "중지됨")

    def start_scan(self) -> None:
        if not self.watch_paths or not self.active_extensions:
            return
        if self._scanner_worker is not None and self._scanner_worker.isRunning():
            return
        self._scanner_worker = FolderCheckerWorker(
            self.watch_paths,
            list(self.active_extensions),
        )
        self._scanner_worker.files_found.connect(self.on_scan_result)
        self._scanner_worker.start()

    def on_scan_result(self, results: list) -> None:
        if self.start_time is None:
            return
        self.monitor.process_scan_results(results, self.start_time)

    # 파일 이벤트 핸들러 ---------------------------------------------------

    def on_file_started(self, mf) -> None:
        """MonitorController 가 파일 입고 시작을 통지하면 테이블에 반영하고 알림."""
        row = self.completed_list.rowCount()
        self.completed_list.insertRow(row)
        self.completed_list.setItem(row, 0, QTableWidgetItem(mf.name))
        self.completed_list.setItem(
            row,
            1,
            QTableWidgetItem(
                QDateTime.currentDateTime().toString("MM월 dd일 (ddd) HH:mm:ss")
            ),
        )
        self.completed_list.setItem(row, 2, QTableWidgetItem("입고 중"))
        mf.row_index = row
        notify_started(mf)

    def on_file_completed(self, mf) -> None:
        """입고 완료 이벤트가 발생하면 상태/스타일/알림 처리."""
        row = mf.row_index if mf.row_index is not None else self.completed_list.rowCount()
        if row == self.completed_list.rowCount():
            self.completed_list.insertRow(row)
            self.completed_list.setItem(row, 0, QTableWidgetItem(mf.name))
            self.completed_list.setItem(
                row,
                1,
                QTableWidgetItem(
                    QDateTime.currentDateTime().toString("MM월 dd일 (ddd) HH:mm:ss")
                ),
            )
        status_item = QTableWidgetItem("입고 완료")
        status_item.setForeground(Qt.red)
        status_item.setFont(QFont("", weight=QFont.Bold))
        self.completed_list.setItem(row, 2, status_item)
        mf.row_index = row
        notify_completed(mf)

    # 기타 ---------------------------------------------------------------

    def clear_completed_list(self) -> None:
        self.completed_list.setRowCount(0)

