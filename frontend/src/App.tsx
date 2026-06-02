import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import PortfolioPage from './pages/PortfolioPage'
import AnalyzePage from './pages/AnalyzePage'
import MarketDataPage from './pages/MarketDataPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">

        <nav className="bg-gray-900 border-b border-gray-800 px-8 py-4 flex gap-6">
          <span className="text-blue-400 font-bold mr-8">Trading Intelligence</span>
          <NavLink to="/" className="hover:text-blue-400">Portfolio</NavLink>
          <NavLink to="/analyze" className="hover:text-blue-400">Analyze</NavLink>
          <NavLink to="/market" className="hover:text-blue-400">Market Data</NavLink>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<PortfolioPage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/market" element={<MarketDataPage />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  )
}

export default App
