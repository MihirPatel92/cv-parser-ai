import { apiClient } from './client';
import { CVTemplate } from './types';

export const getTemplates = async (): Promise<CVTemplate[]> => {
  const response = await apiClient.get('/templates');
  return response.data;
};

export const uploadTemplate = async (formData: FormData): Promise<CVTemplate> => {
  const response = await apiClient.post('/templates', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getTemplate = async (id: string): Promise<CVTemplate> => {
  const response = await apiClient.get(`/templates/${id}`);
  return response.data;
};

export const deleteTemplate = async (id: string): Promise<void> => {
  await apiClient.delete(`/templates/${id}`);
};

export const getTemplatePlaceholders = async (id: string): Promise<string[]> => {
  const response = await apiClient.get(`/templates/${id}/placeholders`);
  return response.data;
};
