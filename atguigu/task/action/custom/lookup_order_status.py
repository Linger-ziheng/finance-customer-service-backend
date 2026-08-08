from typing import Any

from atguigu.clients import http_client
from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class LookupOrderStatusAction(Action):
    name = "action_lookup_order_status"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        order_number = state.task_state.active.slots.get(
            "order_number"
        )
        url = (
            f"{settings.commerce_api_base_url}"
            f"/orders/{order_number}"
        )
        response = await http_client.http_client.get(url)
        payload = response.json()["data"]

        return ActionResult(slot_updates={
            "order_status": (
                    payload.get("status_desc")
                    or payload.get("status")
                    or "未知"
            ),
            "order_summary": (
                f"订单金额 ¥{payload['amount']}。"
            ),
        })
