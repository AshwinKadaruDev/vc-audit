/**
 * Companies API Client
 */

import type { CompanyListItem, CompanyData } from '../types';
import { API_ENDPOINTS } from '../constants';
import { API_BASE_URL, handleResponse } from './config';

export class CompaniesAPI {
  static async list(): Promise<CompanyListItem[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.COMPANIES}`);
    return handleResponse<CompanyListItem[]>(response);
  }

  static async get(companyId: string): Promise<CompanyData> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.COMPANY(companyId)}`);
    return handleResponse<CompanyData>(response);
  }

  static async listSectors(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.SECTORS}`);
    return handleResponse<string[]>(response);
  }

  static async listIndices(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.INDICES}`);
    return handleResponse<string[]>(response);
  }
}
