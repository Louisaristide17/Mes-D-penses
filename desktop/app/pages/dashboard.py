from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from app import theme
from app.api import ApiClient
from app.charts import DonutChart, MonthlyBarChart, build_slices
from app.format import format_amount, format_date, format_percent, month_label
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
    icon_label,
    label,
    separator,
)


def stat_card(title: str, value: str, note: QWidget | str, small: bool = False) -> Card:
    card = Card(spacing=8)
    card.body.addWidget(label(title, "label"))
    card.body.addWidget(label(value, "stat-small" if small else "stat"))
    card.body.addWidget(label(note, "small") if isinstance(note, str) else note)
    card.body.addStretch()
    return card


def variation_note(variation: float | None) -> QWidget:
    if variation is None:
        return label("Pas de dépense le mois précédent", "small")
    rising = variation > 0
    row = QWidget()
    row.setObjectName("row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    # Une hausse des dépenses est signalée en rouge, une baisse en vert.
    color = theme.DANGER if rising else theme.SUCCESS
    layout.addWidget(icon_label("trending-up" if rising else "trending-down", color, 14))
    layout.addWidget(label(f"{'+' if rising else '-'}{format_percent(abs(variation))}", "trend-up" if rising else "trend-down"))
    layout.addWidget(label("par rapport au mois précédent", "small"))
    layout.addStretch()
    return row


def expense_row(expense: dict) -> QWidget:
    row = QWidget()
    row.setObjectName("row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(24, 10, 24, 10)
    layout.setSpacing(12)
    layout.addWidget(CategoryIcon(expense["category"], 32))
    texts = QVBoxLayout()
    texts.setSpacing(0)
    texts.addWidget(label(expense["note"] or expense["category"]["name"], "strong"))
    texts.addWidget(label(f"{expense['category']['name']} · {format_date(expense['date'])}", "small"))
    layout.addLayout(texts, 1)
    layout.addWidget(label(format_amount(expense["amount"]), "strong"))
    return row


class DashboardPage(Page):
    add_requested = Signal()
    see_all_requested = Signal()

    def __init__(self, api: ApiClient):
        super().__init__("Tableau de bord", "")
        self.api = api
        self.month_picker = MonthPicker()
        add_button = button("Nouvelle dépense", "primary", "plus")
        self.actions.addWidget(self.month_picker)
        self.actions.addWidget(add_button)
        self.notice = Notice()
        self.content.addWidget(self.notice)
        self.body = QVBoxLayout()
        self.body.setSpacing(16)
        self.content.addLayout(self.body)
        self.content.addStretch()

        self.month_picker.changed.connect(lambda _month: self.reload())
        add_button.clicked.connect(self.add_requested.emit)

    def reload(self) -> None:
        month = self.month_picker.month
        self.subtitle.setText(f"Vos dépenses de {month_label(month).lower()}.")
        self.notice.clear()

        def received(summary: dict) -> None:
            # Si l'utilisateur a changé de mois entre-temps, cette réponse est périmée.
            if summary["month"] == self.month_picker.month:
                self._render(summary)

        run_async(self, lambda: self.api.dashboard(month), received, self.notice.show_message)

    def _render(self, data: dict) -> None:
        clear_layout(self.body)
        top = data["by_category"][0] if data["by_category"] else None

        stats = QHBoxLayout()
        stats.setSpacing(16)
        stats.addWidget(stat_card("Total du mois", format_amount(data["total"]), variation_note(data["variation"])), 1)
        average = f"{format_amount(round(data['total'] / data['count']))} en moyenne" if data["count"] else "Aucune saisie ce mois-ci"
        stats.addWidget(stat_card("Nombre de dépenses", str(data["count"]), average), 1)
        stats.addWidget(
            stat_card(
                "Premier poste de dépense",
                top["category"]["name"] if top else "Aucun",
                f"{format_amount(top['total'])}, soit {format_percent(top['share'])} du total"
                if top
                else "Ajoutez une dépense pour le voir apparaître",
                small=True,
            ),
            1,
        )
        self.body.addLayout(stats)

        for alert in data["alerts"]:
            name = alert["category"]["name"]
            if alert["level"] == "depasse":
                self.body.addWidget(Notice(f"Budget {name} dépassé de {format_amount(-alert['remaining'])}.", "error"))
            else:
                text = f"Budget {name} consommé à {format_percent(alert['ratio'])} : il reste {format_amount(alert['remaining'])}."
                self.body.addWidget(Notice(text, "warning"))

        charts = QHBoxLayout()
        charts.setSpacing(16)
        charts.addWidget(self._monthly_card(data), 3)
        charts.addWidget(self._breakdown_card(data), 2)
        self.body.addLayout(charts)
        self.body.addWidget(self._recent_card(data))

    def _monthly_card(self, data: dict) -> Card:
        card = Card()
        card.body.addWidget(label("Évolution sur six mois", "section"))
        chart = MonthlyBarChart()
        chart.set_data(data["monthly"], data["month"])
        card.body.addWidget(chart)
        return card

    def _breakdown_card(self, data: dict) -> Card:
        card = Card()
        card.body.addWidget(label("Répartition par catégorie", "section"))
        if not data["by_category"]:
            card.body.addWidget(label("Aucune dépense à répartir pour ce mois.", "muted"))
            card.body.addStretch()
            return card
        slices = build_slices(data["by_category"])
        row = QHBoxLayout()
        row.setSpacing(24)
        donut = DonutChart()
        donut.set_slices(slices)
        row.addWidget(donut, 0, Qt.AlignmentFlag.AlignVCenter)
        legend = QGridLayout()
        legend.setVerticalSpacing(8)
        legend.setHorizontalSpacing(8)
        for index, piece in enumerate(slices):
            swatch = QWidget()
            swatch.setFixedSize(8, 8)
            swatch.setStyleSheet(f"background: {piece['color']}; border-radius: 2px;")
            legend.addWidget(swatch, index, 0, Qt.AlignmentFlag.AlignVCenter)
            legend.addWidget(label(piece["name"]), index, 1)
            legend.addWidget(label(format_percent(piece["share"]), "small"), index, 2, Qt.AlignmentFlag.AlignRight)
        legend.setColumnStretch(1, 1)
        row.addLayout(legend, 1)
        card.body.addLayout(row)
        card.body.addStretch()
        return card

    def _recent_card(self, data: dict) -> Card:
        card = Card(padding=0, spacing=0)
        header = QHBoxLayout()
        header.setContentsMargins(24, 16, 24, 16)
        header.addWidget(label("Dernières dépenses", "section"), 1)
        if data["recent"]:
            see_all = button("Tout voir", "link")
            see_all.clicked.connect(self.see_all_requested.emit)
            header.addWidget(see_all)
        card.body.addLayout(header)
        card.body.addWidget(separator())
        if not data["recent"]:
            add_button = button("Nouvelle dépense", "primary", "plus")
            add_button.clicked.connect(self.add_requested.emit)
            card.body.addWidget(
                EmptyState(
                    "receipt",
                    "Aucune dépense ce mois-ci",
                    "Ajoutez votre première dépense : le tableau de bord se remplira au fur et à mesure.",
                    add_button,
                )
            )
            return card
        for index, expense in enumerate(data["recent"]):
            if index:
                card.body.addWidget(separator())
            card.body.addWidget(expense_row(expense))
        return card
