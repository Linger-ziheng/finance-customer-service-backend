from typing import Any

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.finance_common import (
    finance_request,
    format_yield_rate,
)


class QueryWealthProductAction(Action):
    name = "action_finance_query_wealth_product"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        product_code = state.task_state.active.slots.get("product_code")

        # GET /api/v1/wealth/products/{product_code} —— 产品详情
        data = await finance_request(
            "GET",
            f"{settings.finance_api_base_url}/api/v1/wealth/products/{product_code}",
        )
        detail = data.get("product_detail") or {}
        nav = data.get("latest_nav") or {}
        open_periods = data.get("open_periods") or []
        notices = data.get("notices") or []

        parts = [
            f"{detail.get('product_name', '未知产品')}"
            f"（{detail.get('product_code', '')}）",
            f"业绩比较基准约 {format_yield_rate(detail.get('expected_yield_rate'))}",
            f"起购金额 {detail.get('min_purchase_amount', '未知')} 元",
            f"币种 {detail.get('currency_code', '未知')}",
        ]
        if nav.get("unit_nav"):
            parts.append(
                f"最新净值 {nav.get('unit_nav')}（{nav.get('nav_date', '')}）"
            )
        parts.append(f"开放期 {len(open_periods)} 个，公告 {len(notices)} 条")

        return ActionResult(slot_updates={
            "product_detail": "，".join(parts),
        })
