"""확장자 관리 다이얼로그: 단일 리스트(기본/추가 통합) 관리."""
from __future__ import annotations

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .config import DEFAULT_WATCH_EXTENSIONS
from .styles import KBS_BLUE, KBS_GREY_DARK, KBS_GREY_LIGHT


COLS = 3


def _normalize_ext(ext: str) -> str:
    ext = ext.strip().lower()
    if not ext:
        return ""
    if not ext.startswith("."):
        ext = "." + ext
    return ext


def _dialog_stylesheet() -> str:
    return f"""
    QDialog {{
        background-color: #F5F7FA;
    }}
    QLabel {{
        color: {KBS_GREY_DARK};
        font-size: 13px;
        font-weight: 500;
    }}
    QLabel#sectionTitle {{
        font-family: "KBS_CI", "Segoe UI", "Malgun Gothic", sans-serif;
        font-size: 16px;
        font-weight: 700;
    }}
    QLineEdit {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border-color: {KBS_BLUE};
    }}
    QPushButton#addBtn {{
        background-color: {KBS_BLUE};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0px 16px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton#addBtn:hover {{
        background-color: #4DA3D1;
    }}
    QPushButton#delBtn {{
        background-color: rgba(200, 60, 60, 0.92);
        color: white;
        border: none;
        border-radius: 9px;
        padding: 0px;
    }}
    QPushButton#delBtn:hover {{
        background-color: rgba(220, 80, 80, 1);
    }}
    QPushButton#extToggleBtn {{
        background-color: white;
        color: #5A5A5A;
        border: 1px solid {KBS_GREY_LIGHT};
        border-radius: 10px;
        padding: 5px 10px;
        font-size: 12px;
        min-height: 30px;
    }}
    QPushButton#extToggleBtn:hover {{
        border-color: {KBS_BLUE};
        color: {KBS_BLUE};
    }}
    QPushButton#extToggleBtn:checked {{
        background-color: {KBS_BLUE};
        color: white;
        border-color: {KBS_BLUE};
        font-weight: 600;
    }}
    QPushButton#extToggleBtn:checked:hover {{
        background-color: #4DA3D1;
        border-color: #4DA3D1;
    }}
    QWidget#listFrame {{
        border: 1px solid #DDE3EB;
        border-radius: 8px;
        background: rgba(255,255,255,0.55);
    }}
    QPushButton#okBtn, QPushButton#cancelBtn {{
        min-height: 38px;
        font-size: 13px;
        border-radius: 6px;
    }}
    """


class ExtensionItemWidget(QWidget):
    """토글 + 삭제(X) 한 쌍."""

    def __init__(self, ext: str, checked: bool, on_toggle, on_delete):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.toggle_btn = QPushButton(ext)
        self.toggle_btn.setObjectName("extToggleBtn")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(checked)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.toggled.connect(on_toggle)

        del_btn = QPushButton("✕")
        del_btn.setObjectName("delBtn")
        del_btn.setFixedSize(24, 24)
        del_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFocusPolicy(Qt.NoFocus)
        del_btn.clicked.connect(lambda: QTimer.singleShot(0, on_delete))

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(self.toggle_btn, 1)
        row.addWidget(del_btn, 0, Qt.AlignVCenter)

    def setChecked(self, checked: bool) -> None:
        self.toggle_btn.setChecked(checked)


class ExtensionsDialog(QDialog):
    """감시 확장자 단일 리스트를 편집하는 다이얼로그."""

    def __init__(self, initial_extensions: set[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("감시할 확장자 관리")
        self.resize(560, 430)
        self.setStyleSheet(_dialog_stylesheet())

        self._result: set[str] = set(initial_extensions) or set(DEFAULT_WATCH_EXTENSIONS)
        self._items: dict[str, ExtensionItemWidget] = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("감시 확장자 (토글=포함/제외, ✕=리스트 삭제):")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        list_widget = QWidget()
        list_widget.setObjectName("listFrame")
        self.list_layout = QGridLayout(list_widget)
        self.list_layout.setHorizontalSpacing(12)
        self.list_layout.setVerticalSpacing(10)
        self.list_layout.setContentsMargins(12, 12, 12, 12)
        scroll.setWidget(list_widget)
        layout.addWidget(scroll)

        for ext in sorted(self._result):
            self._insert_item(ext, checked=True)

        add_title = QLabel("예시에 없는 경우 직접 추가:")
        add_title.setObjectName("sectionTitle")
        layout.addWidget(add_title)
        add_row = QHBoxLayout()
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText("예: .webm")
        self.ext_input.installEventFilter(self)
        add_btn = QPushButton("추가")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(lambda: QTimer.singleShot(0, self._add_custom))
        add_btn.setFixedHeight(self.ext_input.sizeHint().height())
        add_row.addWidget(self.ext_input, 1)
        add_row.addWidget(add_btn, 0)
        layout.addLayout(add_row)

        buttons_row = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("okBtn")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_row.addWidget(self.ok_btn, 1)
        buttons_row.addWidget(self.cancel_btn, 1)
        layout.addLayout(buttons_row)

    def eventFilter(self, obj, event):
        if obj is self.ext_input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                QTimer.singleShot(0, self._add_custom)
                return True
        return super().eventFilter(obj, event)

    def _insert_item(self, ext: str, checked: bool) -> None:
        item = ExtensionItemWidget(
            ext,
            checked,
            lambda state, e=ext: self._on_toggle(e, state),
            lambda e=ext: self._on_delete(e),
        )
        idx = len(self._items)
        self.list_layout.addWidget(item, idx // COLS, idx % COLS)
        self._items[ext] = item

    def _on_toggle(self, ext: str, checked: bool) -> None:
        if checked:
            self._result.add(ext)
        else:
            self._result.discard(ext)

    def _on_delete(self, ext: str) -> None:
        self._result.discard(ext)
        item = self._items.pop(ext, None)
        if not item:
            return
        self.list_layout.removeWidget(item)
        item.setParent(None)
        item.deleteLater()
        self._reflow_items()

    def _add_custom(self) -> None:
        norm = _normalize_ext(self.ext_input.text())
        if not norm:
            return
        if norm in self._items:
            self._items[norm].setChecked(True)
            self._result.add(norm)
        else:
            self._result.add(norm)
            self._insert_item(norm, checked=True)
        self.ext_input.clear()

    def _reflow_items(self) -> None:
        for i, item in enumerate(self._items.values()):
            self.list_layout.addWidget(item, i // COLS, i % COLS)

    def get_extensions(self) -> set[str]:
        return set(self._result)
