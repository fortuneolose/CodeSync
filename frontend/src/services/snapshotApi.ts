import api from "./api";

export interface Snapshot {
  id: string;
  session_id: string;
  title: string;
  content: string;
  language: string;
  created_by: string | null;
  created_at: string;
  author_username: string | null;
}

export interface RestoreResponse {
  content: string;
  language: string;
  snapshot_id: string;
}

export const snapshotApi = {
  create: (slug: string, title: string, content: string, language: string) =>
    api.post<Snapshot>(`/sessions/${slug}/snapshots`, { title, content, language }),

  list: (slug: string) =>
    api.get<Snapshot[]>(`/sessions/${slug}/snapshots`),

  restore: (slug: string, snapshotId: string) =>
    api.post<RestoreResponse>(`/sessions/${slug}/snapshots/${snapshotId}/restore`),

  delete: (slug: string, snapshotId: string) =>
    api.delete(`/sessions/${slug}/snapshots/${snapshotId}`),
};
