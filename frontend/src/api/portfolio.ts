import { useQuery } from "@tanstack/react-query"

export interface OpenOrder {
  symbol: string
  order_id: number
  side: string
  type: string
  price: string
  original_quantity: string
  executed_quantity: string
  status: string
  time: number
}

export interface PortfolioAsset {
  asset: string
  free: string
  locked: string
  total: string
  open_orders: OpenOrder[]
}

export interface PortfolioState {
  exchange: string
  account_type: string
  assets: PortfolioAsset[]
  current_prices: Record<string, string>
  open_orders: OpenOrder[]
}

async function fetchPortfolioState(): Promise<PortfolioState>{
    const res = await fetch('/api/portfolio/state')
    
    if (!res.ok)
        throw new Error(`${res.status}`)
    
    return res.json()
}

export function usePortfolio(){
    return useQuery({queryKey: ['portfolio'], queryFn: fetchPortfolioState})
}