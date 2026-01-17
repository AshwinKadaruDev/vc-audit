import { useState, useCallback } from 'react';
import { CompaniesAPI, ValuationsAPI } from '../api';
import type { CompanyListItem, ValuationResult } from '../types';

interface UseValuationState {
  companies: CompanyListItem[];
  selectedCompany: string | null;
  result: ValuationResult | null;
  loading: boolean;
  error: string | null;
}

interface UseValuationReturn extends UseValuationState {
  loadCompanies: () => Promise<void>;
  selectCompany: (companyId: string) => void;
  runValuation: () => Promise<void>;
  clearResult: () => void;
}

export function useValuation(): UseValuationReturn {
  const [state, setState] = useState<UseValuationState>({
    companies: [],
    selectedCompany: null,
    result: null,
    loading: false,
    error: null,
  });

  const loadCompanies = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const companies = await CompaniesAPI.list();
      setState(prev => ({ ...prev, companies, loading: false }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to load companies',
      }));
    }
  }, []);

  const selectCompany = useCallback((companyId: string) => {
    setState(prev => ({
      ...prev,
      selectedCompany: companyId,
      result: null,
      error: null,
    }));
  }, []);

  const runValuation = useCallback(async () => {
    if (!state.selectedCompany) return;

    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const result = await ValuationsAPI.run(state.selectedCompany);
      setState(prev => ({ ...prev, result, loading: false }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Valuation failed',
      }));
    }
  }, [state.selectedCompany]);

  const clearResult = useCallback(() => {
    setState(prev => ({ ...prev, result: null, error: null }));
  }, []);

  return {
    ...state,
    loadCompanies,
    selectCompany,
    runValuation,
    clearResult,
  };
}
