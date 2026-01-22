import { useState } from 'react';
import { ValuationsAPI } from '../api';
import { CompanyForm } from '../components/CompanyForm';
import { ValuationCard } from '../components/ValuationCard';
import { AuditTrail } from '../components/AuditTrail';
import type { CompanyData, ValuationResult } from '../types';

export function ValuationPage() {
  const [result, setResult] = useState<ValuationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async (companyData: CompanyData) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const valuation = await ValuationsAPI.runCustom(companyData);
      setResult(valuation);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Valuation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="bg-white border-b border-neutral-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold text-default-font">VC Audit Tool</h1>
          <p className="text-subtext">Portfolio valuation with full audit trail</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {!result ? (
          <>
            <CompanyForm onProcess={handleProcess} loading={loading} />

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl shadow-sm p-4">
                <p className="text-red-800 font-medium">Valuation Error</p>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-default-font">Valuation Results</h2>
              <button
                onClick={handleReset}
                className="px-4 py-2 text-sm font-medium text-primary-600 bg-primary-50 hover:bg-primary-100 border border-primary-200 rounded-lg transition-colors"
              >
                + New Valuation
              </button>
            </div>

            <ValuationCard
              summary={result.summary}
              companyName={result.company_name}
              valuationDate={result.valuation_date}
            />

            <AuditTrail
              methodResults={result.method_results}
              skippedMethods={result.skipped_methods}
              methodComparison={result.summary.method_comparison}
              overallConfidence={result.summary.overall_confidence}
              overallConfidenceExplanation={result.summary.confidence_explanation}
            />
          </>
        )}
      </main>
    </div>
  );
}
