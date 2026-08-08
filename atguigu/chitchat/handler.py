from atguigu.chitchat.responder import ChitChatResponder
from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState


class ChitChatHandler:

    def __init__(self, chitchat_responder: ChitChatResponder):
        self.chitchat_responder = chitchat_responder

    async def handle(self, user_message: UserMessage, state: DialogueState) -> list[BotMessage]:
        bot_message = await self.chitchat_responder.respond(user_message, state.shared_state.current_session().turns)
        return [bot_message]
