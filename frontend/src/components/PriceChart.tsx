import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import type { Candle } from "../api/marketData"

interface PriceChartProps {
    candles: Candle[]
}

function PriceChart({candles}: PriceChartProps) {
    const data = candles.map(c => ({
        time: new Date(c.open_time).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' }),
        close: parseFloat(c.close)
    }))

    return (
        <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" stroke="#9ca3af" tick={{ fontSize: 11 }} minTickGap={40} />
                <YAxis stroke="#9ca3af" domain={['auto', 'auto']} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937' }} />
                <Area type="monotone" dataKey="close" stroke="#60a5fa" fill="#60a5fa33" />
            </AreaChart>
        </ResponsiveContainer>
    )
}

export default PriceChart