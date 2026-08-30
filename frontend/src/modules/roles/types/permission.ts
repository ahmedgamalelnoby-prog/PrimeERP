export interface Permission {
  id: number;
  name: string;
  resource: string;
  action: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}