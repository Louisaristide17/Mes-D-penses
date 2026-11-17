import csv
import io
from collections.abc import Sequence
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Expense, User

PRIMARY = colors.HexColor("#0F5D4A")
TEXT = colors.HexColor("#16201C")
MUTED = colors.HexColor("#5B6661")
BORDER = colors.HexColor("#E4E7E5")
SURFACE = colors.HexColor("#F7F8F7")


def format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " FCFA"


def format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def expenses_to_csv(expenses: Sequence[Expense]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(["date", "categorie", "montant", "note"])
    for expense in expenses:
        writer.writerow([expense.date.isoformat(), expense.category.name, expense.amount, expense.note])
    # Le BOM permet à Excel d'ouvrir le fichier avec les bons accents.
    return buffer.getvalue().encode("utf-8-sig")


def expenses_to_pdf(user: User, expenses: Sequence[Expense], start: date | None, end: date | None) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Relevé de dépenses",
        author=user.name,
    )
    title = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=TEXT)
    meta = ParagraphStyle("meta", fontName="Helvetica", fontSize=10, leading=14, textColor=MUTED)
    cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=12, textColor=TEXT)

    if start and end:
        period = f"Du {format_date(start)} au {format_date(end)}"
    elif start:
        period = f"Depuis le {format_date(start)}"
    elif end:
        period = f"Jusqu'au {format_date(end)}"
    else:
        period = "Toutes les dépenses"

    total = sum(expense.amount for expense in expenses)
    story = [
        Paragraph("Relevé de dépenses", title),
        Spacer(1, 4),
        Paragraph(f"{user.name} · {period}", meta),
        Paragraph(f"{len(expenses)} dépense(s) · Total : {format_amount(total)}", meta),
        Spacer(1, 14),
    ]

    rows = [["Date", "Catégorie", "Note", "Montant"]]
    for expense in expenses:
        rows.append(
            [
                format_date(expense.date),
                expense.category.name,
                Paragraph(expense.note or "-", cell),
                format_amount(expense.amount),
            ]
        )
    rows.append(["", "", "Total", format_amount(total)])

    table = Table(rows, colWidths=[24 * mm, 36 * mm, 76 * mm, 38 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, SURFACE]),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
                ("LINEABOVE", (0, -1), (-1, -1), 1, PRIMARY),
                ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    document.build(story)
    return buffer.getvalue()
