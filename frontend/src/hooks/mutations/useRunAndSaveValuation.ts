import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ValuationsAPI } from '../../api';
import type { CompanyData } from '../../types';

/**
 * Hook to run and save a valuation
 * Automatically invalidates the valuations list query on success
 */
export function useRunAndSaveValuation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (companyData: CompanyData) => ValuationsAPI.runAndSave(companyData),
    onSuccess: () => {
      // Invalidate the valuations list to refetch it
      queryClient.invalidateQueries({ queryKey: ['valuations'] });
    },
  });
}
