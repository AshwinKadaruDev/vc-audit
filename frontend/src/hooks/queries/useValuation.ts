import { useQuery } from '@tanstack/react-query';
import { ValuationsAPI } from '../../api';

/**
 * Hook to fetch a single valuation by ID
 */
export function useValuation(id: string) {
  return useQuery({
    queryKey: ['valuations', id],
    queryFn: () => ValuationsAPI.get(id),
    enabled: !!id,
  });
}
