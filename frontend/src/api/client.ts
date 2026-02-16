import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { jwtDecode } from 'jwt-decode';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

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

interface ResonanceResponse {
  activity_id: string;
  state: string;
  urgency: number;
  message: string;
  context: Record<string, any> | null;
  paths: Record<string, any> | null;
  envelope: Record<string, any> | null;
  timestamp: string;
}

interface DefinitiveResponse {
  activity_id: string;
  progress: number;
  canvas_before: string;
  canvas_after: string;
  summary: string;
  faq: Array<{ question: string; answer: string }>;
  use_cases: Array<{ audience: string; scenario: string; entrypoint: string; output: string }>;
  api_mechanics: string[];
  structured: Record<string, any>;
  context: Record<string, any> | null;
  paths: Record<string, any> | null;
  choices: Array<{ direction: string; option: Record<string, any>; why: string }>;
  skills: Record<string, any>;
  rag: Record<string, any> | null;
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
    const response = await this.client.post<AuthTokens>('/api/v1/auth/login', credentials);
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
    const response = await this.client.get<User>('/api/v1/auth/me');
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

  // Resonance methods (trust layer)
  async processResonance(request: {
    query: string;
    activity_type?: string;
    context?: Record<string, any>;
  }): Promise<ResonanceResponse> {
    const response = await this.client.post<ResonanceResponse>('/api/v1/resonance/process', {
      query: request.query,
      activity_type: request.activity_type || 'general',
      context: request.context || {},
    });
    return response.data;
  }

  async definitiveStep(request: {
    query: string;
    progress?: number;
    target_schema?: string;
    use_rag?: boolean;
    use_llm?: boolean;
    max_chars?: number;
  }): Promise<DefinitiveResponse> {
    const response = await this.client.post<DefinitiveResponse>('/api/v1/resonance/definitive', {
      query: request.query,
      activity_type: 'general',
      context: {},
      progress: request.progress ?? 0.65,
      target_schema: request.target_schema ?? 'context_engineering',
      use_rag: request.use_rag ?? false,
      use_llm: request.use_llm ?? false,
      max_chars: request.max_chars ?? 280,
    });
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
