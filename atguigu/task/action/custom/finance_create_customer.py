from typing import Any

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.finance_common import (
    finance_request,
    finance_request_no,
    normalize_identity_type,
)


class CreateCustomerAction(Action):
    name = "action_finance_create_customer"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        slots = state.task_state.active.slots
        customer_name = slots.get("customer_name")
        base_url = f"{settings.finance_api_base_url}/api/v1"

        # POST /api/v1/customers —— 代客开户（电话/在线开户）
        create_data = await finance_request(
            "POST",
            f"{base_url}/customers",
            json={
                "request_no": finance_request_no(),
                "customer_type": slots.get("customer_type") or "personal",
                "customer_name": customer_name,
                "branch_code": settings.finance_branch_code,
                "channel_code": settings.finance_channel_code,
            },
        )
        customer_no = create_data["customer_no"]

        # POST /api/v1/customers/{customer_no}/identities —— 录入实名证件
        identity_type = normalize_identity_type(slots.get("customer_id_type"))
        identity_no = slots.get("customer_id_number")
        if identity_type and identity_no:
            await finance_request(
                "POST",
                f"{base_url}/customers/{customer_no}/identities",
                json={
                    "request_no": finance_request_no(),
                    "identity_type": identity_type,
                    "identity_no": identity_no,
                    "legal_name": customer_name,
                },
            )

        # POST /api/v1/customers/{customer_no}/contacts —— 录入手机号/地址
        phone_number = slots.get("phone_number")
        if phone_number:
            await finance_request(
                "POST",
                f"{base_url}/customers/{customer_no}/contacts",
                json={
                    "request_no": finance_request_no(),
                    "contact_type": "mobile",
                    "contact_value": phone_number,
                    "is_primary": True,
                    "contact_name": customer_name,
                },
            )

        address = slots.get("address")
        if address:
            await finance_request(
                "POST",
                f"{base_url}/customers/{customer_no}/contacts",
                json={
                    "request_no": finance_request_no(),
                    "contact_type": "address",
                    "contact_value": address,
                    "is_primary": True,
                    "contact_name": customer_name,
                },
            )

        return ActionResult(slot_updates={
            "customer_no": customer_no,
            "customer_status": create_data.get("customer_status", "active"),
        })
