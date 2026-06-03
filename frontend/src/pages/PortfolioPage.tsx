import { usePortfolio } from "../api/portfolio"

function PortfolioPage() {
  const { data, isLoading, error } = usePortfolio()

  // compute USD value per asset
  const assetRows = data?.assets.map(asset => {
    const price = parseFloat(data.current_prices[asset.asset] ?? '0')
    const total = parseFloat(asset.total)
    const value = price * total
    return { ...asset, price, value }
  }) ?? []

  // total portfolio value
  const totalValue = assetRows.reduce((sum, a) => sum + a.value, 0)

  if (isLoading) 
    return <div className="p-8">Loading...</div>
  
  if (error) 
    return <div className="p-8 text-red-400">Error: {error.message}</div>

  return <div className="p-8">
    <h2 className="text-2xl">Portfolio</h2>  
    <div>Total Value: ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>

    <table className="mt-6 w-full text-sm">
      <thead>
        <tr className="text-left text-gray-400 border-b border-gray-700">
          <th className="pb-2">Asset</th>
          <th className="pb-2">Total</th>
          <th className="pb-2">Price (USDT)</th>
          <th className="pb-2">Value (USDT)</th>
          <th className="pb-2">Allocation</th>
        </tr>
      </thead>
      <tbody>
        {assetRows.map(a => (
          <tr key={a.asset} className="border-b border-gray-800">
            <td className="py-3 font-bold">{a.asset}</td>
            <td className="py-3">{a.total}</td>
            <td className="py-3">${a.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td className="py-3">${a.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
            <td className="py-3">{totalValue > 0 ? ((a.value / totalValue) * 100).toFixed(1) : '0'}%</td>
          </tr>
        ))}
      </tbody>
    </table>

    {data?.open_orders.length ? (
      <div className="mt-10">
        <h3 className="text-lg font-semibold mb-3">Open Orders</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-gray-700">
              <th className="pb-2">Symbol</th>
              <th className="pb-2">Side</th>
              <th className="pb-2">Type</th>
              <th className="pb-2">Price</th>
              <th className="pb-2">Qty</th>
              <th className="pb-2">Filled</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.open_orders.map(o => (
              <tr key={o.order_id} className="border-b border-gray-800">
                <td className="py-3">{o.symbol}</td>
                <td className={`py-3 font-semibold ${o.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                  {o.side}
                </td>
                <td className="py-3">{o.type}</td>
                <td className="py-3">${o.price}</td>
                <td className="py-3">{o.original_quantity}</td>
                <td className="py-3">{o.executed_quantity}</td>
                <td className="py-3 text-gray-400">{o.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : null}
  </div>
}

export default PortfolioPage