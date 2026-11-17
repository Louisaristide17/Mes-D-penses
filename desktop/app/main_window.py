from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app import theme
from app.api import ApiClient
from app.config import APP_NAME
from app.pages.assistant import AssistantPage
from app.pages.budgets import BudgetsPage
from app.pages.dashboard import DashboardPage
from app.pages.expenses import ExpensesPage
from app.pages.login import LoginPage, brand
from app.pages.profile import ProfilePage
from app.tasks import run_async
from app.widgets import icon_button, label

NAVIGATION = [
    ("Tableau de bord", "layout-dashboard"),
    ("Dépenses", "receipt"),
    ("Budgets", "target"),
    ("Assistant", "messages-square"),
    ("Profil", "user"),
]


def initials(name: str) -> str:
    return "".join(part[0].upper() for part in name.split()[:2])


class MainWindow(QMainWindow):
    # Émis depuis un fil d'arrière-plan par le client HTTP ; Qt le délivre dans le fil de l'interface.
    session_expired = Signal()

    def __init__(self, api: ApiClient):
        super().__init__()
        self.api = api
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(theme.icon("receipt", theme.PRIMARY, 64))
        self.resize(1280, 820)
        self.setMinimumSize(1040, 680)

        self.root = QStackedWidget()
        self.setCentralWidget(self.root)
        self.login_page = LoginPage(api)
        self.root.addWidget(self.login_page)
        self.root.addWidget(self._build_shell())

        self.login_page.authenticated.connect(self._enter)
        self.session_expired.connect(self._leave)
        api.on_session_expired = self.session_expired.emit

    # Construction

    def _build_shell(self) -> QWidget:
        shell = QWidget()
        layout = QHBoxLayout(shell)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.dashboard = DashboardPage(self.api)
        self.expenses = ExpensesPage(self.api)
        self.budgets = BudgetsPage(self.api)
        self.assistant = AssistantPage(self.api)
        self.profile = ProfilePage(self.api)
        self.pages = QStackedWidget()
        for page in (self.dashboard, self.expenses, self.budgets, self.assistant, self.profile):
            self.pages.addWidget(page)

        layout.addWidget(self._build_sidebar())
        layout.addWidget(self.pages, 1)

        self.dashboard.add_requested.connect(self._add_from_dashboard)
        self.dashboard.see_all_requested.connect(lambda: self._show_page(1))
        self.profile.user_changed.connect(self._set_user)
        self.profile.logout_requested.connect(self._logout)
        return shell

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        # Sans cet attribut, un QWidget simple n'applique pas le fond défini par la feuille de style.
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(4)

        header = brand()
        header.setContentsMargins(8, 0, 0, 0)
        layout.addLayout(header)
        layout.addSpacing(28)

        self.nav = QButtonGroup(self)
        for index, (text, icon_name) in enumerate(NAVIGATION):
            entry = QPushButton(f"  {text}")
            entry.setProperty("variant", "nav")
            entry.setCheckable(True)
            entry.setIcon(theme.nav_icon(icon_name))
            entry.setIconSize(QSize(20, 20))
            entry.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav.addButton(entry, index)
            layout.addWidget(entry)
        self.nav.idClicked.connect(self._show_page)
        layout.addStretch()

        footer = QHBoxLayout()
        footer.setContentsMargins(8, 12, 0, 0)
        footer.setSpacing(12)
        self.avatar = QLabel()
        self.avatar.setFixedSize(32, 32)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(
            f"background: {theme.PRIMARY_SOFT}; color: {theme.PRIMARY}; border-radius: 16px; "
            "font-size: 12px; font-weight: 600;"
        )
        names = QVBoxLayout()
        names.setSpacing(0)
        self.user_name = label(role="strong")
        self.user_email = label(role="small")
        names.addWidget(self.user_name)
        names.addWidget(self.user_email)
        logout = icon_button("log-out", "Se déconnecter")
        logout.clicked.connect(self._logout)
        footer.addWidget(self.avatar)
        footer.addLayout(names, 1)
        footer.addWidget(logout)
        layout.addLayout(footer)
        return sidebar

    # Session

    def start(self) -> None:
        """Rouvre la session enregistrée si elle est encore valable, sinon affiche la connexion."""
        self.api.restore_session()
        if self.api.has_session:
            run_async(self, self.api.profile, self._enter, lambda _message: self._leave())
        self.show()

    def _enter(self, user: dict) -> None:
        self._set_user(user)
        self.profile.set_user(user)
        self.assistant.reset()
        self.root.setCurrentIndex(1)
        self._show_page(0)
        # Les catégories sont préchargées pour que le formulaire d'ajout s'ouvre sans attente.
        run_async(self, self.api.categories, self.expenses.set_categories)

    def _set_user(self, user: dict) -> None:
        self.avatar.setText(initials(user["name"]))
        self.user_name.setText(user["name"])
        self.user_email.ensurePolished()
        metrics = self.user_email.fontMetrics()
        self.user_email.setText(metrics.elidedText(user["email"], Qt.TextElideMode.ElideRight, 112))
        # Une adresse trop longue pour la barre est abrégée : l'infobulle donne le texte entier.
        self.user_email.setToolTip(user["email"])

    def _logout(self) -> None:
        self.api.clear_session()
        self._leave()

    def _leave(self) -> None:
        self.login_page.reset()
        self.root.setCurrentIndex(0)

    # Navigation

    def _show_page(self, index: int) -> None:
        self.nav.button(index).setChecked(True)
        self.pages.setCurrentIndex(index)
        self.pages.currentWidget().reload()

    def _add_from_dashboard(self) -> None:
        if self.expenses.add_expense():
            self.dashboard.reload()
