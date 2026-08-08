from typing import Any

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.finance_common import (
    finance_request,
    finance_request_no,
    normalize_contact_type,
)


class UpsertContactAction(Action):
    name = "action_finance_upsert_contact"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        slots = state.task_state.active.slots
        customer_no = slots.get("customer_no")
        contact_type = normalize_contact_type(slots.get("contact_type"))
        contact_value = slots.get("contact_value")

        # POST /api/v1/customers/{customer_no}/contacts —— 高频：代客更新联系方式（UPSERT 去重）
        data = await finance_request(
            "POST",
            f"{settings.finance_api_base_url}/api/v1/customers/{customer_no}/contacts",
            json={
                "request_no": finance_request_no(),
                "contact_type": contact_type,
                "contact_value": contact_value,
                "is_primary": True,
                "contact_name": slots.get("customer_name"),
            },
        )
        verified = "已核实" if data.get("verified_flag") else "待核实"
        contact_result = (
            f"已按 UPSERT 规则保存，联系方式ID {data.get('contact_id')}，"
            f"验证状态：{verified}。"
        )
        return ActionResult(slot_updates={
            "contact_result": contact_result,
        })
