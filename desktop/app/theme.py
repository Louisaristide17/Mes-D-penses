"""Design system : couleurs, police, icônes et feuille de style, communs au web et au mobile."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QFontDatabase, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).parent / "assets"

PRIMARY = "#0F5D4A"
PRIMARY_HOVER = "#0B4B3B"
PRIMARY_SOFT = "#E6F0ED"
PRIMARY_MUTED = "#B9D3CB"
BG = "#F7F8F7"
SURFACE = "#FFFFFF"
BORDER = "#E4E7E5"
BORDER_STRONG = "#CFD5D1"
TEXT = "#16201C"
MUTED = "#5B6661"
WARNING = "#B7791F"
WARNING_SOFT = "#FBF3E2"
WARNING_TEXT = "#8A5A12"
DANGER = "#B42318"
DANGER_SOFT = "#FDECEA"
SUCCESS = "#1E7B4F"
SUCCESS_SOFT = "#E7F4EC"

# Noms d'icônes stockés par l'API, vers les fichiers Lucide embarqués.
CATEGORY_ICONS = {"home": "house"}


def load_fonts() -> None:
    for font in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font))


@lru_cache(maxsize=512)
def pixmap(name: str, color: str = TEXT, size: int = 20) -> QPixmap:
    """Dessine une icône Lucide dans la couleur demandée, nette sur les écrans à haute densité."""
    path = ASSETS / "icons" / f"{CATEGORY_ICONS.get(name, name)}.svg"
    if not path.is_file():
        path = ASSETS / "icons" / "tag.svg"
    svg = path.read_text(encoding="utf-8").replace("currentColor", color).replace('stroke-width="2"', 'stroke-width="1.75"')
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    screen = QGuiApplication.primaryScreen()
    ratio = screen.devicePixelRatio() if screen else 1.0
    image = QPixmap(QSize(round(size * ratio), round(size * ratio)))
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size * ratio, size * ratio))
    painter.end()
    image.setDevicePixelRatio(ratio)
    return image


def icon(name: str, color: str = TEXT, size: int = 20) -> QIcon:
    return QIcon(pixmap(name, color, size))


def nav_icon(name: str) -> QIcon:
    """Icône de navigation : grise au repos, verte quand l'entrée est sélectionnée."""
    result = QIcon()
    result.addPixmap(pixmap(name, MUTED), QIcon.Mode.Normal, QIcon.State.Off)
    result.addPixmap(pixmap(name, PRIMARY), QIcon.Mode.Normal, QIcon.State.On)
    return result


