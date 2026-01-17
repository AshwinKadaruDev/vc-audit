import { useState } from 'react';
import type { ValuationSummary } from '../types';
import { formatCurrency, getMethodDisplayName } from '../utils/formatting';
import { getConfidenceBadgeClass, getConfidenceLabel } from '../utils/confidence';

interface ValuationCardProps {
  summary: ValuationSummary;
  companyName: string;
  valuationDate: string;
}

interface ValuationRangeBarProps {
  lowValue: string;
  highValue: string;
  primaryValue: string;
  comparison?: ValuationSummary['method_comparison'];
}

function ValuationRangeBar({ lowValue, highValue, primaryValue, comparison }: ValuationRangeBarProps) {
  const low = parseFloat(lowValue);
  const high = parseFloat(highValue);
  const primary = parseFloat(primaryValue);

  // Calculate position of primary value on the range (0 to 100)
  const range = high - low;
  const position = range > 0 ? ((primary - low) / range) * 100 : 0;

  // Get method names for labels
  const methods = comparison?.methods || [];
  const lowMethod = methods.find(m => parseFloat(m.value) === low);
  const highMethod = methods.find(m => parseFloat(m.value) === high);

  const lowMethodName = lowMethod ? getMethodDisplayName(lowMethod.method).replace(' Method', '') : '';
  const highMethodName = highMethod ? getMethodDisplayName(highMethod.method).replace(' Method', '') : '';

  return (
    <div className="flex-shrink-0 w-80">
      <div className="text-xs font-medium text-subtext uppercase tracking-wide mb-3">Valuation Range</div>

      <div className="relative">
        {/* Range bar */}
        <div className="h-1.5 bg-neutral-100 rounded-full relative">
          {/* Filled portion up to primary value */}
          <div
            className="absolute h-full bg-neutral-400 rounded-full"
            style={{ width: `${position}%` }}
          />
          {/* Primary value marker */}
          <div
            className="absolute w-3 h-3 bg-neutral-700 rounded-full -top-0.5"
            style={{ left: `calc(${position}% - 6px)` }}
          />
        </div>

        {/* Labels */}
        <div className="flex justify-between mt-3 text-xs">
          <div className="text-left">
            <div className="font-semibold text-default-font">{formatCurrency(lowValue)}</div>
            {lowMethodName && <div className="text-subtext mt-0.5">{lowMethodName}</div>}
          </div>
          <div className="text-right">
            <div className="font-semibold text-default-font">{formatCurrency(highValue)}</div>
            {highMethodName && <div className="text-subtext mt-0.5">{highMethodName}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

interface WhyThisNumberProps {
  selectionReason: string;
}

function WhyThisNumber({ selectionReason }: WhyThisNumberProps) {
  const [expanded, setExpanded] = useState(false);

  if (!selectionReason) return null;

  return (
    <div className="mt-4 pt-4 border-t border-neutral-100">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-primary-500 hover:text-primary-600 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={expanded ? "M19 9l-7 7-7-7" : "M9 5l7 7-7 7"} />
        </svg>
        <span>Why this number?</span>
      </button>

      {expanded && (
        <div className="mt-3 p-4 bg-gradient-to-br from-primary-50 to-indigo-50 border border-primary-200 rounded-lg text-sm text-neutral-700 leading-relaxed shadow-sm">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-primary-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>{selectionReason}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export function ValuationCard({ summary, companyName, valuationDate }: ValuationCardProps) {
  const hasRange = summary.value_range_low && summary.value_range_high;
  const confidenceLabel = getConfidenceLabel(summary.overall_confidence);

  return (
    <div className="bg-white border border-neutral-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="border-b border-neutral-100 px-6 py-4">
        <h2 className="text-xl font-semibold text-default-font">{companyName}</h2>
        <p className="text-sm text-subtext mt-0.5">Valuation as of {valuationDate}</p>
      </div>

      {/* Primary Valuation and Range - Horizontal Layout */}
      <div className="px-6 py-6">
        <div className="flex items-start justify-between gap-8">
          {/* Left: Primary Value */}
          <div className="flex-1">
            <div className="flex items-baseline gap-4 mb-1">
              <div className="text-5xl font-bold text-primary-500 tracking-tight">
                {formatCurrency(summary.primary_value)}
              </div>
              <div className={`text-sm font-semibold px-2.5 py-1 rounded ${getConfidenceBadgeClass(summary.overall_confidence)}`}>
                {confidenceLabel} Confidence
              </div>
            </div>
            <div className="text-sm text-subtext mt-2">
              via {getMethodDisplayName(summary.primary_method)}
            </div>
          </div>

          {/* Right: Valuation Range Bar */}
          {hasRange && (
            <ValuationRangeBar
              lowValue={summary.value_range_low!}
              highValue={summary.value_range_high!}
              primaryValue={summary.primary_value}
              comparison={summary.method_comparison}
            />
          )}
        </div>

        {/* Why this number? */}
        <WhyThisNumber selectionReason={summary.selection_reason} />
      </div>
    </div>
  );
}
