export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface Session {
  id: string;
  slug: string;
  title: string;
  language: string;
  content: string;
  is_public: boolean;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Presence {
  user_id: string;
  username: string;
  color: string;
  cursor?: { line: number; col: number };
}