STYLESHEET = f"""
* {{
    font-family: "Inter";
    font-size: 14px;
    color: {TEXT};
    outline: 0;
}}
QMainWindow, QWidget#page, QWidget#auth, QScrollArea, QScrollArea > QWidget > QWidget {{
    background: {BG};
}}
QDialog {{
    background: {SURFACE};
}}
QScrollArea {{
    border: none;
}}

QLabel[role="title"] {{ font-size: 28px; font-weight: 600; }}
QLabel[role="section"] {{ font-size: 16px; font-weight: 600; }}
QLabel[role="muted"] {{ color: {MUTED}; }}
QLabel[role="small"] {{ color: {MUTED}; font-size: 12px; }}
QLabel[role="label"] {{ color: {MUTED}; font-size: 12px; font-weight: 500; }}
QLabel[role="field"] {{ font-size: 12px; font-weight: 500; }}
QLabel[role="stat"] {{ font-size: 28px; font-weight: 600; }}
QLabel[role="stat-small"] {{ font-size: 20px; font-weight: 600; }}
QLabel[role="strong"] {{ font-weight: 500; }}
QLabel[role="brand"] {{ font-size: 16px; font-weight: 600; }}
QLabel[role="pitch"] {{ font-size: 28px; font-weight: 600; color: white; }}
QLabel[role="pitch-item"] {{ color: rgba(255, 255, 255, 0.86); }}
QLabel[role="pitch-note"] {{ color: rgba(255, 255, 255, 0.7); font-size: 12px; }}
QLabel[role="trend-up"] {{ color: {DANGER}; font-size: 12px; font-weight: 500; }}
QLabel[role="trend-down"] {{ color: {SUCCESS}; font-size: 12px; font-weight: 500; }}

QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QFrame#separator {{
    background: {BORDER};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}
QWidget#sidebar {{
    background: {SURFACE};
    border-right: 1px solid {BORDER};
}}
QWidget#authAside {{
    background: {PRIMARY};
}}
QWidget#authAside QLabel[role="brand"] {{
    color: white;
}}
QWidget#authMain, QWidget#row {{
    background: transparent;
}}

QPushButton {{
    min-height: 34px;
    padding: 0 16px;
    border: 1px solid {BORDER_STRONG};
    border-radius: 8px;
    background: {SURFACE};
    font-weight: 500;
}}
QPushButton:hover {{ background: {BG}; }}
QPushButton:disabled {{ color: #9AA5A0; }}
QPushButton[variant="primary"] {{
    background: {PRIMARY};
    border-color: {PRIMARY};
    color: white;
}}
QPushButton[variant="primary"]:hover {{ background: {PRIMARY_HOVER}; border-color: {PRIMARY_HOVER}; }}
QPushButton[variant="primary"]:disabled {{ background: #8FB3A9; border-color: #8FB3A9; color: white; }}
QPushButton[variant="danger"] {{
    background: {DANGER};
    border-color: {DANGER};
    color: white;
}}
QPushButton[variant="danger"]:hover {{ background: #96190F; border-color: #96190F; }}
QPushButton[variant="ghost"] {{
    border-color: transparent;
    background: transparent;
    padding: 0;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
}}
QPushButton[variant="ghost"]:hover {{ background: {BG}; }}
QPushButton[variant="link"] {{
    border: none;
    background: transparent;
    color: {PRIMARY};
    padding: 0;
    min-height: 20px;
    font-weight: 600;
}}
QPushButton[variant="link"]:hover {{ text-decoration: underline; }}
QPushButton[variant="nav"] {{
    border: none;
    background: transparent;
    color: {MUTED};
    text-align: left;
    padding: 0 12px;
    min-height: 38px;
}}
QPushButton[variant="nav"]:hover {{ background: {BG}; color: {TEXT}; }}
QPushButton[variant="nav"]:checked {{ background: {PRIMARY_SOFT}; color: {PRIMARY}; }}

QLineEdit, QComboBox, QDateEdit {{
    min-height: 34px;
    max-height: 34px;
    padding: 0 12px;
    border: 1px solid {BORDER_STRONG};
    border-radius: 8px;
    background: {SURFACE};
    selection-background-color: {PRIMARY};
    selection-color: white;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid {PRIMARY}; }}
QLineEdit:disabled, QComboBox:disabled {{ background: {BG}; color: {MUTED}; }}
QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 28px; }}
QComboBox::down-arrow, QDateEdit::down-arrow {{
    image: url("{(ASSETS / 'icons' / 'chevron-down.svg').as_posix()}");
    width: 14px;
    height: 14px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {BORDER};
    background: {SURFACE};
    selection-background-color: {PRIMARY_SOFT};
    selection-color: {TEXT};
    padding: 4px;
}}

QTableWidget {{
    border: none;
    background: {SURFACE};
    gridline-color: transparent;
}}
QTableWidget::item {{
    border-bottom: 1px solid {BORDER};
    padding: 0 12px;
}}
QTableWidget::item:selected {{ background: #FAFBFA; color: {TEXT}; }}
QHeaderView::section {{
    background: {SURFACE};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 10px 12px;
    color: {MUTED};
    font-size: 12px;
    font-weight: 500;
}}

QProgressBar {{
    border: none;
    border-radius: 4px;
    background: {BG};
    min-height: 8px;
    max-height: 8px;
}}
QProgressBar::chunk {{ border-radius: 4px; background: {PRIMARY}; }}
QProgressBar[level="attention"]::chunk {{ background: {WARNING}; }}
QProgressBar[level="depasse"]::chunk {{ background: {DANGER}; }}

QLabel[badge="ok"] {{ background: {SUCCESS_SOFT}; color: {SUCCESS}; }}
QLabel[badge="attention"] {{ background: {WARNING_SOFT}; color: {WARNING_TEXT}; }}
QLabel[badge="depasse"] {{ background: {DANGER_SOFT}; color: {DANGER}; }}
QLabel[badge] {{ border-radius: 11px; padding: 3px 8px; font-size: 12px; font-weight: 500; }}

QFrame[notice="error"] {{ background: {DANGER_SOFT}; border-radius: 8px; }}
QFrame[notice="error"] QLabel {{ color: {DANGER}; }}
QFrame[notice="warning"] {{ background: {WARNING_SOFT}; border-radius: 8px; }}
QFrame[notice="warning"] QLabel {{ color: {WARNING_TEXT}; }}
QFrame[notice="success"] {{ background: {SUCCESS_SOFT}; border-radius: 8px; }}
QFrame[notice="success"] QLabel {{ color: {SUCCESS}; }}
QFrame#bubbleUser {{
    background: {PRIMARY};
    border-radius: 12px;
    border-bottom-right-radius: 4px;
}}
QFrame#bubbleUser QLabel {{ color: white; }}
QFrame#bubbleAssistant {{
    background: {BG};
    border-radius: 12px;
    border-bottom-left-radius: 4px;
}}
QScrollArea#chatArea, QWidget#chatHolder {{ background: {SURFACE}; }}
QFrame#suggestion {{ background: {PRIMARY_SOFT}; border-radius: 8px; }}
QFrame#suggestion QLabel {{ font-size: 12px; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BORDER_STRONG}; border-radius: 5px; min-height: 32px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QToolTip {{
    background: {TEXT};
    color: white;
    border: none;
    padding: 6px 8px;
}}
QCalendarWidget QWidget {{ background: {SURFACE}; }}
QCalendarWidget QAbstractItemView {{
    selection-background-color: {PRIMARY};
    selection-color: white;
}}
QMessageBox {{ background: {SURFACE}; }}
"""
