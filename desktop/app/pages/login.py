from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPolygonF
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from app import theme
from app.api import ApiClient
from app.tasks import run_async
from app.widgets import Notice, button, field, icon_label, label

MIN_PASSWORD = 8

PITCH = [
    ("receipt", "Notez une dépense en quelques secondes"),
    ("trending-up", "Voyez où part votre argent, mois après mois"),
    ("target", "Fixez un budget et soyez prévenu avant de le dépasser"),
]


class BrandMark(QWidget):
    """Logo : carré arrondi portant le monogramme."""

    def __init__(self, background: str = theme.PRIMARY, foreground: str = "#FFFFFF"):
        super().__init__()
        self._background, self._foreground = QColor(background), QColor(foreground)
        self.setFixedSize(32, 32)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._background)
        painter.drawRoundedRect(self.rect(), 8, 8)
        pen = painter.pen()
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setColor(self._foreground)
        pen.setWidthF(2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolyline(
            QPolygonF([QPointF(10, 21), QPointF(10, 12), QPointF(16, 18), QPointF(22, 12), QPointF(22, 21)])
        )


def brand(inverted: bool = False) -> QHBoxLayout:
    layout = QHBoxLayout()
    layout.setSpacing(12)
    layout.addWidget(BrandMark("#FFFFFF", theme.PRIMARY) if inverted else BrandMark())
    layout.addWidget(label("Mes Dépenses", "brand"))
    layout.addStretch()
    return layout


class LoginPage(QWidget):
    authenticated = Signal(dict)

    def __init__(self, api: ApiClient):
        super().__init__()
        self.setObjectName("auth")
        self.api = api
        self.registering = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_aside(), 5)
        layout.addWidget(self._build_form(), 6)
        self._apply_mode()

    def _build_aside(self) -> QWidget:
        aside = QWidget()
        aside.setObjectName("authAside")
        layout = QVBoxLayout(aside)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addLayout(brand(inverted=True))
        layout.addStretch()
        pitch = label("Gardez la main sur vos dépenses, au franc près.", "pitch", wrap=True)
        pitch.setMaximumWidth(400)
        layout.addWidget(pitch)
        layout.addSpacing(24)
        for icon_name, text in PITCH:
            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(icon_label(icon_name, "#FFFFFF", 20))
            row.addWidget(label(text, "pitch-item"), 1)
            layout.addLayout(row)
            layout.addSpacing(4)
        layout.addStretch()
        layout.addWidget(label("Vos données restent privées et ne sont visibles que de vous.", "pitch-note"))
        return aside

    def _build_form(self) -> QWidget:
        main = QWidget()
        main.setObjectName("authMain")
        outer = QHBoxLayout(main)
        column = QWidget()
        column.setObjectName("authMain")
        column.setFixedWidth(380)
        outer.addStretch()
        outer.addWidget(column, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addStretch()

        form = QVBoxLayout(column)
        form.setSpacing(16)
        self.title = label(role="title")
        self.subtitle = label(role="muted", wrap=True)
        form.addWidget(self.title)
        form.addWidget(self.subtitle)
        form.addSpacing(8)
        self.notice = Notice()
        form.addWidget(self.notice)

        self.name = QLineEdit()
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.name_field = QWidget()
        self.name_field.setObjectName("authMain")
        name_layout = field("Nom complet", self.name)
        name_layout.setContentsMargins(0, 0, 0, 0)
        self.name_field.setLayout(name_layout)
        form.addWidget(self.name_field)
        form.addLayout(field("Adresse e-mail", self.email))
        form.addLayout(field("Mot de passe", self.password))
        self.password_hint = label(f"{MIN_PASSWORD} caractères au minimum.", "small")
        form.addWidget(self.password_hint)

        self.submit = button(variant="primary")
        self.submit.setMinimumHeight(40)
        self.submit.setDefault(True)
        form.addSpacing(4)
        form.addWidget(self.submit)

        switch = QHBoxLayout()
        switch.addStretch()
        self.switch_text = label(role="muted")
        self.switch_button = button(variant="link")
        switch.addWidget(self.switch_text)
        switch.addWidget(self.switch_button)
        switch.addStretch()
        form.addLayout(switch)

        self.submit.clicked.connect(self._submit)
        self.password.returnPressed.connect(self._submit)
        self.switch_button.clicked.connect(self._toggle)
        return main

    def _apply_mode(self) -> None:
        registering = self.registering
        self.title.setText("Créer un compte" if registering else "Connexion")
        self.subtitle.setText(
            "Une minute suffit pour commencer à suivre vos dépenses."
            if registering
            else "Retrouvez vos dépenses et vos budgets."
        )
        self.name_field.setVisible(registering)
        self.password_hint.setVisible(registering)
        self.submit.setText("Créer mon compte" if registering else "Se connecter")
        self.switch_text.setText("Déjà inscrit ?" if registering else "Pas encore de compte ?")
        self.switch_button.setText("Se connecter" if registering else "Créer un compte")
        self.notice.clear()

    def _toggle(self) -> None:
        self.registering = not self.registering
        self._apply_mode()

    def reset(self) -> None:
        self.password.clear()
        self.submit.setEnabled(True)
        self.registering = False
        self._apply_mode()

    def _submit(self) -> None:
        name, email, password = self.name.text().strip(), self.email.text().strip(), self.password.text()
        if "@" not in email or not password:
            self.notice.show_message("Indiquez votre adresse e-mail et votre mot de passe.")
            return
        if self.registering:
            if len(name) < 2:
                self.notice.show_message("Indiquez votre nom.")
                return
            if len(password) < MIN_PASSWORD:
                self.notice.show_message(f"Le mot de passe doit contenir au moins {MIN_PASSWORD} caractères.")
                return
            call = lambda: self.api.register(name, email, password)  # noqa: E731
        else:
            call = lambda: self.api.login(email, password)  # noqa: E731
        self.notice.clear()
        self.submit.setEnabled(False)
        run_async(self, call, self._succeeded, self._failed)

    def _succeeded(self, user: dict) -> None:
        self.password.clear()
        self.authenticated.emit(user)

    def _failed(self, message: str) -> None:
        self.notice.show_message(message)
        self.submit.setEnabled(True)
