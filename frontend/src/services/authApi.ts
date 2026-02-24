import api from "./api";
import type { User } from "../types";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export const authApi = {
  register: (username: string, email: string, password: string) =>
    api.post<TokenResponse>("/auth/register", { username, email, password }),

  login: (username_or_email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { username_or_email, password }),

  refresh: (refresh_token: string) =>
    api.post<{ access_token: string; refresh_token: string }>("/auth/refresh", { refresh_token }),

  logout: (refresh_token: string) =>
    api.post("/auth/logout", { refresh_token }),

  me: () => api.get<User>("/auth/me"),
};
