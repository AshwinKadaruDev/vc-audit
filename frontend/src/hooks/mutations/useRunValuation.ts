import { useMutation } from '@tanstack/react-query';
import { ValuationsAPI } from '../../api';
import type { CompanyData } from '../../types';

/**
 * Hook to run a valuation on custom company data (without saving)
 */
export function useRunValuation() {
  return useMutation({
    mutationFn: (companyData: CompanyData) => ValuationsAPI.runCustom(companyData),
  });
}
