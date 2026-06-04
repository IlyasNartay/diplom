/**
 * src/App.jsx — Корневой компонент с маршрутизацией
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import EventsPage from './pages/EventsPage'
import SeatsPage from './pages/SeatsPage'
import PaymentPage from './pages/PaymentPage'
import TicketPage from './pages/TicketPage'
import LoginPage from './pages/LoginPage'
import useStore from './store/useStore'

function PrivateRoute({ children }) {
  const token = useStore((s) => s.token)
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <div style={{ minHeight: '100vh' }}>
      <Navbar />
      <Routes>
        <Route path="/"            element={<EventsPage />} />
        <Route path="/login"       element={<LoginPage />} />
        <Route path="/events/:id/seats" element={
          <PrivateRoute><SeatsPage /></PrivateRoute>
        } />
        <Route path="/payment"     element={
          <PrivateRoute><PaymentPage /></PrivateRoute>
        } />
        <Route path="/ticket"      element={
          <PrivateRoute><TicketPage /></PrivateRoute>
        } />
      </Routes>
    </div>
  )
}
