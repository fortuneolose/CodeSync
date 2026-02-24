import { create } from "zustand";
import type { User } from "../types";
import { authApi } from "../services/authApi";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,

  login: async (usernameOrEmail, password) => {
    const { data } = await authApi.login(usernameOrEmail, password);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    set({ user: data.user });
  },

  register: async (username, email, password) => {
    const { data } = await authApi.register(username, email, password);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    set({ user: data.user });
  },

  logout: async () => {
    const rt = localStorage.getItem("refresh_token");
    if (rt) await authApi.logout(rt).catch(() => {});
    localStorage.clear();
    set({ user: null });
  },

  hydrate: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) { set({ loading: false }); return; }
    try {
      const { data } = await authApi.me();
      set({ user: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
