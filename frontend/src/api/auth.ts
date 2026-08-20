import { apiClient } from './client';
import { User } from './types';

export const login = async (email: string, password: string) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);
  
  const response = await apiClient.post('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

export const changePassword = async (oldPassword: string, newPassword: string) => {
  const response = await apiClient.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword });
  return response.data;
};
