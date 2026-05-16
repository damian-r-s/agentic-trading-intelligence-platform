from decimal import Decimal
from typing import Any

from src.core.config import get_binance_settings
from src.exchanges.binance.client import BinanceClient

DEFAULT_QUOTE_ASSETS = ("USDT", "USDC", "FDUSD", "BTC", "ETH", "BNB", "EUR")


class BinancePortfolioService:
    def __init__(self, client: BinanceClient):
        self.client = client

    def get_portfolio_snapshot(self) -> dict[str, Any]:
        account_info = self.client.get_account_info()

        return self.normalize_account_info(account_info)

    def get_agent_portfolio_state(
        self,
        quote_assets: tuple[str, ...] = DEFAULT_QUOTE_ASSETS,
    ) -> dict[str, Any]:
        account_info = self.client.get_account_info()
        portfolio = self.normalize_account_info(account_info)
        held_assets = {balance["asset"] for balance in portfolio["balances"]}

        exchange_info = self.client.get_exchange_info()
        symbols = self.find_symbols_for_assets(
            exchange_info,
            held_assets,
            set(quote_assets),
        )
        open_orders = self.client.get_open_orders()
        normalized_open_orders = [
            self.normalize_open_order(order) for order in open_orders
        ]

        trades_by_asset = self.get_trades_by_asset(held_assets, symbols)
        open_orders_by_asset = self.group_open_orders_by_asset(
            held_assets,
            normalized_open_orders,
        )

        return {
            **portfolio,
            "symbols_checked": symbols,
            "open_orders": normalized_open_orders,
            "assets": [
                {
                    **balance,
                    "trades": trades_by_asset.get(balance["asset"], []),
                    "open_orders": open_orders_by_asset.get(balance["asset"], []),
                }
                for balance in portfolio["balances"]
            ],
        }

    def get_trades_by_asset(
        self,
        held_assets: set[str],
        symbols: list[dict[str, str]],
    ) -> dict[str, list[dict[str, Any]]]:
        trades_by_asset: dict[str, list[dict[str, Any]]] = {
            asset: [] for asset in held_assets
        }

        for symbol_info in symbols:
            symbol = symbol_info["symbol"]
            trades = self.client.get_my_trades(symbol)

            for trade in trades:
                normalized_trade = self.normalize_trade(trade, symbol_info)

                for asset in self.assets_touched_by_trade(normalized_trade, held_assets):
                    trades_by_asset[asset].append(normalized_trade)

        return trades_by_asset

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

    @staticmethod
    def find_symbols_for_assets(
        exchange_info: dict[str, Any],
        held_assets: set[str],
        quote_assets: set[str],
    ) -> list[dict[str, str]]:
        symbols = []

        for symbol in exchange_info.get("symbols", []):
            base_asset = symbol.get("baseAsset")
            quote_asset = symbol.get("quoteAsset")

            if symbol.get("status") != "TRADING":
                continue

            if base_asset in held_assets and quote_asset in quote_assets:
                symbols.append(
                    {
                        "symbol": symbol["symbol"],
                        "base_asset": base_asset,
                        "quote_asset": quote_asset,
                    }
                )

        return symbols

    @staticmethod
    def normalize_trade(
        trade: dict[str, Any],
        symbol_info: dict[str, str],
    ) -> dict[str, Any]:
        quantity = Decimal(str(trade.get("qty", "0")))
        price = Decimal(str(trade.get("price", "0")))
        quote_quantity = Decimal(str(trade.get("quoteQty", quantity * price)))
        commission = Decimal(str(trade.get("commission", "0")))

        return {
            "id": trade.get("id"),
            "order_id": trade.get("orderId"),
            "symbol": symbol_info["symbol"],
            "base_asset": symbol_info["base_asset"],
            "quote_asset": symbol_info["quote_asset"],
            "side": "BUY" if trade.get("isBuyer") else "SELL",
            "price": BinancePortfolioService.format_decimal(price),
            "quantity": BinancePortfolioService.format_decimal(quantity),
            "quote_quantity": BinancePortfolioService.format_decimal(quote_quantity),
            "commission": BinancePortfolioService.format_decimal(commission),
            "commission_asset": trade.get("commissionAsset"),
            "time": trade.get("time"),
        }

    @staticmethod
    def assets_touched_by_trade(
        trade: dict[str, Any],
        held_assets: set[str],
    ) -> list[str]:
        return [
            asset
            for asset in (trade["base_asset"], trade["quote_asset"])
            if asset in held_assets
        ]

    @staticmethod
    def group_open_orders_by_asset(
        held_assets: set[str],
        open_orders: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {asset: [] for asset in held_assets}

        for order in open_orders:
            asset = BinancePortfolioService.infer_order_asset(order, held_assets)

            if asset:
                grouped[asset].append(order)

        return grouped

    @staticmethod
    def normalize_open_order(order: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": order.get("symbol"),
            "order_id": order.get("orderId"),
            "client_order_id": order.get("clientOrderId"),
            "side": order.get("side"),
            "type": order.get("type"),
            "status": order.get("status"),
            "price": BinancePortfolioService.format_decimal(
                Decimal(str(order.get("price", "0")))
            ),
            "stop_price": BinancePortfolioService.format_decimal(
                Decimal(str(order.get("stopPrice", "0")))
            ),
            "original_quantity": BinancePortfolioService.format_decimal(
                Decimal(str(order.get("origQty", "0")))
            ),
            "executed_quantity": BinancePortfolioService.format_decimal(
                Decimal(str(order.get("executedQty", "0")))
            ),
            "time_in_force": order.get("timeInForce"),
            "time": order.get("time"),
            "update_time": order.get("updateTime"),
            "is_working": order.get("isWorking"),
        }

    @staticmethod
    def infer_order_asset(
        order: dict[str, Any],
        held_assets: set[str],
    ) -> str | None:
        symbol = order.get("symbol") or ""
        matching_assets = [asset for asset in held_assets if symbol.startswith(asset)]

        if matching_assets:
            return max(matching_assets, key=len)

        return None


def create_binance_portfolio_service() -> BinancePortfolioService:
    client = BinanceClient(get_binance_settings())

    return BinancePortfolioService(client)
