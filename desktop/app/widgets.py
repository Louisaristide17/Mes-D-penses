"""Composants partagés par les écrans."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import theme
from app.format import current_month, month_label, shift_month


def label(text: str = "", role: str | None = None, wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(wrap)
    return widget


def button(text: str = "", variant: str | None = None, icon_name: str | None = None) -> QPushButton:
    # L'espace écarte le texte de l'icône, que la feuille de style Qt ne permet pas de régler.
    widget = QPushButton(f" {text}" if icon_name and text else text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if variant:
        widget.setProperty("variant", variant)
    if icon_name:
        color = "#FFFFFF" if variant in ("primary", "danger") else theme.TEXT
        widget.setIcon(theme.icon(icon_name, color, 16))
        widget.setIconSize(QSize(16, 16))
    return widget


def icon_button(icon_name: str, tooltip: str) -> QPushButton:
    widget = QPushButton()
    widget.setProperty("variant", "ghost")
    widget.setIcon(theme.icon(icon_name, theme.MUTED, 16))
    widget.setIconSize(QSize(16, 16))
    widget.setToolTip(tooltip)
    widget.setAccessibleName(tooltip)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    return widget


def icon_label(icon_name: str, color: str = theme.TEXT, size: int = 16) -> QLabel:
    widget = QLabel()
    widget.setPixmap(theme.pixmap(icon_name, color, size))
    widget.setFixedSize(size, size)
    return widget


def separator() -> QFrame:
    line = QFrame()
    line.setObjectName("separator")
    return line


def field(title: str, widget: QWidget, hint: str | None = None) -> QVBoxLayout:
    """Champ de formulaire : libellé au-dessus, aide facultative en dessous."""
    layout = QVBoxLayout()
    layout.setSpacing(4)
    layout.addWidget(label(title, "field"))
    layout.addWidget(widget)
    if hint:
        layout.addWidget(label(hint, "small"))
    return layout


def remove_widget(widget: QWidget) -> None:
    """Retire un composant de l'écran tout de suite, puis laisse Qt le détruire."""
    # deleteLater seul laisserait le composant visible jusqu'au prochain tour de la boucle d'événements.
    widget.setParent(None)
    widget.deleteLater()


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            remove_widget(item.widget())
        elif item.layout() is not None:
            clear_layout(item.layout())


class Card(QFrame):
    def __init__(self, padding: int = 24, spacing: int = 16):
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)


class Notice(QFrame):
    """Message d'erreur, d'avertissement ou de confirmation. Masqué tant qu'il est vide."""

    ICONS = {"error": "circle-alert", "warning": "triangle-alert", "success": "circle-check"}
    COLORS = {"error": theme.DANGER, "warning": theme.WARNING_TEXT, "success": theme.SUCCESS}

    def __init__(self, text: str = "", tone: str = "error"):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        self._icon = QLabel()
        self._icon.setFixedSize(16, 16)
        self._text = label(wrap=True)
        layout.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._text, 1)
        self.show_message(text, tone)

    def show_message(self, text: str, tone: str = "error") -> None:
        self.setProperty("notice", tone)
        self._icon.setPixmap(theme.pixmap(self.ICONS[tone], self.COLORS[tone], 16))
        self._text.setText(text)
        # La propriété pilote la feuille de style : il faut la réappliquer après un changement.
        self.style().unpolish(self)
        self.style().polish(self)
        self.setVisible(bool(text))

    def clear(self) -> None:
        self.setVisible(False)


class CategoryIcon(QWidget):
    """Pastille colorée portant l'icône d'une catégorie."""

    def __init__(self, category: dict, size: int = 28):
        super().__init__()
        self._color = QColor(category["color"])
        self._pixmap = theme.pixmap(category["icon"], category["color"], round(size * 0.55))
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        background = QColor(self._color)
        background.setAlpha(31)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(self.rect(), 8, 8)
        inner = round(self._size * 0.55)
        offset = (self._size - inner) // 2
        painter.drawPixmap(offset, offset, self._pixmap)


def category_label(category: dict) -> QWidget:
    widget = QWidget()
    widget.setObjectName("row")
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(12, 0, 12, 0)
    layout.setSpacing(8)
    layout.addWidget(CategoryIcon(category))
    layout.addWidget(label(category["name"], "strong"))
    layout.addStretch()
    return widget


