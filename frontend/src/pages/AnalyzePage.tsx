import { useState } from "react"
import { useAnalyze } from "../api/analyze"

const ACTION_STYLES: Record<string, string> = {
  BUY:   'bg-green-500/20 text-green-400 border-green-500/40',
  WAIT:  'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  AVOID: 'bg-red-500/20 text-red-400 border-red-500/40',
}

function fmt(value: number | null | undefined, prefix = '$') {
  return value === null || value === undefined
    ? '—'
    : `${prefix}${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
}

function AnalyzePage() {
  const [symbol, setSymbol] = useState('BTCUSDT')
  const { data, isFetching, error, refetch } = useAnalyze(symbol)

  const report = data?.decision_report
  const critic = data?.critic

  return <div className="p-8">
    <h2 className="text-2xl mb-6">Analyze</h2>

    <div className="flex gap-3 items-center mb-8">
      <input
        value={symbol}
        onChange={e => setSymbol(e.target.value.toUpperCase())}
        className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm w-40"
        placeholder="BTCUSDT"
      />
      <button
        onClick={() => refetch()}
        disabled={isFetching}
        className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-400 rounded px-4 py-2 text-sm font-semibold"
      >
        {isFetching ? 'Analyzing...' : 'Analyze'}
      </button>
    </div>

    {isFetching && (
      <div className="text-gray-400 text-sm mb-6">
        Running the full 11-node pipeline + 3 LLM calls — this can take a few minutes.
      </div>
    )}

    {error && (
      <div className="text-red-400 mb-6">Error: {error.message}</div>
    )}

    {report && (
      <div className="space-y-8">
        <div className="border border-gray-800 rounded-lg p-6">
          <div className="flex items-center gap-4 mb-4">
            <span className={`px-3 py-1 rounded border text-sm font-bold ${ACTION_STYLES[report.final_action] ?? 'bg-gray-700 text-gray-300 border-gray-600'}`}>
              {report.final_action}
            </span>
            <span className="text-gray-400 text-sm">Confidence: {(report.confidence * 100).toFixed(0)}%</span>
          </div>

          <p className="text-gray-300 mb-6">{report.final_thesis}</p>

          <table className="w-full text-sm mb-6">
            <tbody>
              <tr className="border-b border-gray-800">
                <td className="py-2 text-gray-400">Entry price</td>
                <td className="py-2">{fmt(report.entry_price)}</td>
                <td className="py-2 text-gray-400">Stop loss</td>
                <td className="py-2">{fmt(report.stop_loss)}</td>
              </tr>
              <tr className="border-b border-gray-800">
                <td className="py-2 text-gray-400">Take profit</td>
                <td className="py-2">{fmt(report.take_profit)}</td>
                <td className="py-2 text-gray-400">Breakeven</td>
                <td className="py-2">{fmt(report.breakeven_price)}</td>
              </tr>
              <tr className="border-b border-gray-800">
                <td className="py-2 text-gray-400">Risk/reward</td>
                <td className="py-2">{report.risk_reward_ratio ?? '—'}</td>
                <td className="py-2 text-gray-400">Position size</td>
                <td className="py-2">{report.position_size_pct ?? '—'}% ({fmt(report.position_size_usdt)})</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-400">Total fees</td>
                <td className="py-2">{fmt(report.total_fees_usdt)}</td>
                <td className="py-2 text-gray-400">Invalidation</td>
                <td className="py-2">{report.invalidation || '—'}</td>
              </tr>
            </tbody>
          </table>

          {report.binance_orders && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-900 border border-gray-800 rounded p-4">
                <div className="text-xs text-gray-400 uppercase mb-2">Step 1 — Entry</div>
                <p className="text-sm text-gray-300">{report.binance_orders.step_1_entry.instruction}</p>
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded p-4">
                <div className="text-xs text-gray-400 uppercase mb-2">Step 2 — OCO Exit</div>
                <p className="text-sm text-gray-300">{report.binance_orders.step_2_oco_after_fill.instruction}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-green-400 uppercase mb-1">Bull case</div>
              <p className="text-sm text-gray-300">{report.bull_case}</p>
            </div>
            <div>
              <div className="text-xs text-red-400 uppercase mb-1">Bear case</div>
              <p className="text-sm text-gray-300">{report.bear_case}</p>
            </div>
          </div>

          {report.key_risks && (
            <div className="mt-6">
              <div className="text-xs text-gray-400 uppercase mb-1">Key risks</div>
              <p className="text-sm text-gray-300">{report.key_risks}</p>
            </div>
          )}
        </div>

        {critic && (
          <div className="border border-gray-800 rounded-lg p-6">
            <div className="flex items-center gap-4 mb-4">
              <h3 className="text-lg font-semibold">Critic Review</h3>
              <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-300 text-xs uppercase">{critic.verdict}</span>
              <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-300 text-xs uppercase">severity: {critic.severity}</span>
            </div>

            {critic.challenges.length > 0 && (
              <div className="mb-4">
                <div className="text-xs text-gray-400 uppercase mb-1">Challenges</div>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                  {critic.challenges.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}

            {critic.contradictions.length > 0 && (
              <div className="mb-4">
                <div className="text-xs text-gray-400 uppercase mb-1">Contradictions</div>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                  {critic.contradictions.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}

            {critic.risk_flags.length > 0 && (
              <div>
                <div className="text-xs text-gray-400 uppercase mb-1">Risk flags</div>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                  {critic.risk_flags.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    )}
  </div>
}

export default AnalyzePage
