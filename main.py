import sys

from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication

from app.config import KBS_CI_FONT
from app.styles import get_global_stylesheet
from app.ui_main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    if KBS_CI_FONT:
        QFontDatabase.addApplicationFont(KBS_CI_FONT)
    app.setStyleSheet(get_global_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

