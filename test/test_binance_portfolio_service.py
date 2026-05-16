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
