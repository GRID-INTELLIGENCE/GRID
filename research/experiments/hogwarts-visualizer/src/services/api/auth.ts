import apiClient from './client';
import { ApiResponse } from '../../types/api';

export interface LoginRequest {
  username: string;
  password: string;
  scopes?: string[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  scopes: string[];
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ValidateResponse {
  valid: boolean;
  user_id: string | null;
  email: string | null;
  scopes: string[];
  expires_at: number | null;
}

/**
 * Authentication service.
 */
export const authService = {
  /**
   * Login and get tokens.
   */
  login: async (request: LoginRequest): Promise<ApiResponse<TokenResponse>> => {
    const response = await apiClient.post<ApiResponse<TokenResponse>>('/auth/login', request);
    return response.data;
  },

  /**
   * Refresh access token.
   */
  refresh: async (request: RefreshRequest): Promise<ApiResponse<RefreshResponse>> => {
    const response = await apiClient.post<ApiResponse<RefreshResponse>>('/auth/refresh', request);
    return response.data;
  },

  /**
   * Validate current token.
   */
  validate: async (): Promise<ApiResponse<ValidateResponse>> => {
    const response = await apiClient.get<ApiResponse<ValidateResponse>>('/auth/validate');
    return response.data;
  },

  /**
   * Logout and invalidate session.
   */
  logout: async (): Promise<ApiResponse<any>> => {
    const response = await apiClient.post<ApiResponse<any>>('/auth/logout');
    return response.data;
  },
};

export default authService;
