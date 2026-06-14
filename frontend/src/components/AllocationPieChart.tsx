import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts"

export interface AllocationSlice {
  name: string
  value: number
}

interface AllocationPieChartProps {
  data: AllocationSlice[]
}

const COLORS = ['#60a5fa', '#4ade80', '#f87171', '#fbbf24', '#a78bfa', '#34d399', '#f472b6', '#38bdf8']

function AllocationPieChart({ data }: AllocationPieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #1f2937' }}
          formatter={(value: number) => `$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

export default AllocationPieChart
