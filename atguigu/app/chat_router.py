import uuid
from dataclasses import asdict

from fastapi import APIRouter
from fastapi.params import Depends

from atguigu.app.dependencies import get_dialogue_service
from atguigu.app.schemas import ChatRequest, ChatResponse, ChatMessage, HistoryResponse, HistoryMessage, ChatObject
from atguigu.domain.message import UserMessage, ProcessResult, MessageType, MessageObject
from atguigu.service.dialogue_service import DialogueService

chat_router = APIRouter()


@chat_router.post("/api/chat")
async def chat(chat_request: ChatRequest,
               dialogue_service: DialogueService = Depends(get_dialogue_service)) -> ChatResponse:
    process_result = await dialogue_service.process_message(_build_user_message(chat_request))
    return _build_chat_response(process_result)


@chat_router.get("/api/chat/history")
async def history(sender_id: str, dialogue_service: DialogueService = Depends(get_dialogue_service)) -> HistoryResponse:
    sessions = await dialogue_service.get_sessions_by_id(sender_id)

    messages: list[HistoryMessage] = []
    for session in sessions:
        for turn in session.turns:
            messages.append(
                HistoryMessage(role='user',
                               text=turn.user_message.text,
                               object=ChatObject(
                                   **asdict(turn.user_message.object)) if turn.user_message.object else None
                               )
            )

            messages.extend([HistoryMessage(role='bot', text=bot_message.text,
                                            object=ChatObject(
                                                **asdict(bot_message.object)) if bot_message.object else None)
                             for bot_message in
                             turn.bot_messages])

    return HistoryResponse(sender_id=sender_id, messages=messages)


def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),
        type=MessageType.TEXT if chat_request.text else MessageType.OBJECT,
        text=chat_request.text,
        object=MessageObject(
            type=chat_request.object.type,
            id=chat_request.object.id,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes
        ) if chat_request.object else None
    )


def _build_chat_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages=[ChatMessage(
            text=message.text,
            object=ChatObject(**asdict(message.object)) if message.object else None
        ) for message in process_result.messages]
    )
