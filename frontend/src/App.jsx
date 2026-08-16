import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import AppShell from './components/shell/AppShell'
import EnergyDashboardPage from './pages/energy/EnergyDashboardPage'
import MaintenanceDashboardPage from './pages/maintenance/MaintenanceDashboardPage'
import OccupancyDashboardPage from './pages/occupancy/OccupancyDashboardPage'
import SecurityDashboardPage from './pages/security/SecurityDashboardPage'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<Navigate to="/energy" replace />} />
            <Route path="/energy" element={<EnergyDashboardPage />} />
            <Route path="/maintenance" element={<MaintenanceDashboardPage />} />
            <Route path="/occupancy" element={<OccupancyDashboardPage />} />
            <Route path="/security" element={<SecurityDashboardPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </ThemeProvider>
  )
}
