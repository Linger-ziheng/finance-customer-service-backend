from pathlib import Path

from atguigu.chitchat.handler import ChitChatHandler
from atguigu.chitchat.responder import ChitChatResponder
from atguigu.clarify.clarify_responder import ClarifyResponder
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.knowledge.intents import KNOWLEDGE_INTENTS
from atguigu.knowledge.providers import APIOrderProvider, APIProductProvider, RAGProvider, FAQProvider
from atguigu.knowledge.registry import KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponder
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.plan.validator import TurnPlanValidator
from atguigu.task.action.builder import register_custom_actions
from atguigu.task.action.registry import ActionRegistry
from atguigu.task.action.runner import ActionRunner
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.conditions import ConditionEvaluator
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.loader import FlowLoader
from atguigu.task.handler import TaskHandler
from atguigu.task.lifecycle.responder import TaskLifecycleResponder
from atguigu.task.response.renderer import ResponseRenderer


def build_dialogue_engine() -> DialogueEngine:
    flow_config_path = Path(__file__).parents[2] / 'flow_config' / 'finance_flows.yml'
    flow_catalog = FlowLoader().load(flow_config_path)

    turn_planner = TurnPlanner()

    turn_plan_validator = TurnPlanValidator()

    command_processor = CommandProcessor()
    task_lifecycle_responder = TaskLifecycleResponder(flow_catalog)

    condition_evaluator = ConditionEvaluator()
    response_renderer = ResponseRenderer()
    registry = ActionRegistry()
    register_custom_actions(registry)
    action_runner = ActionRunner(registry=registry)
    flow_executor = FlowExecutor(
        condition_evaluator=condition_evaluator,
        response_renderer=response_renderer,
        action_runner=action_runner
    )
    task_handler = TaskHandler(
        command_processor=command_processor,
        task_lifecycle_responder=task_lifecycle_responder,
        flow_executor=flow_executor,
        flow_catalog=flow_catalog
    )

    provider_registry = KnowledgeProviderRegistry([
        APIOrderProvider(),
        APIProductProvider(),
        RAGProvider(),
        FAQProvider()
    ])
    knowledge_responder = KnowledgeResponder()
    knowledge_handler = KnowledgeHandler(
        knowledge_intents=KNOWLEDGE_INTENTS,
        provider_registry=provider_registry,
        knowledge_responder=knowledge_responder
    )

    chitchat_handler = ChitChatHandler(ChitChatResponder())

    clarify_responder = ClarifyResponder()
    return DialogueEngine(
        turn_planner=turn_planner,
        turn_plan_validator=turn_plan_validator,
        task_handler=task_handler,
        knowledge_handler=knowledge_handler,
        chitchat_handler=chitchat_handler,
        clarify_responder=clarify_responder
    )
