from decimal import Decimal
from typing import Any

from src.core.config import get_binance_settings
from src.exchanges.binance.client import BinanceClient


def get_portfolio_snapshot() -> dict[str, Any]:
    client = BinanceClient(get_binance_settings())
    account_info = client.get_account_info()

    return normalize_account_info(account_info)


def normalize_account_info(account_info: dict[str, Any]) -> dict[str, Any]:
    balances = [
        normalize_balance(balance)
        for balance in account_info.get("balances", [])
        if has_non_zero_balance(balance)
    ]

    return {
        "exchange": "binance",
        "account_type": account_info.get("accountType"),
        "can_trade": account_info.get("canTrade"),
        "can_deposit": account_info.get("canDeposit"),
        "can_withdraw": account_info.get("canWithdraw"),
        "balances": balances,
    }


def normalize_balance(balance: dict[str, Any]) -> dict[str, str]:
    free = Decimal(balance.get("free", "0"))
    locked = Decimal(balance.get("locked", "0"))
    total = free + locked

    return {
        "asset": balance.get("asset", ""),
        "free": format_decimal(free),
        "locked": format_decimal(locked),
        "total": format_decimal(total),
    }


def has_non_zero_balance(balance: dict[str, Any]) -> bool:
    free = Decimal(balance.get("free", "0"))
    locked = Decimal(balance.get("locked", "0"))

    return free + locked > 0


def format_decimal(value: Decimal) -> str:
    return format(value.normalize(), "f")
