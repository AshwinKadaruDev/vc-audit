/**
 * API Endpoint Constants
 *
 * Centralized API path definitions for maintainability.
 */

export const API_ENDPOINTS = {
  // Health
  HEALTH: '/api/health',

  // Companies
  COMPANIES: '/api/companies',
  COMPANY: (id: string) => `/api/companies/${id}`,

  // Sectors
  SECTORS: '/api/sectors',

  // Indices
  INDICES: '/api/indices',

  // Valuations
  VALUATIONS: '/api/valuations',
  VALUATIONS_CUSTOM: '/api/valuations/custom',
  VALUATIONS_SAVED: '/api/valuations/saved',
  VALUATION_DETAIL: (id: string) => `/api/valuations/saved/${id}`,
  VALUATION_DELETE: (id: string) => `/api/valuations/saved/${id}`,
  VALUATIONS_RUN_AND_SAVE: '/api/valuations/run-and-save',

  // Portfolio Companies
  PORTFOLIO_COMPANIES: '/api/portfolio-companies',
  PORTFOLIO_COMPANIES_RANDOM: '/api/portfolio-companies/random',
} as const;
