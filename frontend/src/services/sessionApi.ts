import api from "./api";
import type { Session } from "../types";

export interface SessionMember {
  user_id: string;
  username: string;
  role: string;
  joined_at: string;
}

export interface SessionWithMembers extends Session {
  members: SessionMember[];
}

export interface SessionUpdatePayload {
  title?: string;
  language?: string;
  content?: string;
  is_public?: boolean;
}

export const sessionApi = {
  create: (title: string, language: string, is_public = false) =>
    api.post<Session>("/sessions", { title, language, is_public }),

  list: () => api.get<Session[]>("/sessions"),

  get: (slug: string) => api.get<SessionWithMembers>(`/sessions/${slug}`),

  update: (slug: string, data: SessionUpdatePayload) =>
    api.patch<Session>(`/sessions/${slug}`, data),

  delete: (slug: string) => api.delete(`/sessions/${slug}`),

  join: (slug: string) => api.post(`/sessions/${slug}/join`),
};
