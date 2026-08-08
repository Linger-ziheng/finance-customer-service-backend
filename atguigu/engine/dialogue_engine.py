import time
import uuid
from dataclasses import asdict

from atguigu.chitchat.handler import ChitChatHandler
from atguigu.clarify.clarify_responder import ClarifyResponder
from atguigu.domain.message import UserMessage, ProcessResult, MessageType, BotMessage
from atguigu.domain.state import DialogueState, Turn, FocusedObject
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.plan.validator import TurnPlanValidator
from atguigu.task.command.models import SetSlotsCommand
from atguigu.task.flow.models import Flow
from atguigu.task.flow.steps import FlowStep, CollectSlotStep
from atguigu.task.handler import TaskHandler


class DialogueEngine:

    def __init__(self,
                 turn_planner: TurnPlanner,
                 turn_plan_validator: TurnPlanValidator,
                 task_handler: TaskHandler,
                 knowledge_handler: KnowledgeHandler,
                 chitchat_handler: ChitChatHandler,
                 clarify_responder: ClarifyResponder
                 ):
        self.turn_planner = turn_planner
        self.turn_plan_validator = turn_plan_validator
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        self.chitchat_handler = chitchat_handler
        self.clarify_responder = clarify_responder

    async def process_message(self, state: DialogueState, user_message: UserMessage) -> ProcessResult:
        # 准备会话（Session）
        self._prepare_session(state)

        # 准备Turn
        turn = Turn(turn_id=str(uuid.uuid4()), user_message=user_message)

        if user_message.type == MessageType.TEXT:
            messages: list[BotMessage] = await self._handle_text_message(user_message, state)
        else:
            messages: list[BotMessage] = await self._handle_object_message(user_message, state)

        # 组装turn
        turn.bot_messages.extend(messages)

        # 将turn提交到current_session
        state.shared_state.current_session().turns.append(turn)

        # 返回结果
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=messages
        )

    def _prepare_session(self, state: DialogueState):
        now = time.time()
        if not state.shared_state.sessions:
            state.shared_state.start_session()
        else:
            if now - state.shared_state.current_session().last_activity_at > 60 * 60:
                state.shared_state.close_current_session()
                state.clear_context_for_new_session()
                state.shared_state.start_session()
            else:
                state.shared_state.current_session().last_activity_at = now

    async def _handle_text_message(self, user_message: UserMessage, state: DialogueState) -> list[BotMessage]:
        turn_plan: TurnPlan = await self.turn_planner.plan(state, user_message, self.task_handler.flow_catalog,
                                                           self.knowledge_handler.knowledge_intents)
        validation_result: TurnPlanValidationResult = self.turn_plan_validator.validate(turn_plan, state,
                                                                                        self.task_handler.flow_catalog,
                                                                                        self.knowledge_handler.knowledge_intents)
        if not validation_result.valid:
            return await self.clarify_responder.respond(validation_result.reason, state, user_message)

        if turn_plan.task:
            return await self.task_handler.handle(turn_plan.task.commands, state, user_message)

        if turn_plan.knowledge:
            return await self.knowledge_handler.handle(turn_plan.knowledge.intents, state, user_message)

        return await self.chitchat_handler.handle(user_message, state)

    async def _handle_object_message(self, user_message: UserMessage, state: DialogueState) -> list[BotMessage]:

        state.shared_state.focused_object = FocusedObject(**asdict(user_message.object))

        if self._can_fill_slot(state):
            # taskhandler
            if user_message.object.type == 'order':
                slots = {'order_number': user_message.object.id}
            else:
                slots = {'product_id': user_message.object.id}
            command = SetSlotsCommand(command='set_slots', slots=slots)
            return await self.task_handler.handle([command], state, user_message)
        else:
            # clarify_responder
            return await self.clarify_responder.respond(ClarifyReason.OBJECT_REQUIRES_INTENT, state, user_message)

    def _can_fill_slot(self, state: DialogueState) -> bool:
        active_task = state.task_state.active
        if not active_task:
            return False

        flow: Flow = self.task_handler.flow_catalog.get_flow_by_id(active_task.flow_id)
        step: FlowStep = flow.get_step_by_id(active_task.step_id)

        if not isinstance(step, CollectSlotStep):
            return False

        if (step.slot_name == 'order_number') and (state.shared_state.focused_object.type == 'order'):
            return True

        if (step.slot_name == 'product_id') and (state.shared_state.focused_object.type == 'product'):
            return True

        return False
