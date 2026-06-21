import { create } from 'zustand'

interface AuthState {
  username: string | null
  setUser: (username: string | null) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  username: null,
  setUser: (username) => set({ username }),
}))