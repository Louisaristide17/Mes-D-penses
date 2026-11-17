from pathlib import Path

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.api import ApiClient, ApiError
from app.config import PAGE_SIZE
from app.dialogs import ExpenseDialog
from app.format import current_month, format_amount, format_date, month_range
from app.tasks import run_async
from app.widgets import (
    Card,
    EmptyState,
    Notice,
    Page,
    button,
    category_label,
    confirm,
    field,
    icon_button,
    label,
    separator,
)

ROW_HEIGHT = 52
COLUMNS = ["Date", "Dépense", "Catégorie", "Montant", ""]


def date_input(iso_day: str) -> QDateEdit:
    widget = QDateEdit()
    widget.setCalendarPopup(True)
    widget.setDisplayFormat("dd/MM/yyyy")
    widget.setDate(QDate.fromString(iso_day, Qt.DateFormat.ISODate))
    return widget


class ExpensesPage(Page):
    def __init__(self, api: ApiClient):
        super().__init__("Dépenses", "Consultez, corrigez et exportez vos dépenses.")
        self.api = api
        self.categories: list[dict] = []
        self.items: list[dict] = []
        self.total = 0
        self.page = 0
        self._request = 0

        self._build_actions()
        self.notice = Notice()
        self.content.addWidget(self.notice)
        self.content.addWidget(self._build_card())
        self.content.addStretch()

    # Construction

    def _build_actions(self) -> None:
        self.import_button = button("Importer", icon_name="upload")
        self.csv_button = button("CSV", icon_name="download")
        self.pdf_button = button("PDF", icon_name="file-text")
        add_button = button("Nouvelle dépense", "primary", "plus")
        for widget in (self.import_button, self.csv_button, self.pdf_button, add_button):
            self.actions.addWidget(widget)
        self.import_button.clicked.connect(self._import)
        self.csv_button.clicked.connect(lambda: self._export("csv"))
        self.pdf_button.clicked.connect(lambda: self._export("pdf"))
        add_button.clicked.connect(self.add_expense)

    def _build_card(self) -> Card:
        card = Card(padding=0, spacing=0)
        first, last = month_range(current_month())

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher dans les notes")
        self.search.setClearButtonEnabled(True)
        self.date_from = date_input(first)
        self.date_to = date_input(last)
        self.category = QComboBox()
        self.category.addItem("Toutes", None)

        filters = QHBoxLayout()
        filters.setContentsMargins(24, 16, 24, 16)
        filters.setSpacing(12)
        filters.addLayout(field("Recherche", self.search), 2)
        filters.addLayout(field("Du", self.date_from), 1)
        filters.addLayout(field("Au", self.date_to), 1)
        filters.addLayout(field("Catégorie", self.category), 1)
        card.body.addLayout(filters)
        card.body.addWidget(separator())

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setHighlightSections(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 96)
        self.table.cellDoubleClicked.connect(lambda row, _column: self._edit(self.items[row]))
        card.body.addWidget(self.table)

        self.empty_holder = QHBoxLayout()
        card.body.addLayout(self.empty_holder)

        self.footer = QWidget()
        self.footer.setObjectName("row")
        footer = QHBoxLayout(self.footer)
        footer.setContentsMargins(24, 12, 24, 12)
        self.range_label = label(role="small")
        self.previous_button = button("Précédent", icon_name="chevron-left")
        self.next_button = button("Suivant")
        footer.addWidget(self.range_label, 1)
        footer.addWidget(self.previous_button)
        footer.addWidget(self.next_button)
        card.body.addWidget(self.footer)

        # La recherche attend la fin de la frappe avant d'interroger l'API.
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self._filters_changed)
        self.search.textChanged.connect(lambda _text: self._search_timer.start())
        self.date_from.dateChanged.connect(lambda _date: self._filters_changed())
        self.date_to.dateChanged.connect(lambda _date: self._filters_changed())
        self.category.currentIndexChanged.connect(lambda _index: self._filters_changed())
        self.previous_button.clicked.connect(lambda: self._go_to(self.page - 1))
        self.next_button.clicked.connect(lambda: self._go_to(self.page + 1))
        return card

    # Chargement

    def _filters(self) -> dict:
        return {
            "q": self.search.text().strip(),
            "date_from": self.date_from.date().toString(Qt.DateFormat.ISODate),
            "date_to": self.date_to.date().toString(Qt.DateFormat.ISODate),
            "category_id": self.category.currentData(),
        }

    def reload(self) -> None:
        run_async(self, self.api.categories, self.set_categories)
        self._load()

    def set_categories(self, categories: list[dict]) -> None:
        self.categories = categories
        selected = self.category.currentData()
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("Toutes", None)
        for category in categories:
            self.category.addItem(category["name"], category["id"])
        self.category.setCurrentIndex(max(0, self.category.findData(selected)))
        self.category.blockSignals(False)

    def _filters_changed(self) -> None:
        self.page = 0
        self._load()

    def _go_to(self, page: int) -> None:
        self.page = max(0, page)
        self._load()

    def _load(self) -> None:
        self._request += 1
        request = self._request
        filters = self._filters()
        offset = self.page * PAGE_SIZE

        def received(data: dict) -> None:
            # Une réponse arrivée après une requête plus récente est ignorée.
            if request == self._request:
                self._render(data)

        run_async(self, lambda: self.api.expenses(limit=PAGE_SIZE, offset=offset, **filters), received, self.notice.show_message)

    def _render(self, data: dict) -> None:
        self.items, self.total = data["items"], data["total"]
        # Après une suppression, la page courante peut ne plus exister : on recule.
        if not self.items and self.page > 0:
            self._go_to(self.page - 1)
            return

        while self.empty_holder.count():
            self.empty_holder.takeAt(0).widget().deleteLater()
        self.table.setVisible(bool(self.items))
        self.footer.setVisible(bool(self.items))
        if not self.items:
            filtered = bool(self.search.text().strip() or self.category.currentData())
            self.empty_holder.addWidget(
                EmptyState(
                    "search" if filtered else "receipt",
                    "Aucun résultat" if filtered else "Aucune dépense sur cette période",
                    "Aucune dépense ne correspond à ces critères. Élargissez la période ou modifiez la recherche."
                    if filtered
                    else "Ajoutez une dépense ou importez un fichier CSV pour commencer.",
                )
            )
            return

        self.table.setRowCount(len(self.items))
        for row, expense in enumerate(self.items):
            date_item = QTableWidgetItem(format_date(expense["date"]))
            note_item = QTableWidgetItem(expense["note"] or "Sans note")
            amount_item = QTableWidgetItem(format_amount(expense["amount"]))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, date_item)
            self.table.setItem(row, 1, note_item)
            self.table.setItem(row, 2, QTableWidgetItem())
            self.table.setCellWidget(row, 2, category_label(expense["category"]))
            self.table.setItem(row, 3, amount_item)
            self.table.setItem(row, 4, QTableWidgetItem())
            self.table.setCellWidget(row, 4, self._row_actions(expense))
        # Le tableau prend la hauteur de son contenu : c'est la page entière qui défile.
        self.table.setFixedHeight(self.table.horizontalHeader().height() + ROW_HEIGHT * len(self.items) + 2)

        start = self.page * PAGE_SIZE
        self.range_label.setText(f"{start + 1} à {start + len(self.items)} sur {self.total}")
        self.previous_button.setEnabled(self.page > 0)
        self.next_button.setEnabled(start + len(self.items) < self.total)

    def _row_actions(self, expense: dict) -> QWidget:
        widget = QWidget()
        widget.setObjectName("row")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 0, 12, 0)
        layout.setSpacing(4)
        edit = icon_button("pencil", "Modifier")
        delete = icon_button("trash-2", "Supprimer")
        edit.clicked.connect(lambda: self._edit(expense))
        delete.clicked.connect(lambda: self._delete(expense))
        layout.addStretch()
        layout.addWidget(edit)
        layout.addWidget(delete)
        return widget

    # Actions

    def add_expense(self) -> bool:
        """Ouvre le formulaire d'ajout. Renvoie True si une dépense a été créée."""
        if not self.categories:
            # Cas rare : le formulaire est demandé avant le premier chargement des catégories.
            try:
                self.categories = self.api.categories()
            except ApiError as failure:
                self.notice.show_message(failure.message)
                return False
        dialog = ExpenseDialog(self, self.api, self.categories)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load()
            return True
        return False

    def _edit(self, expense: dict) -> None:
        if ExpenseDialog(self, self.api, self.categories, expense).exec() == QDialog.DialogCode.Accepted:
            self._load()

    def _delete(self, expense: dict) -> None:
        text = (
            f"La dépense de {format_amount(expense['amount'])} du {format_date(expense['date'])} "
            "sera supprimée définitivement."
        )
        if confirm(self, "Supprimer la dépense", text):
            run_async(
                self, lambda: self.api.delete_expense(expense["id"]), lambda _result: self._load(), self.notice.show_message
            )

    def _import(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(self, "Importer des dépenses", "", "Fichiers CSV (*.csv)")
        if not path:
            return
        self.import_button.setEnabled(False)

        def done(report: dict) -> None:
            self.import_button.setEnabled(True)
            text = f"{report['imported']} dépense(s) importée(s)."
            if report["rejected"]:
                first = report["errors"][0]
                text += f" {report['rejected']} ligne(s) ignorée(s), la première à la ligne {first['line']} : {first['message']}."
            self.notice.show_message(text, "warning" if report["rejected"] else "success")
            self._filters_changed()

        def failed(message: str) -> None:
            self.import_button.setEnabled(True)
            self.notice.show_message(message)

        run_async(self, lambda: self.api.import_expenses(path), done, failed)

    def _export(self, file_format: str) -> None:
        filters = self._filters()
        filters.pop("q")
        source = self.csv_button if file_format == "csv" else self.pdf_button
        source.setEnabled(False)

        def done(result: tuple[str, bytes]) -> None:
            source.setEnabled(True)
            filename, content = result
            kind = "Fichiers CSV (*.csv)" if file_format == "csv" else "Documents PDF (*.pdf)"
            target, _filter = QFileDialog.getSaveFileName(self, "Enregistrer l'export", str(Path.home() / filename), kind)
            if not target:
                return
            try:
                Path(target).write_bytes(content)
            except OSError:
                self.notice.show_message("Impossible d'écrire le fichier à cet emplacement.")
                return
            self.notice.show_message(f"Export enregistré : {target}", "success")

        def failed(message: str) -> None:
            source.setEnabled(True)
            self.notice.show_message(message)

        run_async(self, lambda: self.api.export_expenses(file_format, **filters), done, failed)
