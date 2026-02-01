/**
 * Common API response structure.
 */
export interface ResponseMeta {
  request_id: string;
  timestamp?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  meta?: ResponseMeta;
}
