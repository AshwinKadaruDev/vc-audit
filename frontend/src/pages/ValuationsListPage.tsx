import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useValuations } from '../hooks/queries/useValuations';
import { useDeleteValuation } from '../hooks/mutations/useDeleteValuation';
import { formatCurrency, formatDate, getMethodDisplayName } from '../utils/formatting';
import { getConfidenceBadgeClass } from '../utils/confidence';

export function ValuationsListPage() {
  const navigate = useNavigate();
  const { data: valuations = [], isLoading: loading, error } = useValuations();
  const deleteMutation = useDeleteValuation();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string, companyName: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent row click navigation

    if (!window.confirm(`Are you sure you want to delete the valuation for "${companyName}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(id);
    } catch (error) {
      console.error('Failed to delete valuation:', error);
      alert('Failed to delete valuation. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-error-50 border border-error-200 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-error-800">Error Loading Valuations</h2>
        <p className="text-error-700 mt-2">{error instanceof Error ? error.message : 'Failed to load valuations'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with action button */}
      <div className="flex items-center justify-between">
        <p className="text-subtext">
          {valuations.length === 0
            ? 'No valuations yet. Create your first one!'
            : `${valuations.length} valuation${valuations.length === 1 ? '' : 's'}`}
        </p>
        <button
          onClick={() => navigate('/valuations/new')}
          className="px-4 py-2 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Valuation
        </button>
      </div>

      {/* Empty state */}
      {valuations.length === 0 ? (
        <div className="bg-white border border-neutral-200 rounded-xl p-12 text-center">
          <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-default-font mb-2">No Valuations Yet</h3>
          <p className="text-subtext mb-6">
            Start by creating your first portfolio valuation with full audit trail.
          </p>
          <button
            onClick={() => navigate('/valuations/new')}
            className="px-6 py-3 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 transition-colors"
          >
            Create Your First Valuation
          </button>
        </div>
      ) : (
        /* Valuations table */
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full min-w-full">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  <th className="text-left px-8 py-4 text-xs font-semibold text-neutral-600 uppercase tracking-wider w-1/4">
                    Company
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-600 uppercase tracking-wider w-1/6">
                    Value
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-neutral-600 uppercase tracking-wider w-1/6">
                    Method
                  </th>
                  <th className="text-left px-6 py-4 text-xs font-semibold text-neutral-600 uppercase tracking-wider w-1/6">
                    Confidence
                  </th>
                  <th className="text-right px-6 py-4 text-xs font-semibold text-neutral-600 uppercase tracking-wider w-1/6">
                    Date
                  </th>
                  <th className="text-right px-8 py-4 text-xs font-semibold text-neutral-600 uppercase tracking-wider w-20">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {valuations.map((valuation) => (
                  <tr
                    key={valuation.id}
                    onClick={() => navigate(`/valuations/${valuation.id}`)}
                    className="hover:bg-neutral-50 cursor-pointer transition-colors group"
                  >
                    <td className="px-8 py-5">
                      <div className="font-semibold text-neutral-900 text-base">
                        {valuation.company_name}
                      </div>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <div className="text-base font-bold text-neutral-900">
                        {formatCurrency(valuation.primary_value)}
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <span className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-primary-50 text-primary-700 border border-primary-100">
                        {getMethodDisplayName(valuation.primary_method, false)}
                      </span>
                    </td>
                    <td className="px-6 py-5">
                      <span className={`inline-flex items-center px-3 py-1 rounded-md text-xs font-medium capitalize ${getConfidenceBadgeClass(valuation.overall_confidence)}`}>
                        {valuation.overall_confidence}
                      </span>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <span className="text-sm text-neutral-600">
                        {formatDate(valuation.valuation_date)}
                      </span>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <button
                        onClick={(e) => handleDelete(valuation.id, valuation.company_name, e)}
                        disabled={deletingId === valuation.id}
                        className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-neutral-400 hover:text-error-600 hover:bg-error-50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Delete valuation"
                      >
                        {deletingId === valuation.id ? (
                          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
