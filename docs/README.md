# Documentation

Architecture decisions, data flows, and design notes for the Agentic Trading Intelligence Platform.

## Data Flow

```
Binance REST API (read-only)
  │
  ├── BinanceClient              Raw HTTP, signed + public endpoints
  │     ├── get_account_info()
  │     ├── get_my_trades(symbol)
  │     ├── get_open_orders()
  │     ├── get_klines(symbol, interval, limit)
  │     ├── get_order_book(symbol, limit)
  │     ├── get_24h_ticker(symbol)
  │     ├── get_ticker_prices(symbols)
  │     ├── get_trade_fee(symbol)
  │     └── get_exchange_info()
  │
  ├── BinancePortfolioService    Normalized portfolio state
  │     ├── get_portfolio_snapshot()
  │     └── get_agent_portfolio_state()
  │           └── includes current_prices (USDT conversion via ticker)
  │
  └── BinanceMarketDataService   Normalized market data
        ├── get_klines()          → list of OHLCV dicts
        ├── get_order_book()      → bids/asks + spread + depth
        └── get_24h_stats()       → price change, volume, high/low
```

## Provider Interfaces (src/market_data/providers.py)

Agents depend on Protocol interfaces, not concrete classes. This allows swapping data sources without touching agent code.

| Interface | Used By | Implementation |
|---|---|---|
| `CandleProvider` | TechnicalAnalysisAgent, MomentumAgent | `BinanceMarketDataService` |
| `OrderBookProvider` | LiquidityAgent | `BinanceMarketDataService` |
| `TickerProvider` | MomentumAgent, MarketRegimeAgent | `BinanceMarketDataService` |
| `MarketDataProvider` | MarketRegimeAgent, MarketSaturationAgent | planned: CoinGecko |
| `DerivativesProvider` | MarketSaturationAgent | planned: Binance Futures API |
| `NewsProvider` | NewsSentimentAgent | planned: CryptoPanic |

## Risk Metrics Design

Risk metrics are computed from portfolio state in `src/agents/tools/risk.py`.

**Position sizing** uses current prices fetched via `/api/v3/ticker/price` at portfolio snapshot time. All values are converted to USDT using a two-pass price resolution:
1. Stablecoins → price = 1
2. Assets with direct USDT pairs → price from ticker
3. Assets quoted in non-USDT (e.g. BTCETH) → price × quote_price_in_USDT

**P&L calculation** uses the weighted average cost basis (WAVG) method:
- Each BUY trade increases the cost basis pool.
- Each SELL trade computes realized P&L against the current average, then reduces the pool proportionally.
- Quote assets are converted to USDT using current prices (approximation — historical rates are not stored).

**HHI (Herfindahl-Hirschman Index)** measures portfolio concentration:
- `HHI = Σ (weight_i)²` where weight is each asset's share of total portfolio value
- Range: 0 (perfectly diversified) → 1 (single asset)
- HHI > 0.25 is generally considered high concentration

## LangGraph Agent State

```python
class TradingDecisionState(TypedDict, total=False):
    symbol: str                      # Target symbol being evaluated

    portfolio_state: dict            # Output of PortfolioAgent
    market_regime: dict              # Output of MarketRegimeAgent
    market_saturation: dict          # Output of MarketSaturationAgent
    technical_analysis: dict         # Output of TechnicalAnalysisAgent
    momentum_analysis: dict          # Output of MomentumAgent
    liquidity_analysis: dict         # Output of LiquidityAgent
    fundamental_analysis: dict       # Output of FundamentalAgent
    sentiment_analysis: dict         # Output of NewsSentimentAgent
    correlation_analysis: dict       # Output of CorrelationAgent

    risk_analysis: dict              # Output of RiskAgent
    strategy_proposal: dict          # Output of StrategyAgent
    critic_review: dict              # Output of CriticAgent
    final_report: dict               # Output of DecisionReportAgent

    human_decision: str              # "APPROVE" | "REJECT" | "MODIFY"
```

## Graph Execution Order

```
START
  └── LoadPortfolioNode
        └── [parallel]
              ├── MarketRegimeAgent
              ├── MarketSaturationAgent
              ├── TechnicalAnalysisAgent
              ├── MomentumAgent
              ├── LiquidityAgent
              ├── FundamentalAgent
              ├── NewsSentimentAgent
              └── CorrelationAgent
                    └── RiskAgent
                          └── StrategyAgent
                                └── CriticAgent
                                      └── DecisionReportAgent
                                            └── HumanApprovalNode
                                                  └── END
```

Parallel nodes all read from the same state and write to separate fields.
LangGraph merges their outputs before passing state to the next sequential node.

## Binance API Notes

- All portfolio endpoints use **signed requests** (HMAC-SHA256).
- Market data endpoints (klines, order book, ticker) are **public** — no signature required.
- `recv_window` defaults to 5000ms; increase if you see timestamp errors.
- Rate limits: 1200 request weight per minute. `get_exchange_info()` costs 20 weight; most others cost 1-5.
