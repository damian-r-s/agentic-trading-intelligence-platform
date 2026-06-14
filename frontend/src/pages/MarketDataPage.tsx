import { useState } from "react"
import { useStats, useIndicators, useCandles, useOrderBook } from "../api/marketData"
import PriceChart from "../components/PriceChart"
import OrderBookDepth from "../components/OrderBookDepth"

const INTERVALS = ['1h', '4h', '8h', '1d'] as const
type Interval = typeof INTERVALS[number]

const SIGNAL_STYLES: Record<string, string> = {
  uptrend: 'text-green-400',
  downtrend: 'text-red-400',
  sideways: 'text-gray-400',
  bullish: 'text-green-400',
  bearish: 'text-red-400',
  bullish_continuation: 'text-green-400',
  bearish_continuation: 'text-red-400',
  overbought: 'text-red-400',
  oversold: 'text-green-400',
  neutral: 'text-gray-400',
  above_upper: 'text-red-400',
  below_lower: 'text-green-400',
  inside: 'text-gray-400',
}

function fmt(value: number | null | undefined, digits = 2) {
  return value === null || value === undefined
    ? '—'
    : value.toLocaleString('en-US', { maximumFractionDigits: digits })
}

function MarketDataPage() {
  const [interval, setIntervalValue] = useState<Interval>('4h')
  const [symbol, setSymbol] = useState('BTCUSDT')
  const { data: stats, isLoading: statsLoading, error: statsError } = useStats(symbol)
  const { data: indicators, isLoading: indicatorsLoading, error: indicatorsError } = useIndicators(symbol)
  const { data: candles, isLoading: candlesLoading, error: candlesError } = useCandles(symbol, interval)
  const { data: orderBook, isLoading: orderBookLoading, error: orderBookError } = useOrderBook(symbol)

  return <div className="p-8">
    <h2 className="text-2xl mb-6">Market Data</h2>

    <input
      value={symbol}
      onChange={e => setSymbol(e.target.value.toUpperCase())}
      className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm w-40 mb-8"
      placeholder="BTCUSDT"
    />

    <section className="mb-10">
      <h3 className="text-lg font-semibold mb-3">24h Stats</h3>
      {statsLoading && <div className="text-gray-400">Loading...</div>}
      {statsError && <div className="text-red-400">Error: {statsError.message}</div>}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">Last price</div>
            <div className="text-lg font-semibold">${stats.last_price}</div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">24h change</div>
            <div className={`text-lg font-semibold ${parseFloat(stats.price_change_pct) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {stats.price_change_pct}%
            </div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">24h high</div>
            <div className="text-lg font-semibold">${stats.high}</div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">24h low</div>
            <div className="text-lg font-semibold">${stats.low}</div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">Volume</div>
            <div className="text-lg font-semibold">{parseFloat(stats.volume).toLocaleString('en-US', { maximumFractionDigits: 2 })}</div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">Quote volume</div>
            <div className="text-lg font-semibold">${parseFloat(stats.quote_volume).toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">Trades</div>
            <div className="text-lg font-semibold">{stats.trade_count.toLocaleString('en-US')}</div>
          </div>
          <div className="border border-gray-800 rounded p-4">
            <div className="text-xs text-gray-400 uppercase mb-1">Weighted avg</div>
            <div className="text-lg font-semibold">${stats.weighted_avg_price}</div>
          </div>
        </div>
      )}
    </section>

    <section>
      <h3 className="text-lg font-semibold mb-3">Technical Indicators</h3>
      {indicatorsLoading && <div className="text-gray-400">Loading...</div>}
      {indicatorsError && <div className="text-red-400">Error: {indicatorsError.message}</div>}
      {indicators && (
        <>
          <div className="flex gap-3 mb-4">
            {Object.entries(indicators.signals).map(([key, value]) => (
              <span key={key} className={`px-2 py-1 rounded bg-gray-900 border border-gray-800 text-xs uppercase ${SIGNAL_STYLES[value as string] ?? 'text-gray-300'}`}>
                {key.replace(/_/g, ' ')}: {(value as string).replace(/_/g, ' ')}
              </span>
            ))}
          </div>

          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-gray-800">
                <td className="py-2 text-gray-400">Close</td>
                <td className="py-2">{fmt(indicators.latest.close)}</td>
                <td className="py-2 text-gray-400">RSI (14)</td>
                <td className="py-2">{fmt(indicators.latest.rsi_14)}</td>
              </tr>
              <tr className="border-b border-gray-800">
                <td className="py-2 text-gray-400">SMA 20 / 50</td>
                <td className="py-2">{fmt(indicators.latest.sma_20)} / {fmt(indicators.latest.sma_50)}</td>
                <td className="py-2 text-gray-400">EMA 9 / 21</td>
                <td className="py-2">{fmt(indicators.latest.ema_9)} / {fmt(indicators.latest.ema_21)}</td>
              </tr>
              <tr className="border-b border-gray-800">
                <td className="py-2 text-gray-400">MACD / Signal / Hist</td>
                <td className="py-2">{fmt(indicators.latest.macd, 4)} / {fmt(indicators.latest.macd_signal, 4)} / {fmt(indicators.latest.macd_histogram, 4)}</td>
                <td className="py-2 text-gray-400">ATR (14)</td>
                <td className="py-2">{fmt(indicators.latest.atr_14)}</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-400">Bollinger Upper / Mid / Lower</td>
                <td className="py-2">{fmt(indicators.latest.bb_upper)} / {fmt(indicators.latest.bb_middle)} / {fmt(indicators.latest.bb_lower)}</td>
                <td className="py-2 text-gray-400">OBV</td>
                <td className="py-2">{fmt(indicators.latest.obv, 0)}</td>
              </tr>
            </tbody>
          </table>
        </>
      )}
    </section>

    <section className="mb-10">      
      <h3 className="text-lg font-semibold mb-3">Price Chart</h3>
      <div className="flex gap-2 mb-3">
        {INTERVALS.map(iv => (
          <button
            key={iv}
            onClick={() => setIntervalValue(iv)}
            className={`px-3 py-1 rounded text-xs font-semibold border ${
              interval === iv
                ? 'bg-blue-600 border-blue-500 text-white'
                : 'bg-gray-900 border-gray-700 text-gray-400 hover:text-white'
            }`}
          >
            {iv}
          </button>
        ))}
      </div>

      {candlesLoading && <div className="text-gray-400">Loading...</div>}
      {candlesError && <div className="text-red-400">Error: {candlesError.message}</div>}
      {candles && <PriceChart candles={candles.candles}/>}
    </section>

    <section className="mb-10">
        <h3 className="text-lg font-semibold mb-3">Order Book</h3>
        {orderBookLoading && <div className="text-gray-400">Loading...</div>}
        {orderBookError && <div className="text-red-400">Error: {orderBookError.message}</div>}
        {orderBook && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="border border-gray-800 rounded p-4">
                <div className="text-xs text-gray-400 uppercase mb-1">Best bid</div>
                <div className="text-lg font-semibold text-green-400">${orderBook.best_bid}</div>
              </div>
              <div className="border border-gray-800 rounded p-4">
                <div className="text-xs text-gray-400 uppercase mb-1">Best ask</div>
                <div className="text-lg font-semibold text-red-400">${orderBook.best_ask}</div>
              </div>
              <div className="border border-gray-800 rounded p-4">
                <div className="text-xs text-gray-400 uppercase mb-1">Spread</div>
                <div className="text-lg font-semibold">{orderBook.spread} ({parseFloat(orderBook.spread_pct).toFixed(4)}%)</div>
              </div>
              <div className="border border-gray-800 rounded p-4">
                <div className="text-xs text-gray-400 uppercase mb-1">Mid price</div>
                <div className="text-lg font-semibold">${orderBook.mid_price}</div>
              </div>
            </div>
            <OrderBookDepth bids={orderBook.bids} asks={orderBook.asks} />
          </>
        )}
    </section>

  </div>
}

export default MarketDataPage