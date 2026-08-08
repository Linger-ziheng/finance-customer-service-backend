import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from atguigu.clients import http_client
from atguigu.conf.config import settings
from atguigu.domain.message import UserMessage
from atguigu.domain.state import DialogueState


@dataclass
class KnowledgeChunk:
    content: str = ""


class KnowledgeProvider(ABC):
    provider_id: str = ""

    @abstractmethod
    async def retrieve(self, user_message: UserMessage, state: DialogueState) -> list[KnowledgeChunk]:
        pass


class APIProductProvider(KnowledgeProvider):
    provider_id: str = "api.product"

    async def retrieve(self, user_message: UserMessage, state: DialogueState) -> list[KnowledgeChunk]:
        product_id = state.shared_state.focused_object.id
        url = f"{settings.commerce_api_base_url}/products/{product_id}"

        response = await http_client.http_client.get(url)
        data = response.json()["data"]

        chunk = json.dumps(data, ensure_ascii=False, indent=2)

        return [KnowledgeChunk(content=chunk)]


class APIOrderProvider(KnowledgeProvider):
    provider_id: str = "api.order"

    async def retrieve(self, user_message: UserMessage, state: DialogueState) -> list[KnowledgeChunk]:
        order_id = state.shared_state.focused_object.id

        order_url = f"{settings.commerce_api_base_url}/orders/{order_id}"
        logistics_url = f"{settings.commerce_api_base_url}/orders/{order_id}/logistics"

        order_info, logistics_info = await asyncio.gather(
            http_client.http_client.get(order_url),
            http_client.http_client.get(logistics_url)
        )

        chunk = json.dumps({
            "order_detail": order_info.json()["data"],
            "logistics_detail": logistics_info.json().get("data", {"detail": "暂无物流信息"})
        }, ensure_ascii=False, indent=2)

        return [KnowledgeChunk(content=chunk)]


class FAQProvider(KnowledgeProvider):
    provider_id = "faq.default"

    async def retrieve(
            self,
            state: DialogueState,
            user_message: UserMessage,
    ) -> list[KnowledgeChunk]:
        return [
            KnowledgeChunk(content="未检索到相关问题")
        ]


class RAGProvider(KnowledgeProvider):
    provider_id = "rag.default"

    async def retrieve(
            self,
            state: DialogueState,
            user_message: UserMessage,
    ) -> list[KnowledgeChunk]:
        return [
            KnowledgeChunk(content="未检索到相关信息")
        ]
