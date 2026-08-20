export type Role = 'super_admin' | 'admin' | 'recruiter';
export type ConversionStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type AIProvider = 'gemini' | 'openai' | 'ollama';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface CVTemplate {
  id: string;
  name: string;
  description: string;
  company_name: string;
  file_type: string;
  placeholder_type: string;
  detected_placeholders: string[];
  created_at: string;
  uploaded_by_name: string;
}

export interface Conversion {
  id: string;
  recruiter_name: string;
  template_name: string;
  source_cv_filename: string;
  status: ConversionStatus;
  ai_provider: AIProvider;
  output_format: string;
  created_at: string;
  completed_at?: string;
}

export interface AIConfig {
  id: string;
  provider: AIProvider;
  model_name: string;
  ollama_base_url?: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
}

export interface DashboardStats {
  total_users: number;
  total_templates: number;
  total_conversions: number;
  completed_conversions: number;
  failed_conversions: number;
  recent_conversions: Conversion[];
}
