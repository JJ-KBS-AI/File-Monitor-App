"""KBS CI 기반 GUI 스타일."""
from __future__ import annotations

# KBS 공식 CI 색상 (RGB)
KBS_PURPLE_BLUE = "#09003E"   # rgb(9, 0, 62)
KBS_BLUE = "#2282B9"          # rgb(34, 130, 185)
KBS_ORANGE = "#FF9C00"        # rgb(255, 156, 0)

# 보조 색상
KBS_BLUE_LIGHT = "#4DA3D1"
KBS_BLUE_DARK = "#1A6B99"
KBS_ORANGE_LIGHT = "#FFB133"
KBS_ORANGE_DARK = "#E58C00"
KBS_GREY_DARK = "#2C2C2C"
KBS_GREY_MID = "#5A5A5A"
KBS_GREY_LIGHT = "#E8E8E8"
KBS_GREY_GRID = "#B8BCC4"  # 테이블 그리드선 (구분선이 보이도록)
KBS_BG = "#F5F7FA"


def get_global_stylesheet() -> str:
    """메인 윈도우 및 앱 전체 스타일시트."""
    return f"""
    QWidget {{
        background-color: {KBS_BG};
        font-family: "Segoe UI", "Malgun Gothic", sans-serif;
    }}
    QLabel {{
        color: {KBS_GREY_DARK};
        font-size: 13px;
    }}
    QLabel#tableTitle {{
        background-color: transparent;
        color: {KBS_PURPLE_BLUE};
        font-family: "KBS_CI", "Segoe UI", "Malgun Gothic", sans-serif;
        padding: 8px 0 10px 0;
        border: none;
        border-bottom: 2px solid {KBS_GREY_GRID};
        font-size: 22px;
        font-weight: 700;
    }}
    QPushButton {{
        background-color: {KBS_BLUE};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        min-height: 42px;
    }}
    QPushButton:hover {{
        background-color: {KBS_BLUE_LIGHT};
    }}
    QPushButton:pressed {{
        background-color: {KBS_BLUE_DARK};
    }}
    QPushButton#startMonitorButton {{
        background-color: {KBS_ORANGE};
    }}
    QPushButton#startMonitorButton:hover {{
        background-color: {KBS_ORANGE_LIGHT};
    }}
    QPushButton#startMonitorButton:pressed {{
        background-color: {KBS_ORANGE_DARK};
    }}
    QPushButton#grayActionButton {{
        background-color: #9A9A9A;
    }}
    QPushButton#grayActionButton:hover {{
        background-color: #A8A8A8;
    }}
    QPushButton#grayActionButton:pressed {{
        background-color: #8A8A8A;
    }}
    QPushButton:disabled {{
        background-color: {KBS_GREY_LIGHT};
        color: {KBS_GREY_MID};
    }}
    QLineEdit {{
        background-color: white;
        border: 1px solid {KBS_GREY_LIGHT};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border-color: {KBS_BLUE};
    }}
    QTableWidget {{
        background-color: white;
        border: 1px solid {KBS_GREY_LIGHT};
        border-radius: 6px;
    }}
    QTableWidget::item {{
        padding: 6px;
        border-right: 1px solid {KBS_GREY_GRID};
        border-bottom: 1px solid {KBS_GREY_GRID};
    }}
    QHeaderView::section {{
        background-color: {KBS_PURPLE_BLUE};
        color: white;
        padding: 10px;
        font-weight: 600;
        border: 1px solid {KBS_GREY_GRID};
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QDialog {{
        background-color: {KBS_BG};
    }}
    """


def get_extension_toggle_stylesheet() -> str:
    """확장자 토글 버튼 스타일 (checked=선택, unchecked=제외)."""
    return f"""
        QPushButton {{
            background-color: white;
            color: {KBS_GREY_MID};
            border: 2px solid {KBS_GREY_LIGHT};
            border-radius: 12px;
            padding: 10px 18px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            border-color: {KBS_BLUE};
            color: {KBS_BLUE};
        }}
        QPushButton:checked {{
            background-color: {KBS_BLUE};
            color: white;
            border-color: {KBS_BLUE};
            font-weight: 600;
        }}
        QPushButton:checked:hover {{
            background-color: {KBS_BLUE_LIGHT};
            border-color: {KBS_BLUE_LIGHT};
        }}
    """
