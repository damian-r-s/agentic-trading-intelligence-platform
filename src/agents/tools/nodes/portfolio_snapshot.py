from src.agents.tools.state import TradingDecisionState
from src.core.logging import get_logger
from src.exchanges.binance.market_data import create_binance_market_data_service
from src.exchanges.binance.service import create_binance_portfolio_service

logger = get_logger(__name__)

def portfolio_snapshot_node(state: TradingDecisionState) -> TradingDecisionState:
    symbol = state["symbol"]
    logger.info(f"START fetching portfolio snapshot and daily candles for {symbol}...")

    service = create_binance_portfolio_service()
    portfolio = service.get_agent_portfolio_state()

    market_data = create_binance_market_data_service()
    daily_candles = market_data.get_klines(symbol=symbol, interval="1d", limit=250)

    asset_count = len(portfolio.get("balances", []))
    logger.info(f"RESULT assets={asset_count} daily_candles={len(daily_candles)}")

    return {"portfolio": portfolio, "daily_candles": daily_candles}
