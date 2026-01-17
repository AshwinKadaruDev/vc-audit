import { useParams, useNavigate } from 'react-router-dom';
import { useValuation } from '../hooks/queries/useValuation';
import { ValuationCard } from '../components/ValuationCard';
import { AuditTrail } from '../components/AuditTrail';
import type { ValuationSummary, MethodResult, MethodSkipped, MethodComparisonData, MethodName, Confidence } from '../types';

export function ValuationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: valuation, isLoading: loading, error } = useValuation(id!);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error || !valuation) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => navigate('/valuations')}
          className="flex items-center gap-2 text-neutral-600 hover:text-neutral-900 text-sm font-medium"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Valuations
        </button>
        <div className="bg-error-50 border border-error-200 rounded-lg p-6">
          <h2 className="text-base font-semibold text-error-800">Error Loading Valuation</h2>
          <p className="text-sm text-error-700 mt-1">
            {error instanceof Error ? error.message : 'Valuation not found'}
          </p>
        </div>
      </div>
    );
  }

  // Convert saved valuation to the format expected by components
  const methodComparison: MethodComparisonData | undefined = valuation.summary.method_comparison
    ? {
        methods: valuation.summary.method_comparison.methods.map((m) => ({
          method: m.method as MethodName,
          value: m.value,
          confidence: m.confidence as Confidence,
          is_primary: m.is_primary,
        })),
        spread_percent: valuation.summary.method_comparison.spread_percent,
        spread_warning: valuation.summary.method_comparison.spread_warning,
        selection_steps: valuation.summary.method_comparison.selection_steps,
      }
    : undefined;

  const summary: ValuationSummary = {
    primary_value: valuation.summary.primary_value,
    primary_method: valuation.summary.primary_method as MethodName,
    value_range_low: valuation.summary.value_range_low,
    value_range_high: valuation.summary.value_range_high,
    overall_confidence: valuation.summary.overall_confidence as Confidence,
    summary_text: valuation.summary.summary_text,
    selection_reason: valuation.summary.selection_reason,
    method_comparison: methodComparison,
  };

  const methodResults: MethodResult[] = valuation.method_results.map((mr) => ({
    method: mr.method as MethodName,
    value: mr.value,
    confidence: mr.confidence as Confidence,
    audit_trail: mr.audit_trail,
    warnings: mr.warnings,
  }));

  const skippedMethods: MethodSkipped[] = valuation.skipped_methods.map((sm) => ({
    method: sm.method as MethodName,
    reason: sm.reason,
  }));

  return (
    <div className="space-y-5">
      {/* Back button */}
      <button
        onClick={() => navigate('/valuations')}
        className="flex items-center gap-2 text-neutral-600 hover:text-neutral-900 text-sm font-medium"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Valuations
      </button>

      {/* Valuation Card */}
      <ValuationCard
        summary={summary}
        companyName={valuation.company_name}
        valuationDate={valuation.valuation_date}
      />

      {/* Audit Trail */}
      <AuditTrail
        methodResults={methodResults}
        skippedMethods={skippedMethods}
        methodComparison={summary.method_comparison}
      />
    </div>
  );
}
