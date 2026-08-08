from typing import Any

from atguigu.clients import http_client
from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class LookupLogisticsAction(Action):
    name = "action_lookup_logistics"

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
            f"/orders/{order_number}/logistics"
        )
        response = await http_client.http_client.get(url)
        payload = response.json().get("data", {"detail": "未知"})

        return ActionResult(slot_updates={
            "tracking_number": (
                    payload.get("tracking_number")
                    or "未知"
            ),
            "logistics_company": (
                    payload.get("logistics_company")
                    or "未知"
            ),
            "logistics_status": (
                    payload.get("status_desc")
                    or payload.get("status")
                    or "未知"
            ),
        })
