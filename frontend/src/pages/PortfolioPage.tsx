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
  </div>
}

export default PortfolioPage