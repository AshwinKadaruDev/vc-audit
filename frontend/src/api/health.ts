/**
 * Health API Client
 */

import { API_ENDPOINTS } from '../constants';
import { API_BASE_URL, handleResponse } from './config';

export interface HealthResponse {
  status: string;
  version: string;
}

export class HealthAPI {
  static async check(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.HEALTH}`);
    return handleResponse<HealthResponse>(response);
  }
}
