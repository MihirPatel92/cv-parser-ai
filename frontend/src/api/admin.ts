import { apiClient } from './client';
import { AIConfig, DashboardStats } from './types';

export const getStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get('/admin/stats');
  return response.data;
};

export const getAIConfig = async (): Promise<AIConfig> => {
  const response = await apiClient.get('/admin/ai-config');
  return response.data;
};

export const updateAIConfig = async (data: Partial<AIConfig>): Promise<AIConfig> => {
  const response = await apiClient.put('/admin/ai-config', data);
  return response.data;
};
