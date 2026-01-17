import { useQuery } from '@tanstack/react-query';
import { PortfolioCompaniesAPI } from '../../api';

/**
 * Hook to fetch a random portfolio company
 * Use the refetch function to get a new random company
 */
export function useRandomPortfolioCompany() {
  return useQuery({
    queryKey: ['portfolio-companies', 'random'],
    queryFn: () => PortfolioCompaniesAPI.getRandom(),
    enabled: false, // Don't auto-fetch on mount
  });
}
