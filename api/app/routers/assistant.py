from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import Conversation, Message
from app.schemas import AssistantReply, AssistantRequest, ConversationDetail, ConversationOut, MessageOut
from app.services.agent import run_agent
from app.services.llm import LLMClient, LLMUnavailable, get_llm

router = APIRouter(prefix="/assistant", tags=["Assistant"])

# Nombre de messages précédents transmis au modèle : assez pour suivre le fil, sans alourdir chaque appel.
HISTORY_LIMIT = 12
TITLE_LENGTH = 60


def _get_own_conversation(db, user, conversation_id: int) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable.")
    return conversation


@router.post("/messages", response_model=AssistantReply)
def send_message(
    payload: AssistantRequest,
    user: CurrentUser,
    db: DbSession,
    llm: Annotated[LLMClient | None, Depends(get_llm)],
):
    if llm is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "L'assistant n'est pas configuré sur ce serveur (clé GROQ_API_KEY absente).",
        )

    if payload.conversation_id is None:
        title = payload.message if len(payload.message) <= TITLE_LENGTH else payload.message[: TITLE_LENGTH - 1] + "…"
        conversation = Conversation(user_id=user.id, title=title)
        db.add(conversation)
        db.flush()
        history = []
    else:
        conversation = _get_own_conversation(db, user, payload.conversation_id)
        history = [
            {"role": message.role, "content": message.content} for message in conversation.messages[-HISTORY_LIMIT:]
        ]

    try:
        result = run_agent(db, user, llm, history, payload.message, date.today())
    except LLMUnavailable:
        # Rien n'est enregistré : ni le message, ni une dépense que l'agent aurait créée avant la panne.
        db.rollback()
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "L'assistant est momentanément indisponible. Réessayez dans un instant."
        )

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    db.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=result.reply,
            tool_name=",".join(result.tools_used) or None,
        )
    )
    db.commit()
    return AssistantReply(
        conversation_id=conversation.id,
        reply=result.reply,
        tools_used=result.tools_used,
        data_changed=result.data_changed,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(user: CurrentUser, db: DbSession):
    return db.scalars(
        select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.id.desc()).limit(50)
    ).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def read_conversation(conversation_id: int, user: CurrentUser, db: DbSession):
    conversation = _get_own_conversation(db, user, conversation_id)
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[
            MessageOut(
                role=message.role,
                content=message.content,
                tools_used=message.tool_name.split(",") if message.tool_name else [],
                created_at=message.created_at,
            )
            for message in conversation.messages
        ],
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, user: CurrentUser, db: DbSession):
    db.delete(_get_own_conversation(db, user, conversation_id))
    db.commit()
