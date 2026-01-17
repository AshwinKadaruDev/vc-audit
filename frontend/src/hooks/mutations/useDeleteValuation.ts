import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ValuationsAPI } from '../../api';

/**
 * Hook to delete a saved valuation
 */
export function useDeleteValuation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => ValuationsAPI.delete(id),
    onSuccess: () => {
      // Invalidate valuations list to refresh the UI
      queryClient.invalidateQueries({ queryKey: ['valuations'] });
    },
  });
}
