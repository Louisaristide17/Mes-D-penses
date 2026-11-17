"""Fenêtres de saisie : dépense et budget."""

from datetime import date

from PySide6.QtCore import QDate, QRegularExpression, Qt, QTimer
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QComboBox, QDateEdit, QFrame, QHBoxLayout, QLineEdit, QWidget

from app.api import ApiClient
from app.format import format_percent, month_label, parse_amount
from app.tasks import run_async
from app.widgets import FormDialog, button, field, icon_label, label
from app import theme

AMOUNT_PATTERN = QRegularExpression(r"[\d\s]{0,13}")


def amount_input() -> QLineEdit:
    widget = QLineEdit()
    widget.setPlaceholderText("0")
    widget.setValidator(QRegularExpressionValidator(AMOUNT_PATTERN))
    return widget


class ExpenseDialog(FormDialog):
    """Ajout ou modification d'une dépense, avec catégorie suggérée à partir de la note."""

    def __init__(self, parent: QWidget, api: ApiClient, categories: list[dict], expense: dict | None = None):
        editing = expense is not None
        super().__init__(
            parent,
            "Modifier la dépense" if editing else "Nouvelle dépense",
            "Enregistrer" if editing else "Ajouter la dépense",
        )
        self.api = api
        self.expense = expense
        self._suggested: dict | None = None
        self._request = 0

        self.amount = amount_input()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("dd/MM/yyyy")
        self.note = QLineEdit()
        self.note.setMaxLength(255)
        self.note.setPlaceholderText("Taxi pour Cocody, facture CIE, marché...")
        self.category = QComboBox()
        if not editing:
            self.category.addItem("Automatique", None)
        for category in categories:
            self.category.addItem(category["name"], category["id"])

        if editing:
            self.amount.setText(str(expense["amount"]))
            self.date.setDate(QDate.fromString(expense["date"], Qt.DateFormat.ISODate))
            self.note.setText(expense["note"])
            self.category.setCurrentIndex(self.category.findData(expense["category"]["id"]))
        else:
            today = date.today()
            self.date.setDate(QDate(today.year, today.month, today.day))

        row = QHBoxLayout()
        row.setSpacing(16)
        row.addLayout(field("Montant (FCFA)", self.amount))
        row.addLayout(field("Date", self.date))
        self.form.addLayout(row)
        self.form.addLayout(field("Note", self.note))
        self.form.addLayout(field("Catégorie", self.category))

        self.suggestion = QFrame()
        self.suggestion.setObjectName("suggestion")
        suggestion_row = QHBoxLayout(self.suggestion)
        suggestion_row.setContentsMargins(12, 8, 12, 8)
        suggestion_row.setSpacing(8)
        suggestion_row.addWidget(icon_label("tag", theme.PRIMARY, 14))
        self.suggestion_text = label(wrap=True)
        suggestion_row.addWidget(self.suggestion_text, 1)
        apply_button = button("Appliquer", "link")
        apply_button.clicked.connect(self._apply_suggestion)
        suggestion_row.addWidget(apply_button)
        self.suggestion.hide()
        self.form.addWidget(self.suggestion)

        # La suggestion est demandée une fois la frappe interrompue, pas à chaque lettre.
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._ask_suggestion)
        self.note.textChanged.connect(lambda _text: self._timer.start())
        self.category.currentIndexChanged.connect(lambda _index: self._update_suggestion())
        self.confirm_button.clicked.connect(self._save)
        self.amount.setFocus()

    def _ask_suggestion(self) -> None:
        text = self.note.text().strip()
        if len(text) < 3:
            self._suggested = None
            self._update_suggestion()
            return
        self._request += 1
        request = self._request

        def received(result: dict) -> None:
            # Une réponse arrivée après une frappe plus récente est ignorée.
            if request == self._request:
                self._suggested = result if result["category"] else None
                self._update_suggestion()

        run_async(self, lambda: self.api.suggest_category(text), received)

    def _update_suggestion(self) -> None:
        suggested = self._suggested
        if suggested is None or suggested["category"]["id"] == self.category.currentData():
            self.suggestion.hide()
            return
        self.suggestion_text.setText(
            f"Catégorie suggérée : <b>{suggested['category']['name']}</b> "
            f"({format_percent(suggested['confidence'])} de confiance)"
        )
        self.suggestion.show()

    def _apply_suggestion(self) -> None:
        if self._suggested:
            self.category.setCurrentIndex(self.category.findData(self._suggested["category"]["id"]))

    def _save(self) -> None:
        amount = parse_amount(self.amount.text())
        if not amount:
            self.notice.show_message("Indiquez un montant supérieur à zéro.")
            return
        payload = {
            "amount": amount,
            "date": self.date.date().toString(Qt.DateFormat.ISODate),
            "note": self.note.text().strip(),
        }
        if self.category.currentData() is not None:
            payload["category_id"] = self.category.currentData()
        self.notice.clear()
        self.set_busy(True)
        if self.expense is None:
            call = lambda: self.api.create_expense(payload)  # noqa: E731
        else:
            call = lambda: self.api.update_expense(self.expense["id"], payload)  # noqa: E731
        run_async(self, call, lambda _result: self.accept(), self.fail)


class BudgetDialog(FormDialog):
    """Création d'un budget, ou modification du plafond d'un budget existant."""

    def __init__(self, parent: QWidget, api: ApiClient, month: str, categories: list[dict], budget: dict | None = None):
        super().__init__(parent, "Modifier le plafond" if budget else "Nouveau budget", "Enregistrer")
        self.api = api
        self.month = month

        self.category = QComboBox()
        for category in [budget["category"]] if budget else categories:
            self.category.addItem(category["name"], category["id"])
        self.category.setEnabled(budget is None)
        self.ceiling = amount_input()
        if budget:
            self.ceiling.setText(str(budget["ceiling"]))

        self.form.addLayout(field("Catégorie", self.category))
        self.form.addLayout(field(f"Plafond pour {month_label(month).lower()} (FCFA)", self.ceiling))
        self.confirm_button.clicked.connect(self._save)
        self.ceiling.setFocus()

    def _save(self) -> None:
        ceiling = parse_amount(self.ceiling.text())
        if not ceiling:
            self.notice.show_message("Indiquez un plafond supérieur à zéro.")
            return
        category_id = self.category.currentData()
        self.notice.clear()
        self.set_busy(True)
        run_async(
            self,
            lambda: self.api.set_budget(category_id, self.month, ceiling),
            lambda _result: self.accept(),
            self.fail,
        )
