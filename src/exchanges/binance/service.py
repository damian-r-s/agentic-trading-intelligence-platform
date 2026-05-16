from decimal import Decimal
from typing import Any

from src.core.config import get_binance_settings
from src.exchanges.binance.client import BinanceClient


class BinancePortfolioService:
    def __init__(self, client: BinanceClient):
        self.client = client

    def get_portfolio_snapshot(self) -> dict[str, Any]:
        account_info = self.client.get_account_info()

        return self.normalize_account_info(account_info)

    @staticmethod
    def normalize_account_info(account_info: dict[str, Any]) -> dict[str, Any]:
        balances = [
            BinancePortfolioService.normalize_balance(balance)
            for balance in account_info.get("balances", [])
            if BinancePortfolioService.has_non_zero_balance(balance)
        ]

        return {
            "exchange": "binance",
            "account_type": account_info.get("accountType"),
            "can_trade": account_info.get("canTrade"),
            "can_deposit": account_info.get("canDeposit"),
            "can_withdraw": account_info.get("canWithdraw"),
            "balances": balances,
        }

    @staticmethod
    def normalize_balance(balance: dict[str, Any]) -> dict[str, str]:
        free = Decimal(balance.get("free", "0"))
        locked = Decimal(balance.get("locked", "0"))
        total = free + locked

        return {
            "asset": balance.get("asset", ""),
            "free": BinancePortfolioService.format_decimal(free),
            "locked": BinancePortfolioService.format_decimal(locked),
            "total": BinancePortfolioService.format_decimal(total),
        }

    @staticmethod
    def has_non_zero_balance(balance: dict[str, Any]) -> bool:
        free = Decimal(balance.get("free", "0"))
        locked = Decimal(balance.get("locked", "0"))

        return free + locked > 0

    @staticmethod
    def format_decimal(value: Decimal) -> str:
        return format(value.normalize(), "f")


def create_binance_portfolio_service() -> BinancePortfolioService:
    client = BinanceClient(get_binance_settings())

    return BinancePortfolioService(client)