class MonthPicker(QFrame):
    changed = Signal(str)

    def __init__(self, allow_future: bool = False):
        super().__init__()
        self.setObjectName("card")
        self.month = current_month()
        self.allow_future = allow_future
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self._previous = icon_button("chevron-left", "Mois précédent")
        self._next = icon_button("chevron-right", "Mois suivant")
        self._label = label(role="strong")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumWidth(140)
        layout.addWidget(self._previous)
        layout.addWidget(self._label)
        layout.addWidget(self._next)
        self._previous.clicked.connect(lambda: self._shift(-1))
        self._next.clicked.connect(lambda: self._shift(1))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._update()

    def _shift(self, offset: int) -> None:
        self.month = shift_month(self.month, offset)
        self._update()
        self.changed.emit(self.month)

    def _update(self) -> None:
        self._label.setText(month_label(self.month))
        self._next.setEnabled(self.allow_future or self.month < current_month())


class EmptyState(QWidget):
    def __init__(self, icon_name: str, title: str, text: str, action: QPushButton | None = None):
        super().__init__()
        self.setObjectName("row")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 40, 24, 40)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        picture = icon_label(icon_name, theme.MUTED, 28)
        layout.addWidget(picture, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(4)
        heading = label(title, "section")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        body = label(text, "muted", wrap=True)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setFixedWidth(380)
        # Un texte sur plusieurs lignes centré dans une colonne ne réserve pas seul sa hauteur.
        body.ensurePolished()
        body.setMinimumHeight(body.heightForWidth(380) + 4)
        layout.addWidget(body, 0, Qt.AlignmentFlag.AlignHCenter)
        if action is not None:
            layout.addSpacing(8)
            layout.addWidget(action, 0, Qt.AlignmentFlag.AlignHCenter)


class Page(QScrollArea):
    """Écran défilant avec un en-tête (titre, sous-titre, actions) et une colonne de contenu."""

    def __init__(self, title: str, subtitle: str, max_width: int = 1120):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        container.setObjectName("page")
        outer = QHBoxLayout(container)
        outer.setContentsMargins(32, 32, 32, 40)
        column = QWidget()
        column.setObjectName("page")
        column.setMaximumWidth(max_width)
        outer.addWidget(column)
        self.setWidget(container)

        self.content = QVBoxLayout(column)
        self.content.setContentsMargins(0, 0, 0, 0)
        self.content.setSpacing(16)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(4)
        titles.addWidget(label(title, "title"))
        self.subtitle = label(subtitle, "muted")
        titles.addWidget(self.subtitle)
        header.addLayout(titles, 1)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        header.addLayout(self.actions)
        header.setAlignment(self.actions, Qt.AlignmentFlag.AlignBottom)
        self.content.addLayout(header)
        self.content.addSpacing(8)


class FormDialog(QDialog):
    """Fenêtre modale avec un corps de formulaire et une rangée de boutons."""

    def __init__(self, parent: QWidget, title: str, confirm_text: str, confirm_variant: str = "primary"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(label(title, "section"))
        self.notice = Notice()
        layout.addWidget(self.notice)
        self.form = QVBoxLayout()
        self.form.setSpacing(16)
        layout.addLayout(self.form)
        layout.addSpacing(8)
        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = button("Annuler")
        self.confirm_button = button(confirm_text, confirm_variant)
        self.confirm_button.setDefault(True)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.confirm_button)
        layout.addLayout(buttons)
        self.cancel_button.clicked.connect(self.reject)

    def set_busy(self, busy: bool) -> None:
        self.confirm_button.setEnabled(not busy)

    def fail(self, message: str) -> None:
        self.notice.show_message(message)
        self.set_busy(False)


def confirm(parent: QWidget, title: str, text: str, confirm_text: str = "Supprimer") -> bool:
    dialog = FormDialog(parent, title, confirm_text, "danger")
    dialog.form.addWidget(label(text, wrap=True))
    dialog.confirm_button.clicked.connect(dialog.accept)
    return dialog.exec() == QDialog.DialogCode.Accepted
