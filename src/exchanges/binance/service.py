from dataclasses import replace
from decimal import Decimal
from typing import Any
from concurrent.futures import ThreadPoolExecutor

from src.core.config import get_binance_settings
from src.exchanges.binance.client import BinanceClient, BinanceConfigurationError
from src.core.cache import CacheService
from src.core.databases.repositories.users_repo import get_binance_credentials

DEFAULT_QUOTE_ASSETS = ("USDT", "USDC", "FDUSD", "BTC", "ETH", "BNB", "EUR")
STABLECOIN_ASSETS = {"USDT", "USDC", "FDUSD", "BUSD", "DAI", "TUSD"}

class BinancePortfolioService:
    def __init__(self, client: BinanceClient, cache: CacheService):
        self.client = client
        self.cache  = cache

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

        exchange_info = self.cache.get_exchange_info()
        symbols = self.find_symbols_for_assets(
            exchange_info,
            held_assets,
            set(quote_assets),
        )

        with ThreadPoolExecutor() as executor:
            f_orders = executor.submit(self.client.get_open_orders)
            f_fees   = executor.submit(self.get_trade_fees_for_symbols, [s["symbol"] for s in symbols])
            f_trades = executor.submit(self.get_trades_by_asset, held_assets, symbols)
            f_prices = executor.submit(self.get_prices_in_usdt, symbols)

            open_orders      = f_orders.result()
            trade_fees       = f_fees.result()
            trades_by_asset  = f_trades.result()
            current_prices   = f_prices.result()

        portfolio["balances"] = [
            b for b in portfolio["balances"]
            if Decimal(b["total"]) * Decimal(current_prices.get(b["asset"], "0")) >= 100
        ]
        held_assets = {b["asset"] for b in portfolio["balances"]}

        normalized_open_orders = [
            self.normalize_open_order(order) for order in open_orders
        ]       
        open_orders_by_asset = self.group_open_orders_by_asset(held_assets, normalized_open_orders)

        return {
            **portfolio,
            "symbols_checked": symbols,
            "open_orders": normalized_open_orders,
            "trade_fees": trade_fees,
            "current_prices": current_prices,
            "assets": [
                {
                    **balance,
                    "trades": trades_by_asset.get(balance["asset"], []),
                    "open_orders": open_orders_by_asset.get(balance["asset"], []),
                }
                for balance in portfolio["balances"]
            ],
        }

    def get_prices_in_usdt(self, symbols: list[dict[str, str]]) -> dict[str, str]:
        prices: dict[str, Decimal] = {coin: Decimal("1") for coin in STABLECOIN_ASSETS}

        symbol_names = [s["symbol"] for s in symbols]

        non_stable_quotes = {
            s["quote_asset"]
            for s in symbols
            if s["quote_asset"] not in STABLECOIN_ASSETS
        }
        cross_symbols = [f"{q}USDT" for q in non_stable_quotes]
        all_symbols = list(set(symbol_names) | set(cross_symbols))

        if not all_symbols:
            return {k: BinancePortfolioService.format_decimal(v) for k, v in prices.items()}

        ticker_data = self.client.get_ticker_prices(all_symbols)
        price_by_symbol: dict[str, Decimal] = {
            t["symbol"]: Decimal(str(t["price"]))
            for t in ticker_data
            if "symbol" in t and "price" in t
        }

        # Price non-stablecoin quote assets via their USDT cross-pair
        for quote in non_stable_quotes:
            pair = f"{quote}USDT"
            if pair in price_by_symbol:
                prices[quote] = price_by_symbol[pair]

        # First pass: assets with direct stablecoin or already-priced quote
        for symbol_info in symbols:
            base = symbol_info["base_asset"]
            quote = symbol_info["quote_asset"]
            sym = symbol_info["symbol"]
            if base not in prices and quote in prices and sym in price_by_symbol:
                prices[base] = price_by_symbol[sym] * prices[quote]

        # Second pass: assets whose quote was resolved in first pass
        for symbol_info in symbols:
            base = symbol_info["base_asset"]
            quote = symbol_info["quote_asset"]
            sym = symbol_info["symbol"]
            if base not in prices and quote in prices and sym in price_by_symbol:
                prices[base] = price_by_symbol[sym] * prices[quote]

        return {k: BinancePortfolioService.format_decimal(v) for k, v in prices.items()}

    def get_trades_by_asset(
        self,
        held_assets: set[str],
        symbols: list[dict[str, str]],
    ) -> dict[str, list[dict[str, Any]]]:
        trades_by_asset: dict[str, list[dict[str, Any]]] = {
            asset: [] for asset in held_assets
        }

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.client.get_my_trades, s["symbol"]): s
                for s in symbols
            }
            for future, symbol_info in futures.items():
                for trade in future.result():
                    normalized_trade = self.normalize_trade(trade, symbol_info)
                    for asset in self.assets_touched_by_trade(normalized_trade, held_assets):
                        trades_by_asset[asset].append(normalized_trade)

        return trades_by_asset

    def get_trade_fees(self, symbol: str | None = None) -> list[dict[str, str]]:
        fees = self.client.get_trade_fee(symbol)

        return [self.normalize_trade_fee(fee) for fee in fees]

    def get_trade_fees_for_symbols(self, symbols: list[str]) -> list[dict[str, str]]:
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.get_trade_fees, symbol) for symbol in symbols]
            return [fee for future in futures for fee in future.result()]

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
    def normalize_trade_fee(fee: dict[str, Any]) -> dict[str, str]:
        maker_commission = Decimal(str(fee.get("makerCommission", "0")))
        taker_commission = Decimal(str(fee.get("takerCommission", "0")))

        return {
            "symbol": fee.get("symbol", ""),
            "maker_commission": BinancePortfolioService.format_decimal(
                maker_commission
            ),
            "taker_commission": BinancePortfolioService.format_decimal(
                taker_commission
            ),
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


def create_binance_portfolio_service(user_id: int) -> BinancePortfolioService:
    credentials = get_binance_credentials(user_id)
    if credentials is None:
        raise BinanceConfigurationError(
            "No Binance API key configured — set one in Settings first"
        )

    api_key, api_secret = credentials
    settings = replace(get_binance_settings(), api_key=api_key, api_secret=api_secret)
    client = BinanceClient(settings=settings)
    cache = CacheService(client=client)
    return BinancePortfolioService(client, cache)
