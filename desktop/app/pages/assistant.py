from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from app import theme
from app.api import ApiClient
from app.tasks import run_async
from app.widgets import Card, Notice, Page, button, clear_layout, icon_label, label, remove_widget, separator

SUGGESTIONS = [
    "Combien ai-je dépensé ce mois-ci ?",
    "Quelle est ma plus grosse dépense du mois ?",
    "Où en sont mes budgets ?",
    "Ajoute 2 000 FCFA de taxi",
    "Comment mieux tenir mon budget ?",
]

# Noms des outils renvoyés par l'API, traduits pour l'utilisateur.
TOOL_LABELS = {
    "total_depenses": "total des dépenses",
    "depenses_par_categorie": "répartition par catégorie",
    "lister_depenses": "liste des dépenses",
    "etat_budgets": "état des budgets",
    "ajouter_depense": "ajout d'une dépense",
}

BUBBLE_WIDTH = 520


def bubble(text: str, role: str, caption: str | None = None) -> QWidget:
    """Message de la conversation : à droite et en vert pour l'utilisateur, à gauche pour l'assistant."""
    frame = QFrame()
    frame.setObjectName("bubbleUser" if role == "user" else "bubbleAssistant")
    frame.setMaximumWidth(BUBBLE_WIDTH)
    inner = QVBoxLayout(frame)
    inner.setContentsMargins(14, 10, 14, 10)
    inner.setSpacing(8)
    content = QLabel(text)
    content.setWordWrap(True)
    content.setTextFormat(Qt.TextFormat.PlainText)
    content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    # Un texte à retour automatique se réduit à sa largeur minimale s'il n'est pas contraint :
    # on lui réserve la largeur de sa ligne la plus longue, dans la limite de la bulle.
    content.ensurePolished()
    longest = max(content.fontMetrics().horizontalAdvance(line) for line in text.split("\n"))
    content.setMinimumWidth(min(longest + 4, BUBBLE_WIDTH - 28))
    inner.addWidget(content)
    if caption:
        inner.addWidget(separator())
        inner.addWidget(label(caption, "small", wrap=True))

    row = QWidget()
    row.setObjectName("row")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    if role == "user":
        layout.addStretch()
        layout.addWidget(frame)
    else:
        layout.addWidget(frame)
        layout.addStretch()
    return row


class AssistantPage(Page):
    def __init__(self, api: ApiClient):
        super().__init__("Assistant", "Interrogez vos dépenses, ajoutez-en une, ou posez une question générale.", max_width=820)
        self.api = api
        self.conversation_id: int | None = None
        self.waiting = False

        self.reset_button = button("Nouvelle conversation", icon_name="plus")
        self.reset_button.clicked.connect(self.reset)
        self.actions.addWidget(self.reset_button)

        card = Card(padding=0, spacing=0)
        self.messages_area = QScrollArea()
        self.messages_area.setObjectName("chatArea")
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_area.setMinimumHeight(380)
        holder = QWidget()
        holder.setObjectName("chatHolder")
        self.messages = QVBoxLayout(holder)
        self.messages.setContentsMargins(24, 24, 24, 24)
        self.messages.setSpacing(12)
        self.messages.addStretch()
        self.messages_area.setWidget(holder)
        card.body.addWidget(self.messages_area, 1)

        self.notice = Notice()
        notice_row = QVBoxLayout()
        notice_row.setContentsMargins(24, 0, 24, 12)
        notice_row.addWidget(self.notice)
        card.body.addLayout(notice_row)
        card.body.addWidget(separator())

        form = QHBoxLayout()
        form.setContentsMargins(24, 16, 24, 16)
        form.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Écrivez votre question")
        self.input.setMaxLength(1000)
        self.send_button = button("Envoyer", "primary")
        form.addWidget(self.input, 1)
        form.addWidget(self.send_button)
        card.body.addLayout(form)
        self.content.addWidget(card, 1)

        self.input.returnPressed.connect(lambda: self.send(self.input.text()))
        self.send_button.clicked.connect(lambda: self.send(self.input.text()))
        self.reset()

    def reload(self) -> None:
        self.input.setFocus()

    def reset(self) -> None:
        self.conversation_id = None
        self.notice.clear()
        self._clear_messages()
        self._show_welcome()
        self.reset_button.setVisible(False)

    # Affichage

    def _clear_messages(self) -> None:
        clear_layout(self.messages)
        self.messages.addStretch()

    def _show_welcome(self) -> None:
        welcome = QWidget()
        welcome.setObjectName("row")
        layout = QVBoxLayout(welcome)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(icon_label("messages-square", theme.MUTED, 28), 0, Qt.AlignmentFlag.AlignHCenter)
        heading = label("Que voulez-vous savoir ?", "section")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        text = label(
            "Les chiffres viennent de vos dépenses et de vos budgets. Pour le reste, l'assistant répond\n"
            "à partir de ses connaissances générales, sans accès à internet.",
            "muted",
        )
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text)
        layout.addSpacing(8)
        for suggestion in SUGGESTIONS:
            chip = button(suggestion)
            chip.clicked.connect(lambda _checked=False, value=suggestion: self.send(value))
            layout.addWidget(chip, 0, Qt.AlignmentFlag.AlignHCenter)
        self.messages.insertWidget(0, welcome)
        self.messages.insertStretch(0)

    def _append(self, widget: QWidget) -> None:
        self.messages.addWidget(widget)
        # Le défilement attend que la mise en page ait pris en compte le nouveau message.
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        bar = self.messages_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    # Échange avec l'API

    def send(self, text: str) -> None:
        message = text.strip()
        if not message or self.waiting:
            return
        if self.conversation_id is None and not self.reset_button.isVisible():
            self._clear_messages()
        self.reset_button.setVisible(True)
        self.notice.clear()
        self.input.clear()
        self._set_waiting(True)

        question = bubble(message, "user")
        pending = bubble("L'assistant rédige sa réponse...", "assistant")
        self._append(question)
        self._append(pending)
        conversation_id = self.conversation_id

        def received(answer: dict) -> None:
            remove_widget(pending)
            self.conversation_id = answer["conversation_id"]
            caption = None
            if answer["tools_used"]:
                prefix = "Action : " if answer["data_changed"] else "Calculé à partir de : "
                caption = prefix + ", ".join(TOOL_LABELS.get(tool, tool) for tool in answer["tools_used"])
            self._append(bubble(answer["reply"], "assistant", caption))
            # Rien à rafraîchir ici après un ajout : chaque écran recharge ses données quand on y revient.
            self._set_waiting(False)

        def failed(error: str) -> None:
            # La question est remise dans le champ : l'utilisateur peut la renvoyer sans la retaper.
            remove_widget(pending)
            remove_widget(question)
            self.input.setText(message)
            self.notice.show_message(error)
            self._set_waiting(False)

        run_async(self, lambda: self.api.ask_assistant(message, conversation_id), received, failed)

    def _set_waiting(self, waiting: bool) -> None:
        self.waiting = waiting
        self.send_button.setEnabled(not waiting)
        if not waiting:
            self.input.setFocus()
