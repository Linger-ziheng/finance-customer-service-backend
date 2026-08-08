"""Finance Data API 公共辅助函数（鉴权头、幂等号、统一调用与类型归一化）。"""

import uuid
from typing import Any

from atguigu.clients import http_client
from atguigu.conf.config import settings


def finance_headers() -> dict[str, str]:
    """代客操作公共请求头，遵循接口文档鉴权约定。"""
    return {
        "Authorization": f"Bearer {settings.finance_operator_no}",
        "X-Channel-Code": settings.finance_channel_code,
        "X-Request-Id": uuid.uuid4().hex,
        "X-Operator-No": settings.finance_operator_no,
    }


def finance_request_no() -> str:
    """写接口幂等控制使用的 request_no。"""
    return uuid.uuid4().hex


async def finance_request(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    """统一调用 Finance Data API：附加鉴权头、校验 HTTP 状态与 code=0，返回 data。"""
    response = await http_client.http_client.request(
        method,
        url,
        headers=finance_headers(),
        **kwargs,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("code") != 0:
        raise RuntimeError(
            f"Finance API error: {body.get('code')} {body.get('message')}"
        )
    return body.get("data") or {}


def normalize_contact_type(value: str | None) -> str:
    """把口语化的联系方式类型归一化为接口编码（mobile/address/email）。"""
    if not value:
        return "unknown"
    text = str(value).strip().lower()
    if text in {
        "mobile",
        "phone",
        "手机",
        "手机号",
        "手机号码",
        "电话",
        "电话号码",
    }:
        return "mobile"
    if text in {"address", "地址", "联系地址"}:
        return "address"
    if text in {"email", "邮箱", "电子邮箱"}:
        return "email"
    return text


def normalize_identity_type(value: str | None) -> str:
    """把证件类型归一化为接口编码（id_card/passport）。"""
    if not value:
        return "unknown"
    text = str(value).strip()
    if text in {"身份证", "居民身份证", "身份证号", "id_card"}:
        return "id_card"
    if text in {"护照", "passport"}:
        return "passport"
    return text


def format_yield_rate(rate: Any) -> str:
    """把预期收益率（小数）格式化为百分比文本。"""
    try:
        return f"{float(rate) * 100:.2f}%"
    except (TypeError, ValueError):
        return "未知"
