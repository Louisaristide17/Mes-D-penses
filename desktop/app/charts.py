"""Graphiques dessinés avec QPainter : histogramme mensuel et anneau de répartition."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from app import theme
from app.format import format_amount, format_compact_amount, format_percent, month_label, short_month_label

OTHERS_COLOR = "#C5CBC8"


def nice_ceiling(value: int) -> int:
    """Arrondit le maximum à une valeur ronde pour graduer l'axe (87 000 devient 90 000)."""
    if value <= 0:
        return 1
    magnitude = 10 ** (len(str(value)) - 1)
    return math.ceil(value / magnitude) * magnitude


def build_slices(rows: list[dict], limit: int = 6) -> list[dict]:
    """Regroupe les plus petites catégories au-delà de `limit` pour garder la légende lisible."""
    slices = [
        {"name": row["category"]["name"], "color": row["category"]["color"], "total": row["total"], "share": row["share"]}
        for row in rows[:limit]
    ]
    rest = rows[limit:]
    if rest:
        slices.append(
            {
                "name": f"{len(rest)} autres",
                "color": OTHERS_COLOR,
                "total": sum(row["total"] for row in rest),
                "share": sum(row["share"] for row in rest),
            }
        )
    return slices


def _axis_font() -> QFont:
    font = QFont("Inter")
    font.setPixelSize(12)
    return font


class MonthlyBarChart(QWidget):
    AXIS_WIDTH = 48
    LABEL_HEIGHT = 26
    TOP = 8

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(240)
        self.setMouseTracking(True)
        self._data: list[dict] = []
        self._selected = ""
        self._bars: list[tuple[QRectF, dict]] = []

    def set_data(self, monthly: list[dict], selected: str) -> None:
        self._data, self._selected = monthly, selected
        self.update()

    def paintEvent(self, _event):
        self._bars = []
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(_axis_font())

        scale_max = nice_ceiling(max(row["total"] for row in self._data))
        chart_height = self.height() - self.LABEL_HEIGHT - self.TOP
        chart_width = self.width() - self.AXIS_WIDTH

        for step in range(3):
            y = self.TOP + chart_height * (1 - step / 2)
            painter.setPen(QPen(QColor(theme.BORDER), 1))
            painter.drawLine(QPointF(self.AXIS_WIDTH, y), QPointF(self.width(), y))
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(
                QRectF(0, y - 10, self.AXIS_WIDTH - 8, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                format_compact_amount(scale_max * step / 2),
            )

        slot = chart_width / len(self._data)
        bar_width = min(slot * 0.6, 48)
        for index, row in enumerate(self._data):
            center = self.AXIS_WIDTH + slot * (index + 0.5)
            height = chart_height * row["total"] / scale_max
            rect = QRectF(center - bar_width / 2, self.TOP + chart_height - height, bar_width, height)
            if height > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(theme.PRIMARY if row["month"] == self._selected else theme.PRIMARY_MUTED))
                painter.drawRoundedRect(rect, 4, 4)
                # Le bas de la barre reste droit : on recouvre les coins inférieurs arrondis.
                if height > 4:
                    painter.drawRect(QRectF(rect.left(), rect.bottom() - 4, bar_width, 4))
            # La zone de survol couvre toute la colonne, même pour une barre très basse.
            self._bars.append((QRectF(center - slot / 2, self.TOP, slot, chart_height), row))
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(
                QRectF(center - slot / 2, self.height() - self.LABEL_HEIGHT + 6, slot, 18),
                Qt.AlignmentFlag.AlignCenter,
                short_month_label(row["month"]),
            )

    def mouseMoveEvent(self, event):
        for rect, row in self._bars:
            if rect.contains(event.position()):
                text = f"{month_label(row['month'])}\n{format_amount(row['total'])}"
                QToolTip.showText(event.globalPosition().toPoint(), text, self)
                return
        QToolTip.hideText()


class DonutChart(QWidget):
    THICKNESS = 26

    def __init__(self):
        super().__init__()
        self.setFixedSize(160, 160)
        self.setMouseTracking(True)
        self._slices: list[dict] = []

    def set_slices(self, slices: list[dict]) -> None:
        self._slices = slices
        self.update()

    def paintEvent(self, _event):
        total = sum(piece["share"] for piece in self._slices)
        if total <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = self.THICKNESS / 2 + 1
        rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)
        # Qt mesure les angles en seizièmes de degré, dans le sens trigonométrique.
        start = 90 * 16
        gap = 24 if len(self._slices) > 1 else 0
        for piece in self._slices:
            span = 360 * 16 * piece["share"] / total
            pen = QPen(QColor(piece["color"]), self.THICKNESS)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, round(start - gap / 2), -round(max(span - gap, 1)))
            start -= span

    def mouseMoveEvent(self, event):
        total = sum(piece["share"] for piece in self._slices)
        center = QPointF(self.width() / 2, self.height() / 2)
        delta = event.position() - center
        distance = math.hypot(delta.x(), delta.y())
        outer = self.width() / 2
        if total <= 0 or not (outer - self.THICKNESS - 2 <= distance <= outer):
            QToolTip.hideText()
            return
        # Angle horaire depuis le haut de l'anneau, de 0 à 1.
        position = (math.degrees(math.atan2(delta.x(), -delta.y())) % 360) / 360
        cumulative = 0.0
        for piece in self._slices:
            cumulative += piece["share"] / total
            if position <= cumulative:
                text = f"{piece['name']}\n{format_amount(piece['total'])} ({format_percent(piece['share'])})"
                QToolTip.showText(event.globalPosition().toPoint(), text, self)
                return
