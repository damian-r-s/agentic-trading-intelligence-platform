import { useQuery } from "@tanstack/react-query"

export interface Stats24h {
  symbol: string
  price_change: string
  price_change_pct: string
  last_price: string
  high: string
  low: string
  volume: string
  quote_volume: string
  open_price: string
  trade_count: number
  weighted_avg_price: string
}

export interface IndicatorLatest {
  close: number
  sma_20: number | null
  sma_50: number | null
  ema_9: number | null
  ema_21: number | null
  rsi_14: number | null
  macd: number | null
  macd_signal: number | null
  macd_histogram: number | null
  bb_upper: number | null
  bb_middle: number | null
  bb_lower: number | null
  atr_14: number | null
  obv: number | null
}

export interface IndicatorSignals {
  rsi_zone?: string
  macd_cross?: string
  bb_position?: string
  trend?: string
}

export interface Indicators {
  symbol: string
  interval: string
  candle_count: number
  latest: IndicatorLatest
  signals: IndicatorSignals
}

async function fetchStats(symbol: string): Promise<Stats24h> {
  const res = await fetch(`/api/market-data/${symbol}/stats`)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}

async function fetchIndicators(symbol: string): Promise<Indicators> {
  const res = await fetch(`/api/market-data/${symbol}/indicators`)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}

export function useStats(symbol: string) {
  return useQuery({
    queryKey: ['market-stats', symbol],
    queryFn: () => fetchStats(symbol),
  })
}

export function useIndicators(symbol: string) {
  return useQuery({
    queryKey: ['market-indicators', symbol],
    queryFn: () => fetchIndicators(symbol),
  })
}
