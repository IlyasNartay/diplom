/**
 * src/store/useStore.js
 * Глобальное состояние приложения через Zustand.
 * Хранит: авторизацию, выбранное событие, выбранное место, заказ.
 */
import { create } from 'zustand'

const useStore = create((set) => ({
  // ── Auth ───────────────────────────────────────────────────
  token:    localStorage.getItem('token') || null,
  username: localStorage.getItem('username') || null,

  setAuth: (token, username) => {
    localStorage.setItem('token', token)
    localStorage.setItem('username', username)
    set({ token, username })
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    set({ token: null, username: null })
  },

  // ── Booking flow ───────────────────────────────────────────
  selectedEvent: null,
  selectedSeat:  null,
  currentOrder:  null,
  paymentResult: null,

  setSelectedEvent: (event) => set({ selectedEvent: event, selectedSeat: null, currentOrder: null }),
  setSelectedSeat:  (seat)  => set({ selectedSeat: seat }),
  setCurrentOrder:  (order) => set({ currentOrder: order }),
  setPaymentResult: (result) => set({ paymentResult: result }),

  resetBooking: () => set({
    selectedEvent: null,
    selectedSeat:  null,
    currentOrder:  null,
    paymentResult: null,
  }),
}))

export default useStore
