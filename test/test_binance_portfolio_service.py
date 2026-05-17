from src.exchanges.binance.service import BinancePortfolioService


class FakeBinanceClient:
    def get_account_info(self):
        return {
            "accountType": "SPOT",
            "canTrade": True,
            "canDeposit": True,
            "canWithdraw": False,
            "balances": [
                {"asset": "BTC", "free": "0.01000000", "locked": "0.00000000"},
                {"asset": "ETH", "free": "0", "locked": "0"},
            ],
        }

    def get_exchange_info(self):
        return {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                }
            ]
        }

    def get_my_trades(self, symbol):
        assert symbol == "BTCUSDT"

        return [
            {
                "id": 1,
                "orderId": 100,
                "price": "60000.00000000",
                "qty": "0.01000000",
                "quoteQty": "600.00000000",
                "commission": "0.00001000",
                "commissionAsset": "BTC",
                "time": 1710000000000,
                "isBuyer": True,
            },
            {
                "id": 2,
                "orderId": 101,
                "price": "70000.00000000",
                "qty": "0.00500000",
                "quoteQty": "350.00000000",
                "commission": "0.35000000",
                "commissionAsset": "USDT",
                "time": 1720000000000,
                "isBuyer": False,
            },
        ]

    def get_open_orders(self):
        return [
            {
                "symbol": "BTCUSDT",
                "orderId": 200,
                "clientOrderId": "sell-btc-at-price",
                "side": "SELL",
                "type": "LIMIT",
                "status": "NEW",
                "price": "80000.00000000",
                "stopPrice": "0.00000000",
                "origQty": "0.00500000",
                "executedQty": "0.00000000",
                "timeInForce": "GTC",
                "time": 1730000000000,
                "updateTime": 1730000000000,
                "isWorking": True,
            }
        ]

    def get_trade_fee(self, symbol=None):
        assert symbol in {None, "BTCUSDT"}

        fees = [
            {
                "symbol": "BTCUSDT",
                "makerCommission": "0.00100000",
                "takerCommission": "0.00100000",
            }
        ]

        if symbol:
            return [fee for fee in fees if fee["symbol"] == symbol]

        return fees

    def get_ticker_prices(self, symbols):
        prices = {"BTCUSDT": "60000.00"}
        return [{"symbol": s, "price": prices[s]} for s in symbols if s in prices]


def test_portfolio_snapshot_uses_injected_client():
    service = BinancePortfolioService(FakeBinanceClient())

    snapshot = service.get_portfolio_snapshot()

    assert snapshot == {
        "exchange": "binance",
        "account_type": "SPOT",
        "can_trade": True,
        "can_deposit": True,
        "can_withdraw": False,
        "balances": [
            {
                "asset": "BTC",
                "free": "0.01",
                "locked": "0",
                "total": "0.01",
            }
        ],
    }


def test_agent_portfolio_state_includes_current_prices():
    service = BinancePortfolioService(FakeBinanceClient())

    state = service.get_agent_portfolio_state()

    assert state["current_prices"]["BTC"] == "60000"
    assert state["current_prices"]["USDT"] == "1"


def test_agent_portfolio_state_includes_trades_and_open_orders():
    service = BinancePortfolioService(FakeBinanceClient())

    state = service.get_agent_portfolio_state()

    assert state["symbols_checked"] == [
        {
            "symbol": "BTCUSDT",
            "base_asset": "BTC",
            "quote_asset": "USDT",
        }
    ]
    assert state["open_orders"] == [
        {
            "symbol": "BTCUSDT",
            "order_id": 200,
            "client_order_id": "sell-btc-at-price",
            "side": "SELL",
            "type": "LIMIT",
            "status": "NEW",
            "price": "80000",
            "stop_price": "0",
            "original_quantity": "0.005",
            "executed_quantity": "0",
            "time_in_force": "GTC",
            "time": 1730000000000,
            "update_time": 1730000000000,
            "is_working": True,
        }
    ]
    assert state["trade_fees"] == [
        {
            "symbol": "BTCUSDT",
            "maker_commission": "0.001",
            "taker_commission": "0.001",
        }
    ]
    assert state["assets"] == [
        {
            "asset": "BTC",
            "free": "0.01",
            "locked": "0",
            "total": "0.01",
            "trades": [
                {
                    "id": 1,
                    "order_id": 100,
                    "symbol": "BTCUSDT",
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "side": "BUY",
                    "price": "60000",
                    "quantity": "0.01",
                    "quote_quantity": "600",
                    "commission": "0.00001",
                    "commission_asset": "BTC",
                    "time": 1710000000000,
                },
                {
                    "id": 2,
                    "order_id": 101,
                    "symbol": "BTCUSDT",
                    "base_asset": "BTC",
                    "quote_asset": "USDT",
                    "side": "SELL",
                    "price": "70000",
                    "quantity": "0.005",
                    "quote_quantity": "350",
                    "commission": "0.35",
                    "commission_asset": "USDT",
                    "time": 1720000000000,
                },
            ],
            "open_orders": [
                {
                    "symbol": "BTCUSDT",
                    "order_id": 200,
                    "client_order_id": "sell-btc-at-price",
                    "side": "SELL",
                    "type": "LIMIT",
                    "status": "NEW",
                    "price": "80000",
                    "stop_price": "0",
                    "original_quantity": "0.005",
                    "executed_quantity": "0",
                    "time_in_force": "GTC",
                    "time": 1730000000000,
                    "update_time": 1730000000000,
                    "is_working": True,
                }
            ],
        }
    ]


def test_trade_fees_are_normalized():
    service = BinancePortfolioService(FakeBinanceClient())

    assert service.get_trade_fees("BTCUSDT") == [
        {
            "symbol": "BTCUSDT",
            "maker_commission": "0.001",
            "taker_commission": "0.001",
        }
    ]
