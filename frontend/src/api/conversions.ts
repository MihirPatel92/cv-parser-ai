import { apiClient } from './client';
import { Conversion } from './types';

export const getConversions = async (): Promise<Conversion[]> => {
  const response = await apiClient.get('/conversions');
  return response.data;
};

export const createConversion = async (formData: FormData): Promise<Conversion> => {
  const response = await apiClient.post('/conversions', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getConversion = async (id: string): Promise<Conversion> => {
  const response = await apiClient.get(`/conversions/${id}`);
  return response.data;
};

export const downloadConversion = async (id: string, format: string): Promise<Blob> => {
  const response = await apiClient.get(`/conversions/${id}/download?format=${format}`, {
    responseType: 'blob'
  });
  return response.data;
};

export const deleteConversion = async (id: string): Promise<void> => {
  await apiClient.delete(`/conversions/${id}`);
};
