import { useQuery } from '@tanstack/react-query';
import { ValuationsAPI } from '../../api';

/**
 * Hook to fetch the list of saved valuations
 */
export function useValuations() {
  return useQuery({
    queryKey: ['valuations'],
    queryFn: () => ValuationsAPI.list(),
  });
}
