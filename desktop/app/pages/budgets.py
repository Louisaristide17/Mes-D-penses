from PySide6.QtWidgets import QDialog, QHBoxLayout, QProgressBar, QVBoxLayout

from app.api import ApiClient
from app.dialogs import BudgetDialog
from app.format import format_amount, format_percent, month_label
from app.tasks import run_async
from app.widgets import (
    Card,
    CategoryIcon,
    EmptyState,
    MonthPicker,
    Notice,
    Page,
    button,
    clear_layout,
    confirm,
    icon_button,
    label,
)

LEVEL_LABELS = {"ok": "Dans le budget", "attention": "Bientôt atteint", "depasse": "Dépassé"}


class BudgetsPage(Page):
    def __init__(self, api: ApiClient):
        super().__init__("Budgets", "")
        self.api = api
        self.statuses: list[dict] = []
        self.categories: list[dict] = []

        self.month_picker = MonthPicker(allow_future=True)
        self.add_button = button("Nouveau budget", "primary", "plus")
        self.actions.addWidget(self.month_picker)
        self.actions.addWidget(self.add_button)
        self.notice = Notice()
        self.content.addWidget(self.notice)
        self.body = QVBoxLayout()
        self.body.setSpacing(16)
        self.content.addLayout(self.body)
        self.content.addStretch()

        self.month_picker.changed.connect(lambda _month: self.reload())
        self.add_button.clicked.connect(lambda: self._open_form())

    @property
    def month(self) -> str:
        return self.month_picker.month

    def reload(self) -> None:
        month = self.month
        self.notice.clear()

        def load():
            return self.api.budget_statuses(month), self.api.categories()

        def received(result) -> None:
            if month == self.month:
                self.statuses, self.categories = result
                self._render()

        run_async(self, load, received, self.notice.show_message)

    def _available(self) -> list[dict]:
        used = {status["category"]["id"] for status in self.statuses}
        return [category for category in self.categories if category["id"] not in used]

    def _render(self) -> None:
        clear_layout(self.body)
        self.add_button.setEnabled(bool(self._available()))
        if not self.statuses:
            self.subtitle.setText("Fixez un plafond mensuel par catégorie.")
            card = Card(padding=0)
            create = button("Nouveau budget", "primary", "plus")
            create.clicked.connect(lambda: self._open_form())
            card.body.addWidget(
                EmptyState(
                    "target",
                    f"Aucun budget pour {month_label(self.month).lower()}",
                    "Un budget fixe un plafond pour une catégorie. Vous êtes prévenu à 80 % du plafond, "
                    "puis en cas de dépassement.",
                    create,
                )
            )
            self.body.addWidget(card)
            return
        spent = sum(status["spent"] for status in self.statuses)
        ceiling = sum(status["ceiling"] for status in self.statuses)
        self.subtitle.setText(f"{format_amount(spent)} dépensés sur {format_amount(ceiling)} prévus.")
        for status in self.statuses:
            self.body.addWidget(self._budget_card(status))

    def _budget_card(self, status: dict) -> Card:
        card = Card(spacing=12)
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(CategoryIcon(status["category"]))
        head.addWidget(label(status["category"]["name"], "strong"), 1)
        badge = label(LEVEL_LABELS[status["level"]])
        badge.setProperty("badge", status["level"])
        head.addWidget(badge)
        edit = icon_button("pencil", "Modifier le plafond")
        delete = icon_button("trash-2", "Supprimer le budget")
        edit.clicked.connect(lambda: self._open_form(status))
        delete.clicked.connect(lambda: self._delete(status))
        head.addWidget(edit)
        head.addWidget(delete)
        card.body.addLayout(head)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(min(100, round(status["ratio"] * 100)))
        bar.setTextVisible(False)
        bar.setProperty("level", status["level"])
        card.body.addWidget(bar)

        figures = QHBoxLayout()
        figures.addWidget(
            label(
                f"{format_amount(status['spent'])} sur {format_amount(status['ceiling'])} ({format_percent(status['ratio'])})",
                "small",
            ),
            1,
        )
        over = status["remaining"] < 0
        remaining = (
            f"Dépassement de {format_amount(-status['remaining'])}" if over else f"Reste {format_amount(status['remaining'])}"
        )
        figures.addWidget(label(remaining, "small"))
        card.body.addLayout(figures)
        return card

    def _open_form(self, budget: dict | None = None) -> None:
        dialog = BudgetDialog(self, self.api, self.month, self._available(), budget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.reload()

    def _delete(self, status: dict) -> None:
        text = (
            f"Le budget {status['category']['name']} de {month_label(self.month).lower()} sera supprimé. "
            "Vos dépenses ne sont pas modifiées."
        )
        if confirm(self, "Supprimer le budget", text):
            run_async(
                self,
                lambda: self.api.delete_budget(status["budget_id"]),
                lambda _result: self.reload(),
                self.notice.show_message,
            )
