from __future__ import annotations

import time
from typing import List

from PyQt5.QtCore import QDateTime, Qt
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
    QCheckBox,
)

from .config import (
    DEFAULT_INTERVAL,
    DEFAULT_STABLE_SECONDS,
    MAX_STABLE_SECONDS,
    MIN_STABLE_SECONDS,
)
from .monitor import FolderCheckerWorker, MonitorController
from .notifications import notify_completed, notify_started
from .presets import PresetData, load_preset, save_preset


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

        # 알림음 경로
        self.sound_path_mxf = ""
        self.sound_path_mov = ""
        self.sound_path_xmp = ""

        # 확장자 상태
        self.active_extensions = set()

        self._build_ui()

    # UI 구성 --------------------------------------------------------------

    def _build_ui(self) -> None:
        self.layout = QVBoxLayout()

        # 경로 테이블
        self.path_table = QTableWidget(0, 2)
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

        # 알림음 설정 (기본 구조만 유지)
        self.sound_input_mxf = QLineEdit()
        self.sound_input_mov = QLineEdit()
        self.sound_input_xmp = QLineEdit()
        for w in (self.sound_input_mxf, self.sound_input_mov, self.sound_input_xmp):
            w.setReadOnly(True)

        self.toggle_sound_button = QPushButton("🔊 알림음 설정 열기")
        self.toggle_sound_button.setCheckable(True)
        self.toggle_sound_button.setChecked(False)
        self.toggle_sound_button.toggled.connect(self.toggle_sound_section)
        self.layout.addWidget(self.toggle_sound_button)

        self.sound_section_widget = QWidget()
        self.sound_section_layout = QVBoxLayout()
        self.sound_section_widget.setLayout(self.sound_section_layout)
        self.sound_section_widget.setVisible(False)

        for label, input_field, attr in [
            ("MXF 알림음 파일:", self.sound_input_mxf, "sound_path_mxf"),
            ("MOV 알림음 파일:", self.sound_input_mov, "sound_path_mov"),
            ("XMP 알림음 파일:", self.sound_input_xmp, "sound_path_xmp"),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(input_field)
            btn = QPushButton("선택")
            btn.clicked.connect(lambda _, i=input_field, a=attr: self.select_sound(i, a))
            row.addWidget(btn)
            self.sound_section_layout.addLayout(row)

        self.layout.addWidget(self.sound_section_widget)

        # 확장자 UI
        self.extensions_layout = QVBoxLayout()
        self.layout.addWidget(QLabel("감시할 확장자:"))
        self.extensions_container = QWidget()
        self.extensions_container.setLayout(self.extensions_layout)
        self.layout.addWidget(self.extensions_container)

        self.extension_checkboxes: dict[str, QCheckBox] = {}
        # active_extensions 는 외부에서 세팅할 수 있지만, 여기서는 비워두고
        # 프리셋/설정에서 채우도록 한다.

        add_ext_layout = QHBoxLayout()
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText(".webm")
        add_ext_layout.addWidget(self.ext_input)
        add_ext_btn = QPushButton("확장자 추가")
        add_ext_btn.clicked.connect(self.add_extension)
        add_ext_layout.addWidget(add_ext_btn)
        self.layout.addLayout(add_ext_layout)

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
        self.completed_list.setHorizontalHeaderLabels(["파일명", "입고 시각", "상태"])
        self.completed_list.horizontalHeader().setSectionResizeMode(0, self.completed_list.horizontalHeader().Stretch)
        self.layout.addWidget(self.completed_list)

        self.setLayout(self.layout)

    # 확장자 관련 ----------------------------------------------------------

    def _normalize_extension(self, ext: str) -> str:
        ext = ext.strip().lower()
        if not ext:
            return ""
        if not ext.startswith("."):
            ext = "." + ext
        return ext

    def _add_extension_checkbox(self, ext: str, checked: bool = True) -> None:
        norm_ext = self._normalize_extension(ext)
        if not norm_ext:
            return
        if norm_ext in self.extension_checkboxes:
            cb = self.extension_checkboxes[norm_ext]
            cb.setChecked(checked)
        else:
            cb = QCheckBox(norm_ext)
            cb.setChecked(checked)
            cb.toggled.connect(lambda state, e=norm_ext: self.on_extension_toggled(e, state))
            self.extensions_layout.addWidget(cb)
            self.extension_checkboxes[norm_ext] = cb
        if checked:
            self.active_extensions.add(norm_ext)
        else:
            self.active_extensions.discard(norm_ext)

    def on_extension_toggled(self, ext: str, checked: bool) -> None:
        if checked:
            self.active_extensions.add(ext)
        else:
            self.active_extensions.discard(ext)

    def add_extension(self) -> None:
        text = self.ext_input.text()
        norm_ext = self._normalize_extension(text)
        if not norm_ext:
            return
        self._add_extension_checkbox(norm_ext, checked=True)
        self.ext_input.clear()

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
            sound_mxf=self.sound_path_mxf,
            sound_mov=self.sound_path_mov,
            sound_xmp=self.sound_path_xmp,
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
        self.sound_path_mxf = data.sound_mxf
        self.sound_path_mov = data.sound_mov
        self.sound_path_xmp = data.sound_xmp
        self.sound_input_mxf.setText(self.sound_path_mxf)
        self.sound_input_mov.setText(self.sound_path_mov)
        self.sound_input_xmp.setText(self.sound_path_xmp)
        self.interval_input.setText(str(data.interval))

        self.path_table.setRowCount(0)
        for path in self.watch_paths:
            row = self.path_table.rowCount()
            self.path_table.insertRow(row)
            self.path_table.setItem(row, 0, QTableWidgetItem(path))
            self.path_table.setItem(row, 1, QTableWidgetItem("대기 중"))
        QMessageBox.information(self, "불러옴", "프리셋을 불러왔습니다.")

    # 알림음/토글 ----------------------------------------------------------

    def toggle_sound_section(self, checked: bool) -> None:
        self.sound_section_widget.setVisible(checked)
        self.toggle_sound_button.setText("🔊 알림음 설정 닫기" if checked else "🔊 알림음 설정 열기")

    def select_sound(self, input_field: QLineEdit, attr_name: str) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "알림음 파일 선택", "", "WAV 파일 (*.wav)")
        if file:
            setattr(self, attr_name, file)
            input_field.setText(file)

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
        # 타이머는 MainWindow 외부에서 생성되므로,
        # 기존 구조와의 호환을 위해 간단히 QTimer를 재사용하려면
        # main.py 에서 QTimer를 연결하는 방식으로도 확장 가능하다.
        # 여기서는 interval 값만 보관하고, 스캔은 start_scan 에서 처리.
        self._scan_interval_sec = interval  # type: ignore[attr-defined]
        # 실제 QTimer 설정은 main.py 혹은 기존 구조에서 담당.

    def stop_monitoring(self) -> None:
        # 외부 타이머를 사용하는 구조라면 여기서는 버튼 상태/표시만 관리.
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        QMessageBox.information(self, "알림", "감시를 중지했습니다.")
        for path in self.watch_paths:
            self.update_path_status(path, "중지됨")

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
        notify_started(mf, self.sound_path_mxf)

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
        notify_completed(mf, self.sound_path_mxf)

    # 기타 ---------------------------------------------------------------

    def clear_completed_list(self) -> None:
        self.completed_list.setRowCount(0)

