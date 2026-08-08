from jinja2 import Template
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.clients.llm_client import llm
from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.task.response.models import ResponseTemplate, ResponseMode


class ResponseRenderer:

    async def render(self, template: ResponseTemplate, state: DialogueState, user_message: UserMessage) -> BotMessage:
        if template.mode == ResponseMode.STATIC:
            rendered_text = Template(template.text).render(slots=state.task_state.active.slots)
            return BotMessage(text=rendered_text)

        if template.mode == ResponseMode.REPHRASE:
            rendered_text = Template(template.text).render(slots=state.task_state.active.slots)

            prompt = PromptTemplate.from_template(template.prompt, template_format='jinja2')

            parser = StrOutputParser()

            chain = prompt | llm | parser

            response = await chain.ainvoke({
                'history': HistoryBuilder.build(state.shared_state.current_session().turns),
                'user_message': HistoryBuilder.render_user_message(user_message),
                'current_response': rendered_text
            })
            return BotMessage(text=response)

        if template.mode == ResponseMode.GENERATE:
            prompt = PromptTemplate.from_template(template.prompt, template_format='jinja2')

            parser = StrOutputParser()

            chain = prompt | llm | parser

            response = await chain.ainvoke({
                'history': HistoryBuilder.build(state.shared_state.current_session().turns),
                'user_message': HistoryBuilder.render_user_message(user_message)
            })
            return BotMessage(text=response)
