import { useQuery } from '@tanstack/react-query';
import { CompaniesAPI } from '../../api';

/**
 * Hook to fetch the list of available sectors
 */
export function useSectors() {
  return useQuery({
    queryKey: ['sectors'],
    queryFn: () => CompaniesAPI.listSectors(),
  });
}
