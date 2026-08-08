from typing import Any

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.finance_common import finance_request


class QueryAccountAction(Action):
    name = "action_finance_query_account"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        account_no = state.task_state.active.slots.get("account_no")

        # GET /api/v1/accounts/{account_no} —— 高频：余额、冻结金额、账户产品
        data = await finance_request(
            "GET",
            f"{settings.finance_api_base_url}/api/v1/accounts/{account_no}",
        )
        frozen_amount = str(data.get("frozen_amount") or "0")
        product = data.get("account_product") or {}
        product_name = (
                product.get("product_name")
                or product.get("product_code")
                or "未知"
        )
        return ActionResult(slot_updates={
            "balance": str(data.get("balance_amount") or "0"),
            "frozen_amount": frozen_amount,
            "account_product": product_name,
            "account_status": data.get("account_status") or "未知",
            # 账户接口不直接返回冻结原因，有冻结时给出核实指引
            "freeze_reason": (
                "具体冻结原因请以资金冻结或流水记录进一步核实"
                if frozen_amount not in {"0", "0.00"}
                else ""
            ),
        })
