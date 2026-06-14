import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import type { OrderBookLevel } from "../api/marketData"

interface OrderBookDepthProps {
  bids: OrderBookLevel[]
  asks: OrderBookLevel[]
}

function OrderBookDepth({bids, asks}: OrderBookDepthProps) {
    const data = Array.from({ length: Math.max(bids.length, asks.length) }, 
        (_, i) => ({
            level: i + 1,
            bidQty: bids[i] ? parseFloat(bids[i].quantity) : 0,
            askQty: asks[i] ? parseFloat(asks[i].quantity) : 0,
        })
    )

    return(
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="level" stroke="#9ca3af" tick={{ fontSize: 11 }} label={{ value: 'Level', position: 'insideBottom', offset: -5, fill: '#9ca3af' }} />
                <YAxis stroke="#9ca3af" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1f2937' }} />
                <Legend />
                <Bar dataKey="bidQty" name="Bid qty" fill="#4ade80" />
                <Bar dataKey="askQty" name="Ask qty" fill="#f87171" />
            </BarChart>
        </ResponsiveContainer>
    )
}

export default OrderBookDepth