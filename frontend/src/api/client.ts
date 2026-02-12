import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { jwtDecode } from 'jwt-decode';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface AuthTokens {
  access_token: string;
  token_type: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  trust_tier: string;
  is_active: boolean;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface InferenceRequest {
  prompt: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
  context?: Record<string, any>;
}

interface InferenceResponse {
  result: string;
  model: string;
  tokens_used: number;
  processing_time: number;
  metadata?: Record<string, any>;
}

interface PrivacyRequest {
  text: string;
  level?: string;
  context?: string;
}

interface PrivacyResponse {
  masked_text: string;
  detected_entities: Array<{
    type: string;
    value: string;
    start: number;
    end: number;
  }>;
  applied_rules: string[];
}

class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<AuthTokens> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for auth token
    this.client.interceptors.request.use((config) => {
      const token = this.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest?._retry) {
          originalRequest._retry = true;

          try {
            const newTokens = await this.refreshToken();
            this.setTokens(newTokens);
            originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  private setTokens(tokens: AuthTokens) {
    localStorage.setItem('access_token', tokens.access_token);
    // In a real implementation, you'd also store a refresh token
    localStorage.setItem('token_type', tokens.token_type);
  }

  private clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_type');
  }

  private async refreshToken(): Promise<AuthTokens> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: this.getRefreshToken(),
    }).then(response => response.data);

    try {
      const tokens = await this.refreshPromise;
      return tokens;
    } finally {
      this.refreshPromise = null;
    }
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.client.post<AuthTokens>('/auth/token', credentials);
    this.setTokens(response.data);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  // Inference methods
  async createInference(request: InferenceRequest): Promise<InferenceResponse> {
    const response = await this.client.post<InferenceResponse>('/api/v1/inference/', request);
    return response.data;
  }

  async createAsyncInference(request: InferenceRequest): Promise<{ task_id: string }> {
    const response = await this.client.post('/api/v1/inference/async', request);
    return response.data;
  }

  async getInferenceStatus(taskId: string): Promise<any> {
    const response = await this.client.get(`/api/v1/inference/status/${taskId}`);
    return response.data;
  }

  async getAvailableModels(): Promise<{ models: string[]; default: string }> {
    const response = await this.client.get('/api/v1/inference/models');
    return response.data;
  }

  // Privacy methods
  async detectPII(request: { text: string }): Promise<any> {
    const response = await this.client.post('/api/v1/privacy/detect', request);
    return response.data;
  }

  async maskPII(request: PrivacyRequest): Promise<PrivacyResponse> {
    const response = await this.client.post<PrivacyResponse>('/api/v1/privacy/mask', request);
    return response.data;
  }

  async batchPrivacyProcessing(request: { texts: string[]; level?: string }): Promise<any> {
    const response = await this.client.post('/api/v1/privacy/batch', request);
    return response.data;
  }

  async getPrivacyLevels(): Promise<any> {
    const response = await this.client.get('/api/v1/privacy/levels');
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Utility methods
  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    if (!token) return false;

    try {
      const decoded = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      return decoded.exp > currentTime;
    } catch {
      return false;
    }
  }

  getUserFromToken(): User | null {
    const token = this.getAccessToken();
    if (!token) return null;

    try {
      const decoded = jwtDecode(token) as any;
      return {
        id: decoded.user_id,
        username: decoded.sub,
        email: decoded.email,
        trust_tier: decoded.trust_tier,
        is_active: true,
      };
    } catch {
      return null;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
