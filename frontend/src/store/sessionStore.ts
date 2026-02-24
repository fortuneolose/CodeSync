import { create } from "zustand";
import type { Session } from "../types";
import { sessionApi } from "../services/sessionApi";

interface SessionState {
  sessions: Session[];
  loading: boolean;
  fetch: () => Promise<void>;
  create: (title: string, language: string, isPublic?: boolean) => Promise<Session>;
  remove: (slug: string) => Promise<void>;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  loading: false,

  fetch: async () => {
    set({ loading: true });
    const { data } = await sessionApi.list();
    set({ sessions: data, loading: false });
  },

  create: async (title, language, isPublic = false) => {
    const { data } = await sessionApi.create(title, language, isPublic);
    set({ sessions: [data, ...get().sessions] });
    return data;
  },

  remove: async (slug) => {
    await sessionApi.delete(slug);
    set({ sessions: get().sessions.filter((s) => s.slug !== slug) });
  },
}));
