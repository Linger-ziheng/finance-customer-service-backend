from typing import Any

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.finance_common import finance_request


class ListCustomerAccountsAction(Action):
    name = "action_finance_list_customer_accounts"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        customer_no = state.task_state.active.slots.get("customer_no")

        # GET /api/v1/customers/{customer_no}/accounts —— 高频：列出客户名下全部账户
        data = await finance_request(
            "GET",
            f"{settings.finance_api_base_url}/api/v1/customers/{customer_no}/accounts",
        )
        accounts = data.get("list") or []

        if not accounts:
            return ActionResult(slot_updates={
                "account_count": 0,
                "account_list_summary": "该客户名下暂无账户",
            })

        summary = "；".join(
            _format_account(account)
            for account in accounts
        )
        updates: dict[str, Any] = {
            "account_count": len(accounts),
            "account_list_summary": summary,
        }
        # 仅一个账户时直接写入 account_no，供后续查询步骤使用
        if len(accounts) == 1:
            updates["account_no"] = accounts[0]["account_no"]
        return ActionResult(slot_updates=updates)


def _format_account(account: dict[str, Any]) -> str:
    product = account.get("account_product") or {}
    product_name = (
            product.get("product_name")
            or product.get("product_code")
            or "未知产品"
    )
    return (
        f"{account.get('account_no', '未知')}"
        f"（{product_name}，余额 {account.get('balance_amount', '0')} "
        f"{account.get('currency_code', '')}）"
    )
