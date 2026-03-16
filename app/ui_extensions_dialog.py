"""확장자 관리 다이얼로그: 아이콘 스타일 토글 + KBS CI 적용."""
from __future__ import annotations

from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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
from .styles import KBS_BLUE, KBS_GREY_DARK, get_extension_toggle_stylesheet


COLS = 4  # 확장자 토글 그리드 열 개수


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
        padding: 8px 20px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton#addBtn:hover {{
        background-color: #4DA3D1;
    }}
    QPushButton#delBtn {{
        background-color: rgba(200, 60, 60, 0.9);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
    }}
    QPushButton#delBtn:hover {{
        background-color: rgba(220, 80, 80, 1);
    }}
    """


class ExtensionItemWidget(QWidget):
    """토글 버튼 + 삭제(X) 버튼을 담는 위젯. 레이아웃 기반으로 안정적 동작."""

    def __init__(
        self,
        ext: str,
        checked: bool,
        on_toggle,
        on_delete,
        toggle_stylesheet: str,
        defer_delete: bool = False,
    ):
        super().__init__()
        self.ext = ext
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.toggle_btn = QPushButton(ext)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(checked)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(toggle_stylesheet)
        self.toggle_btn.toggled.connect(on_toggle)

        del_btn = QPushButton("✕")
        del_btn.setObjectName("delBtn")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFocusPolicy(Qt.NoFocus)
        if defer_delete:
            del_btn.clicked.connect(lambda: QTimer.singleShot(0, on_delete))
        else:
            del_btn.clicked.connect(on_delete)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        row.addWidget(self.toggle_btn, 1)
        row.addWidget(del_btn, 0)

    def setChecked(self, checked: bool) -> None:
        self.toggle_btn.setChecked(checked)


class ExtensionsDialog(QDialog):
    """감시할 확장자를 아이콘 스타일 토글로 관리하는 다이얼로그. KBS CI 적용."""

    def __init__(self, initial_extensions: set[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("감시할 확장자 관리")
        self.resize(480, 420)
        self.setStyleSheet(_dialog_stylesheet())

        self._result: set[str] = set(initial_extensions)
        self._example_items: dict[str, ExtensionItemWidget] = {}
        self._custom_items: dict[str, ExtensionItemWidget] = {}
        self._toggle_stylesheet = get_extension_toggle_stylesheet()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 예시 확장자 - 토글 + 삭제
        layout.addWidget(QLabel("예시 확장자 (클릭 시 선택/제외, ✕로 리스트에서 제거):"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        example_widget = QWidget()
        example_layout = QGridLayout(example_widget)
        example_layout.setSpacing(10)
        for i, ext in enumerate(DEFAULT_WATCH_EXTENSIONS):
            item = self._create_extension_item(
                ext, ext in self._result,
                lambda checked, e=ext: self._on_toggle(e, checked),
                lambda e=ext: self._on_delete_example(e),
            )
            example_layout.addWidget(item, i // COLS, i % COLS)
            self._example_items[ext] = item
        scroll.setWidget(example_widget)
        layout.addWidget(scroll)

        # 직접 추가
        layout.addWidget(QLabel("예시에 없는 경우 직접 추가:"))
        add_row = QHBoxLayout()
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText("예: .webm")
        self.ext_input.installEventFilter(self)
        add_btn = QPushButton("추가")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(self._add_custom)
        add_row.addWidget(self.ext_input)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        # 직접 추가된 확장자
        self.custom_container = QWidget()
        self.custom_layout = QGridLayout(self.custom_container)
        self.custom_layout.setSpacing(10)
        layout.addWidget(self.custom_container)
        custom_exts = sorted(e for e in self._result if e not in DEFAULT_WATCH_EXTENSIONS)
        for i, ext in enumerate(custom_exts):
            item = self._create_extension_item(
                ext, True,
                lambda checked, e=ext: self._on_toggle(e, checked),
                lambda e=ext: self._on_delete_custom(e),
                defer_delete=True,
            )
            self._custom_layout.addWidget(item, i // COLS, i % COLS)
            self._custom_items[ext] = item

        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def eventFilter(self, obj, event):
        """Enter 키가 다이얼로그 기본버튼(OK)으로 전달되지 않도록 처리."""
        if obj is self.ext_input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._add_custom()
                return True
        return super().eventFilter(obj, event)

    def _create_extension_item(
        self, ext: str, checked: bool, on_toggle, on_delete, defer_delete: bool = False
    ) -> ExtensionItemWidget:
        """토글 + 삭제 버튼이 있는 확장자 아이템 생성."""
        return ExtensionItemWidget(
            ext, checked, on_toggle, on_delete, self._toggle_stylesheet, defer_delete
        )

    def _on_toggle(self, ext: str, checked: bool) -> None:
        if checked:
            self._result.add(ext)
        else:
            self._result.discard(ext)

    def _on_delete_example(self, ext: str) -> None:
        """예시 확장자 삭제 = 리스트에서 제외."""
        self._result.discard(ext)
        self._example_items[ext].setChecked(False)

    def _on_delete_custom(self, ext: str) -> None:
        """직접 추가 확장자 삭제 = 위젯 제거."""
        self._result.discard(ext)
        item = self._custom_items.pop(ext, None)
        if item:
            item.setParent(None)
            self._custom_layout.removeWidget(item)
            item.deleteLater()

    def _add_custom(self) -> None:
        text = self.ext_input.text()
        norm = _normalize_ext(text)
        if not norm:
            return
        if norm in DEFAULT_WATCH_EXTENSIONS:
            self._example_items[norm].setChecked(True)
        elif norm not in self._custom_items:
            self._result.add(norm)
            item = self._create_extension_item(
                norm, True,
                lambda checked, e=norm: self._on_toggle(e, checked),
                lambda e=norm: self._on_delete_custom(e),
                defer_delete=True,
            )
            idx = len(self._custom_items)
            self._custom_layout.addWidget(item, idx // COLS, idx % COLS)
            self._custom_items[norm] = item
        self.ext_input.clear()

    def get_extensions(self) -> set[str]:
        """적용된 확장자 집합 반환."""
        return set(self._result)
