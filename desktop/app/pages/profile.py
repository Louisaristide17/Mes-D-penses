from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit

from app.api import ApiClient
from app.tasks import run_async
from app.widgets import Card, Notice, Page, button, field, label

MIN_PASSWORD = 8


class ProfilePage(Page):
    user_changed = Signal(dict)
    logout_requested = Signal()

    def __init__(self, api: ApiClient):
        super().__init__("Profil", "Votre compte et vos réglages.", max_width=640)
        self.api = api
        logout = button("Se déconnecter", icon_name="log-out")
        logout.clicked.connect(self.logout_requested.emit)
        self.actions.addWidget(logout)
        self.content.addWidget(self._identity_card())
        self.content.addWidget(self._password_card())
        self.content.addStretch()

    def set_user(self, user: dict) -> None:
        self.name.setText(user["name"])
        self.email.setText(user["email"])
        self.identity_notice.clear()
        self.password_notice.clear()

    def reload(self) -> None:
        pass

    def _identity_card(self) -> Card:
        card = Card()
        card.body.addWidget(label("Informations personnelles", "section"))
        self.identity_notice = Notice()
        card.body.addWidget(self.identity_notice)
        self.name = QLineEdit()
        self.email = QLineEdit()
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addLayout(field("Nom complet", self.name))
        row.addLayout(field("Adresse e-mail", self.email))
        card.body.addLayout(row)
        self.identity_button = button("Enregistrer", "primary")
        buttons = QHBoxLayout()
        buttons.addWidget(self.identity_button)
        buttons.addStretch()
        card.body.addLayout(buttons)
        self.identity_button.clicked.connect(self._save_identity)
        return card

    def _password_card(self) -> Card:
        card = Card()
        card.body.addWidget(label("Mot de passe", "section"))
        self.password_notice = Notice()
        card.body.addWidget(self.password_notice)
        self.current_password = QLineEdit()
        self.new_password = QLineEdit()
        for widget in (self.current_password, self.new_password):
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addLayout(field("Mot de passe actuel", self.current_password))
        row.addLayout(field("Nouveau mot de passe", self.new_password))
        card.body.addLayout(row)
        card.body.addWidget(label(f"Le nouveau mot de passe doit contenir {MIN_PASSWORD} caractères au minimum.", "small"))
        self.password_button = button("Modifier le mot de passe", "primary")
        buttons = QHBoxLayout()
        buttons.addWidget(self.password_button)
        buttons.addStretch()
        card.body.addLayout(buttons)
        self.password_button.clicked.connect(self._save_password)
        return card

    def _save_identity(self) -> None:
        name, email = self.name.text().strip(), self.email.text().strip()
        if len(name) < 2 or "@" not in email:
            self.identity_notice.show_message("Indiquez un nom et une adresse e-mail valides.")
            return
        self.identity_button.setEnabled(False)

        def done(user: dict) -> None:
            self.identity_button.setEnabled(True)
            self.identity_notice.show_message("Profil mis à jour.", "success")
            self.user_changed.emit(user)

        def failed(message: str) -> None:
            self.identity_button.setEnabled(True)
            self.identity_notice.show_message(message)

        run_async(self, lambda: self.api.update_profile(name, email), done, failed)

    def _save_password(self) -> None:
        current, new = self.current_password.text(), self.new_password.text()
        if not current or len(new) < MIN_PASSWORD:
            self.password_notice.show_message(f"Le nouveau mot de passe doit contenir au moins {MIN_PASSWORD} caractères.")
            return
        self.password_button.setEnabled(False)

        def done(_result) -> None:
            self.password_button.setEnabled(True)
            self.current_password.clear()
            self.new_password.clear()
            self.password_notice.show_message("Mot de passe modifié.", "success")

        def failed(message: str) -> None:
            self.password_button.setEnabled(True)
            self.password_notice.show_message(message)

        run_async(self, lambda: self.api.change_password(current, new), done, failed)
