from typing import Any

from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.task.action.custom.finance_common import (
    finance_request,
    format_yield_rate,
)


class ListWealthProductsAction(Action):
    name = "action_finance_list_wealth_products"

    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        # GET /api/v1/wealth/products —— 高频：在售理财产品（名称/收益率/风险等级）
        data = await finance_request(
            "GET",
            f"{settings.finance_api_base_url}/api/v1/wealth/products",
        )
        products = data.get("list") or []

        if not products:
            return ActionResult(slot_updates={
                "products_summary": "当前没有在售的理财产品。",
            })

        summary = "；".join(
            (
                f"{product.get('product_name', '未知产品')}"
                f"（{product.get('product_code', '')}，"
                f"业绩比较基准约 {format_yield_rate(product.get('expected_yield_rate'))}，"
                f"风险等级 {product.get('risk_level', '未知')}）"
            )
            for product in products
        )
        return ActionResult(slot_updates={
            "products_summary": summary,
        })
