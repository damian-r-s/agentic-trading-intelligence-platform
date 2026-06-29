import { BrowserRouter, Routes, Route, NavLink, Navigate, useLocation, useNavigate } from 'react-router-dom'
import PortfolioPage from './pages/PortfolioPage'
import AnalyzePage from './pages/AnalyzePage'
import MarketDataPage from './pages/MarketDataPage'
import Settings from './pages/Settings'
import Login from './pages/Login'
import { useEffect } from 'react'
import { useLogout, useMe } from './api/auth'
import { useAuthStore } from './store/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const username = useAuthStore(s => s.username)
  if (!username) return <Navigate to="/login" replace />
  return <>{children}</>
}

function Nav() {
  const location = useLocation()
  const navigate = useNavigate()
  const setUser = useAuthStore(s => s.setUser)
  const { mutate: logout } = useLogout()

  if (location.pathname === '/login') return null


  function handleLogout() {
    logout(undefined, {
      onSuccess: () => {
        setUser(null)
        navigate('/login')
      }
    })
  }
  
  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-8 py-4 flex gap-6">
      <span className="text-blue-400 font-bold mr-8">Trading Intelligence</span>
      <NavLink to="/" className="hover:text-blue-400">Portfolio</NavLink>
      <NavLink to="/analyze" className="hover:text-blue-400">Analyze</NavLink>
      <NavLink to="/market" className="hover:text-blue-400">Market Data</NavLink>
      <NavLink to="/settings" className="hover:text-blue-400">Settings</NavLink>
      <button onClick={handleLogout} className="ml-auto hover:text-red-400">Logout</button>
    </nav>
  )
}

function App() {
  const { data, isLoading } = useMe()
  const setUser = useAuthStore(s => s.setUser)

  useEffect(() => {
    if (data) setUser(data.username)
  }, [data, setUser])

  if (isLoading) return <div className="p-8 text-white">Loading...</div>
   
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">

        <Nav />

        <main>
          <Routes>
            <Route path="/" element={<ProtectedRoute><PortfolioPage /></ProtectedRoute>} />
            <Route path="/analyze" element={<ProtectedRoute><AnalyzePage /></ProtectedRoute>} />
            <Route path="/market" element={<ProtectedRoute><MarketDataPage /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="/login" element={<Login />} />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  )
}

export default App
