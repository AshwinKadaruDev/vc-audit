/**
 * Portfolio Companies API Client
 */

import type { PortfolioCompany } from '../types';
import { API_ENDPOINTS } from '../constants';
import { API_BASE_URL, handleResponse } from './config';

export class PortfolioCompaniesAPI {
  static async list(): Promise<PortfolioCompany[]> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PORTFOLIO_COMPANIES}`);
    return handleResponse<PortfolioCompany[]>(response);
  }

  static async getRandom(): Promise<PortfolioCompany> {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.PORTFOLIO_COMPANIES_RANDOM}`);
    return handleResponse<PortfolioCompany>(response);
  }
}
