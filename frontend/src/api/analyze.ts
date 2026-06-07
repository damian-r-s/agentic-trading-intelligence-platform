import { useQuery } from "@tanstack/react-query"

export interface Strategy {
  action: string
  confidence: number
  entry_zone: string
  thesis: string
  risks: string
}

export interface Critic {
  challenges: string[]
  risk_flags: string[]
  contradictions: string[]
  severity: string
  verdict: string
}

export interface BinanceOrderStep {
  order_type: string
  side: string
  price?: number
  amount_usdt?: number
  take_profit_price?: number
  stop_price?: number
  stop_limit_price?: number
  fee_usdt: number
  time_in_force?: string
  instruction: string
}

export interface BinanceOrders {
  step_1_entry: BinanceOrderStep
  step_2_oco_after_fill: BinanceOrderStep
}

export interface DecisionReport {
  final_action: string
  confidence: number
  entry_price: number | null
  stop_loss: number | null
  take_profit: number | null
  breakeven_price: number | null
  risk_reward_ratio: number | null
  fee_rate_pct: number | null
  total_fees_usdt: number | null
  position_size_pct: number | null
  position_size_usdt: number | null
  binance_orders: BinanceOrders | null
  invalidation: string
  bull_case: string
  bear_case: string
  final_thesis: string
  key_risks: string
}

export interface State {
  symbol: string
  strategy: Strategy
  critic: Critic
  decision_report: DecisionReport
}

async function fetchAnalyze(symbol: string): Promise<State> {
    const res = await fetch(`/api/agent/analyze?symbol=${symbol}`)

    if (!res.ok)
        throw new Error(`${res.status}`)

    return res.json()
}

export function useAnalyze(symbol: string) {
    return useQuery({
        queryKey: ['analyze', symbol],
        queryFn: () => fetchAnalyze(symbol),
        enabled: false,
    })
}
