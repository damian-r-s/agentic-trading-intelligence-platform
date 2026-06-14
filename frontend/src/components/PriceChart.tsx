import { ComposedChart, Area, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import type { Candle } from "../api/marketData"

interface PriceChartProps {
  candles: Candle[]
}

function PriceChart({ candles }: PriceChartProps) {
  const data = candles.map(c => ({
    time: new Date(c.open_time).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' }),
    close: parseFloat(c.close),
    volume: parseFloat(c.volume),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis dataKey="time" stroke="#9ca3af" tick={{ fontSize: 11 }} minTickGap={40} />
        <YAxis yAxisId="price" stroke="#9ca3af" domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
        <YAxis yAxisId="volume" orientation="right" stroke="#9ca3af" tick={{ fontSize: 11 }} />
        <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937' }} />
        <Bar yAxisId="volume" dataKey="volume" fill="#37415180" />
        <Area yAxisId="price" type="monotone" dataKey="close" stroke="#60a5fa" fill="#60a5fa33" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export default PriceChart