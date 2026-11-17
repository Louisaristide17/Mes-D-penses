import logging
import sys

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from app import theme
from app.api import ApiClient
from app.config import API_URL, APP_NAME
from app.main_window import MainWindow


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    application = QApplication(sys.argv)
    application.setApplicationName(APP_NAME)
    # Calendriers et dates en français, quelle que soit la langue du système.
    QLocale.setDefault(QLocale(QLocale.Language.French, QLocale.Country.France))
    theme.load_fonts()
    application.setStyleSheet(theme.STYLESHEET)

    window = MainWindow(ApiClient(API_URL))
    window.start()
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
