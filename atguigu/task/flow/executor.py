from wsgiref.util import request_uri

from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.runner import ActionCall, ActionRunner
from atguigu.task.flow.conditions import ConditionEvaluator
from atguigu.task.flow.links import FlowStepLink, ConditionalLink, FallbackLink
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.task.flow.steps import FlowStep, StartFlowStep, CollectSlotStep, ActionFlowStep, ResponseFlowStep, \
    EndFlowStep
from atguigu.task.response.renderer import ResponseRenderer


class FlowExecutor:
    def __init__(
            self,
            condition_evaluator: ConditionEvaluator,
            response_renderer: ResponseRenderer,
            action_runner: ActionRunner,
            max_steps_per_turn: int = 100,
    ) -> None:
        self.condition_evaluator = condition_evaluator
        self.response_renderer = response_renderer
        self.max_steps_per_turn = max_steps_per_turn
        self.action_runner = action_runner

    async def run_task(self, state: DialogueState, flows: FlowCatalog, user_message: UserMessage) -> list[BotMessage]:

        bot_messages: list[BotMessage] = []

        if not state.task_state.active:
            return bot_messages

        for _ in range(self.max_steps_per_turn):

            flow: Flow = flows.get_flow_by_id(state.task_state.active.flow_id)
            step: FlowStep = flow.get_step_by_id(state.task_state.active.step_id)

            if isinstance(step, StartFlowStep):
                self._advance(step, state)
                continue

            if isinstance(step, CollectSlotStep):
                should_wait = await self._run_collect_step(step, state, user_message, bot_messages)
                if should_wait:
                    return bot_messages
                else:
                    self._advance(step, state)
                    continue

            if isinstance(step, ActionFlowStep):
                action_call = ActionCall(step.action, step.args)
                action_result = await self.action_runner.run(action_call, state)
                state.task_state.active.slots.update(action_result.slot_updates)
                self._advance(step, state)
                continue

            if isinstance(step, ResponseFlowStep):
                bot_message = await self.response_renderer.render(step.template, state, user_message)
                bot_messages.append(bot_message)
                self._advance(step, state)
                continue

            if isinstance(step, EndFlowStep):
                state.task_state.active = None
                return bot_messages

    def _advance(self, step: FlowStep, state: DialogueState):
        next_step_id = self._select_next_step(step.next, state)
        state.task_state.active.step_id = next_step_id

    def _select_next_step(self, next: list[FlowStepLink], state: DialogueState) -> str:
        if len(next) == 1:
            return next[0].target
        for link in next:
            if isinstance(link, ConditionalLink):
                # 校验condition是否成立
                result = self.condition_evaluator.evaluate(link.condition, {'slots': state.task_state.active.slots})
                if result:
                    # 成立: return target
                    return link.target
                # 不成立: continue
                continue
            if isinstance(link, FallbackLink):
                return link.target

    async def _run_collect_step(self, step: CollectSlotStep,
                                state: DialogueState,
                                user_message: UserMessage,
                                bot_messages: list[BotMessage]) -> bool:

        slot_value = state.task_state.active.slots.get(step.slot_name)
        if not slot_value:
            self.try_to_fill_slot_from_focused_object(step, state)

        slot_value = state.task_state.active.slots.get(step.slot_name)

        if not slot_value:
            bot_messages.append(await self.response_renderer.render(step.template, state, user_message))
            return True
        else:
            if not step.validation:
                return False
            else:
                result = self.condition_evaluator.evaluate(step.validation.condition,
                                                           {'slots': state.task_state.active.slots})
                if result:
                    return False
                else:
                    state.task_state.active.slots.pop(step.slot_name)
                    bot_messages.append(
                        await self.response_renderer.render(step.validation.failure_template, state, user_message))
                    return True

    def try_to_fill_slot_from_focused_object(self, step, state):

        if not state.shared_state.focused_object:
            return
        if step.slot_name == 'order_number' and state.shared_state.focused_object.type == 'order':
            state.task_state.active.slots.update({step.slot_name: state.shared_state.focused_object.id})
            return
        if step.slot_name == 'product_id' and state.shared_state.focused_object.type == 'product':
            state.task_state.active.slots.update({step.slot_name: state.shared_state.focused_object.id})
            return
