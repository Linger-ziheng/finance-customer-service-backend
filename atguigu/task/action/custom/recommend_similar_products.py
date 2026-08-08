from typing import Any

from atguigu.clients import http_client
from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class RecommendSimilarProductsAction(Action):
    name = "action_recommend_similar_products"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        product_id = state.task_state.active.slots.get(
            "product_id"
        )
        label = product_id or "这件商品"

        url = (
            f"{settings.commerce_api_base_url}"
            f"/products/{product_id}"
        )
        response = await http_client.http_client.get(url)
        payload = response.json()["data"]

        if payload:
            title = str(payload.get("title") or "").strip()
            label = title or label

        summary = (
            f'我已经收到你对"{label}"的相似商品推荐需求。'
            "不过当前版本还没有接入正式的推荐系统，"
            "稍后可以继续补上这部分能力。"
        )
        return ActionResult(slot_updates={
            "recommendation_summary": summary
        })
