import { create } from "zustand";

import type { Token, UserResponse } from "@/types/api";

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  setSession: (tokens: Token, user: UserResponse) => void;
  setUser: (user: UserResponse | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: Boolean(localStorage.getItem("access_token")),

  setSession: (tokens, user) => {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    set({ user, isAuthenticated: true });
  },

  setUser: (user) => set({ user, isAuthenticated: user !== null }),

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },
}));
