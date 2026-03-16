from __future__ import annotations

import time
from typing import List

from PyQt5.QtCore import QDateTime, QEvent, QPoint, Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from .config import (
    DEFAULT_INTERVAL,
    DEFAULT_STABLE_SECONDS,
    DEFAULT_WATCH_EXTENSIONS,
    MAX_STABLE_SECONDS,
    MIN_STABLE_SECONDS,
    get_resource_path,
)
from .monitor import FolderCheckerWorker, MonitorController
from .notifications import notify_completed, notify_started
from .presets import PresetData, load_preset, save_preset
from .styles import KBS_GREY_GRID, KBS_GREY_LIGHT, KBS_PURPLE_BLUE
from .ui_extensions_dialog import ExtensionsDialog


class MainWindow(QWidget):
    """파일 입고 모니터링 메인 윈도우."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("File Monitor App")
        self.setWindowIcon(QIcon(get_resource_path("MXFMonitorApp.ico")))
        self.resize(980, 660)

        self.watch_paths: List[str] = []
        self.start_time: float | None = None
        self._scanner_worker: FolderCheckerWorker | None = None

        self.monitor = MonitorController(stable_seconds=DEFAULT_STABLE_SECONDS)
        self.monitor.file_started.connect(self.on_file_started)
        self.monitor.file_completed.connect(self.on_file_completed)
        self.monitor.path_status_changed.connect(self.update_path_status)

        self.active_extensions = set(DEFAULT_WATCH_EXTENSIONS)
        self.interval_seconds = DEFAULT_INTERVAL
        self.stable_seconds = DEFAULT_STABLE_SECONDS
        self.is_monitoring = False

        self.help_tooltips_enabled = True
        self._tooltip_target: QWidget | None = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.start_scan)

        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.timeout.connect(self._show_delayed_tooltip)

        self._build_ui()

    def _build_ui(self) -> None:
        self.layout = QHBoxLayout()
        self.layout.setSpacing(14)

        # 좌측: 표 영역
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)

        path_title = self._create_table_title("감시 중인 폴더")
        path_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_panel.addWidget(path_title)

        self.path_table = QTableWidget(0, 2)
        self.path_table.setShowGrid(True)
        self._apply_table_grid_style(self.path_table)
        self.path_table.setHorizontalHeaderLabels(["경로", "상태"])
        self.path_table.horizontalHeader().setSectionResizeMode(
            0, self.path_table.horizontalHeader().Stretch
        )
        left_panel.addWidget(self.path_table, 1)

        completed_title = self._create_table_title("입고 완료된 파일")
        completed_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_panel.addWidget(completed_title)

        self.completed_list = QTableWidget(0, 3)
        self.completed_list.setShowGrid(True)
        self._apply_table_grid_style(self.completed_list)
        self.completed_list.setHorizontalHeaderLabels(["파일명", "입고 시각", "상태"])
        self.completed_list.horizontalHeader().setSectionResizeMode(
            0, self.completed_list.horizontalHeader().Stretch
        )
        left_panel.addWidget(self.completed_list, 1)

        # 우측: 컨트롤 영역
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)

        control_row = QHBoxLayout()
        control_row.setSpacing(6)

        self.interval_button = QPushButton()
        self.interval_button.clicked.connect(self.select_interval_seconds)
        self.interval_button.setMinimumWidth(140)
        self.interval_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        control_row.addWidget(self.interval_button, 1)

        self.stable_button = QPushButton()
        self.stable_button.clicked.connect(self.select_stable_seconds)
        self.stable_button.setMinimumWidth(140)
        self.stable_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        control_row.addWidget(self.stable_button, 1)

        right_panel.addLayout(control_row)
        self._refresh_setting_buttons()

        self.monitor_toggle_button = QPushButton("▶ 감시 시작")
        self.monitor_toggle_button.setObjectName("startMonitorButton")
        self.monitor_toggle_button.clicked.connect(self.toggle_monitoring)
        right_panel.addWidget(self.monitor_toggle_button)

        path_action_row = QHBoxLayout()
        path_action_row.setSpacing(6)

        self.add_path_button = QPushButton("➕📁 폴더 추가")
        self.add_path_button.setObjectName("grayActionButton")
        self.add_path_button.clicked.connect(self.add_path)
        path_action_row.addWidget(self.add_path_button)

        self.remove_path_button = QPushButton("➖📁 폴더 삭제")
        self.remove_path_button.setObjectName("grayActionButton")
        self.remove_path_button.clicked.connect(self.remove_selected_paths)
        path_action_row.addWidget(self.remove_path_button)
        right_panel.addLayout(path_action_row)

        manage_row = QHBoxLayout()
        manage_row.setSpacing(6)

        self.ext_button = QPushButton("🧩 확장자 관리")
        self.ext_button.clicked.connect(self.open_extensions_dialog)
        manage_row.addWidget(self.ext_button)

        self.clear_button = QPushButton("🧹 목록 초기화")
        self.clear_button.clicked.connect(self.clear_completed_list)
        manage_row.addWidget(self.clear_button)
        right_panel.addLayout(manage_row)

        right_panel.addStretch()

        self.help_toggle_button = QPushButton("❓ 도움말 ON")
        self.help_toggle_button.setObjectName("helpToggleButton")
        self.help_toggle_button.setCheckable(True)
        self.help_toggle_button.setChecked(True)
        self.help_toggle_button.clicked.connect(self.toggle_help_tooltips)
        right_panel.addWidget(self.help_toggle_button)

        self.save_preset_button = QPushButton("💾 프리셋 저장")
        self.save_preset_button.clicked.connect(self.save_preset_clicked)
        right_panel.addWidget(self.save_preset_button)

        self.load_preset_button = QPushButton("📂 프리셋 불러오기")
        self.load_preset_button.clicked.connect(self.load_preset_clicked)
        right_panel.addWidget(self.load_preset_button)

        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_container = QWidget()
        right_container.setLayout(right_panel)
        right_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        right_container.setFixedWidth(360)

        self.layout.addWidget(left_container, 1)
        self.layout.addWidget(right_container, 0)
        self.setLayout(self.layout)

        self._setup_button_tooltips()

    def _create_table_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("tableTitle")
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        return label

    def _refresh_setting_buttons(self) -> None:
        self.interval_button.setText(f"주기 {self.interval_seconds}초")
        self.stable_button.setText(f"대기 {self.stable_seconds}초")

    def toggle_help_tooltips(self, checked: bool) -> None:
        self.help_tooltips_enabled = checked
        self.help_toggle_button.setText("❓ 도움말 ON" if checked else "❓ 도움말 OFF")
        if not checked:
            self._tooltip_target = None
            self._tooltip_timer.stop()
            QToolTip.hideText()

    def _setup_button_tooltips(self) -> None:
        self.help_toggle_button.setToolTip("버튼별 기능 안내를 받고 싶으면 클릭하세요.")
        button_tips = {
            self.monitor_toggle_button: "클릭하면 감시 시작/정지가 전환됩니다.",
            self.add_path_button: "감시할 폴더를 추가합니다.",
            self.remove_path_button: "선택한 폴더를 목록에서 삭제합니다.",
            self.interval_button: "감시 주기(초)를 설정합니다.",
            self.stable_button: "입고 완료 판정 대기시간(초)를 설정합니다.",
            self.ext_button: "감시할 확장자 목록을 편집합니다.",
            self.clear_button: "입고 완료 목록을 비웁니다.",
            self.save_preset_button: "감시 폴더 경로, 확장자 목록, 감시 주기를 프리셋에 저장합니다.",
            self.load_preset_button: "저장된 프리셋을 불러옵니다.",
        }
        for button, tip in button_tips.items():
            button.setToolTip(tip)
            button.installEventFilter(self)
        self.help_toggle_button.installEventFilter(self)

    def eventFilter(self, obj, event):
        if isinstance(obj, QPushButton):
            if event.type() == QEvent.ToolTip:
                # 도움말 OFF 시에는 도움말 토글 버튼 외 모든 툴팁 차단
                if obj is not self.help_toggle_button and not self.help_tooltips_enabled:
                    return True
            if event.type() == QEvent.Enter:
                if obj is self.help_toggle_button or self.help_tooltips_enabled:
                    self._tooltip_target = obj
                    self._tooltip_timer.start(1000)
            elif event.type() in (QEvent.Leave, QEvent.MouseButtonPress):
                if self._tooltip_target is obj:
                    self._tooltip_target = None
                self._tooltip_timer.stop()
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def _show_delayed_tooltip(self) -> None:
        if self._tooltip_target is None:
            return
        text = self._tooltip_target.toolTip()
        if not text:
            return
        pos = self._tooltip_target.mapToGlobal(
            QPoint(self._tooltip_target.width() // 2, self._tooltip_target.height())
        )
        QToolTip.showText(pos, text, self._tooltip_target)

    def select_interval_seconds(self) -> None:
        value, ok = QInputDialog.getInt(
            self,
            "감시 주기 설정",
            "감시 주기(초):",
            self.interval_seconds,
            1,
            3600,
            1,
        )
        if ok:
            self.interval_seconds = value
            self._refresh_setting_buttons()

    def select_stable_seconds(self) -> None:
        value, ok = QInputDialog.getInt(
            self,
            "입고 완료 판정 대기시간 설정",
            "대기시간(초):",
            self.stable_seconds,
            MIN_STABLE_SECONDS,
            MAX_STABLE_SECONDS,
            1,
        )
        if ok:
            self.stable_seconds = value
            self._refresh_setting_buttons()

    def _apply_table_grid_style(self, table: QTableWidget) -> None:
        # 행 번호(세로 헤더) 가림 현상을 막기 위해 폭/정렬을 명시한다.
        table.verticalHeader().setMinimumWidth(44)
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        table.setStyleSheet(
            f"QTableWidget {{ background-color: white; border: 1px solid {KBS_GREY_LIGHT}; "
            f"border-radius: 6px; }} "
            f"QTableWidget::item {{ border-right: 1px solid {KBS_GREY_GRID}; "
            f"border-bottom: 1px solid {KBS_GREY_GRID}; padding: 6px; }} "
            f"QHeaderView::section:horizontal {{ background-color: {KBS_PURPLE_BLUE}; color: white; "
            f"padding: 10px; font-weight: 600; border: 1px solid {KBS_GREY_GRID}; }}"
            f"QHeaderView::section:vertical {{ background-color: {KBS_PURPLE_BLUE}; color: white; "
            f"padding: 2px; font-weight: 600; border: 1px solid {KBS_GREY_GRID}; text-align: center; }}"
        )

    # 확장자 ---------------------------------------------------------------

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
        preset = PresetData(
            paths=list(self.watch_paths),
            extensions=list(self.active_extensions),
            interval=self.interval_seconds,
        )
        try:
            save_preset(preset)
        except OSError as exc:
            QMessageBox.critical(
                self,
                "저장 실패",
                f"프리셋 저장 중 파일 접근 오류가 발생했습니다.\n{exc}",
            )
            return
        QMessageBox.information(self, "저장됨", "프리셋이 저장되었습니다.")

    def load_preset_clicked(self) -> None:
        try:
            data = load_preset()
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "불러오기 실패",
                f"프리셋 파일을 읽는 중 오류가 발생했습니다.\n{exc}",
            )
            return
        if data is None:
            QMessageBox.warning(self, "없음", "프리셋 파일이 없습니다.")
            return
        self.watch_paths = list(data.paths)
        self.active_extensions = (
            set(data.extensions) if data.extensions else set(DEFAULT_WATCH_EXTENSIONS)
        )
        self.interval_seconds = int(data.interval)
        self._refresh_setting_buttons()

        self.path_table.setRowCount(0)
        for path in self.watch_paths:
            row = self.path_table.rowCount()
            self.path_table.insertRow(row)
            self.path_table.setItem(row, 0, QTableWidgetItem(path))
            self.path_table.setItem(row, 1, QTableWidgetItem("대기 중"))
        QMessageBox.information(self, "불러옴", "프리셋을 불러왔습니다.")

    # 감시 시작/정지 -------------------------------------------------------

    def toggle_monitoring(self) -> None:
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self) -> None:
        if not self.watch_paths:
            self._show_center_warning("경고", "감시할 폴더를 하나 이상 추가하세요.")
            return
        self.start_time = time.time()
        interval = max(1, self.interval_seconds)
        stable_seconds = max(MIN_STABLE_SECONDS, min(MAX_STABLE_SECONDS, self.stable_seconds))
        self.monitor.reset(stable_seconds)

        self.completed_list.setRowCount(0)
        self._start_timer(interval)

        self.is_monitoring = True
        self.monitor_toggle_button.setText("⏹ 감시 정지")
        self.interval_button.setEnabled(False)
        self.stable_button.setEnabled(False)

        QMessageBox.information(self, "알림", "감시를 시작합니다.")
        for path in self.watch_paths:
            self.update_path_status(path, "감시 중")

    def _start_timer(self, interval: int) -> None:
        self.timer.stop()
        self.timer.start(interval * 1000)
        self.start_scan()

    def stop_monitoring(self) -> None:
        self.timer.stop()
        self.is_monitoring = False
        self.monitor_toggle_button.setText("▶ 감시 시작")
        self.interval_button.setEnabled(True)
        self.stable_button.setEnabled(True)
        QMessageBox.information(self, "알림", "감시를 중지했습니다.")
        for path in self.watch_paths:
            self.update_path_status(path, "중지됨")

    def _show_center_warning(self, title: str, message: str) -> None:
        """경고창 문구/버튼 정렬을 일정하게 보여준다."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(title)
        box.setText(f"<div style='text-align:center; min-width:260px;'>{message}</div>")
        box.setStandardButtons(QMessageBox.Ok)
        box.exec_()

    def start_scan(self) -> None:
        if not self.watch_paths or not self.active_extensions:
            return
        if self._scanner_worker is not None and self._scanner_worker.isRunning():
            return
        self._scanner_worker = FolderCheckerWorker(self.watch_paths, list(self.active_extensions))
        self._scanner_worker.files_found.connect(self.on_scan_result)
        self._scanner_worker.start()

    def on_scan_result(self, results: list) -> None:
        if self.start_time is None:
            return
        self.monitor.process_scan_results(results, self.start_time)

    # 파일 이벤트 ----------------------------------------------------------

    def on_file_started(self, mf) -> None:
        row = self.completed_list.rowCount()
        self.completed_list.insertRow(row)
        self.completed_list.setItem(row, 0, QTableWidgetItem(mf.path))
        self.completed_list.setItem(
            row,
            1,
            QTableWidgetItem(QDateTime.currentDateTime().toString("MM월 dd일 (ddd) HH:mm:ss")),
        )
        self.completed_list.setItem(row, 2, QTableWidgetItem("입고 중"))
        mf.row_index = row
        notify_started(mf)

    def on_file_completed(self, mf) -> None:
        row = mf.row_index if mf.row_index is not None else self.completed_list.rowCount()
        if row == self.completed_list.rowCount():
            self.completed_list.insertRow(row)
            self.completed_list.setItem(row, 0, QTableWidgetItem(mf.path))
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

    def clear_completed_list(self) -> None:
        self.completed_list.setRowCount(0)

