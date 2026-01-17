/**
 * Valuations API Client
 */

import type {
  CompanyData,
  ValuationResult,
  ValuationListItem,
  SavedValuation,
  SavedValuationResponse,
} from '../types';
import { API_ENDPOINTS } from '../constants';
import { API_BASE_URL, handleResponse } from './config';

export class ValuationsAPI {
  static async run(companyId: string): Promise<ValuationResult> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.VALUATIONS}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ company_id: companyId }),
    });
    return handleResponse<ValuationResult>(response);
  }

  static async runCustom(companyData: CompanyData): Promise<ValuationResult> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.VALUATIONS_CUSTOM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(companyData),
    });
    return handleResponse<ValuationResult>(response);
  }

  static async runAndSave(companyData: CompanyData): Promise<SavedValuationResponse> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.VALUATIONS_RUN_AND_SAVE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(companyData),
    });
    return handleResponse<SavedValuationResponse>(response);
  }

  static async list(): Promise<ValuationListItem[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.VALUATIONS_SAVED}`);
    return handleResponse<ValuationListItem[]>(response);
  }

  static async get(id: string): Promise<SavedValuation> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.VALUATION_DETAIL(id)}`);
    return handleResponse<SavedValuation>(response);
  }

  static async delete(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.VALUATION_DELETE(id)}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete valuation');
    }
  }
}
