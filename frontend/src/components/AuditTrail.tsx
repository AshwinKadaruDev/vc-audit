import { useState } from 'react';
import type { MethodResult, AuditStep, MethodSkipped, MethodComparisonData, MethodName, DataSourceInfo, Confidence } from '../types';
import { formatCurrency, getMethodDisplayName } from '../utils/formatting';
import { getConfidenceColor, getConfidenceBgClass } from '../utils/confidence';
import { InfoTooltip } from './InfoTooltip';

interface AuditTrailProps {
  methodResults: MethodResult[];
  skippedMethods: MethodSkipped[];
  methodComparison?: MethodComparisonData;
  overallConfidence?: Confidence;
  overallConfidenceExplanation?: string;
}

interface ComparableCompany {
  ticker: string;
  name: string;
  revenue: string;
  market_cap: string;
  revenue_multiple: string;
  growth: string;
}

interface Adjustment {
  name: string;
  impact: string;
  reason: string;
}

interface FormulaVariable {
  name: string;
  symbol: string;
  value: string;
  derivation: string;
}

function SourceCitation({ source }: { source: DataSourceInfo }) {
  return (
    <div className="text-xs text-neutral-500 mt-3 pt-3 border-t border-neutral-200 flex items-center gap-1.5">
      <span className="text-neutral-400">Source:</span>
      <span>{source.citation}</span>
    </div>
  );
}

// Methods Summary Section Component
interface MethodsSummaryProps {
  methodComparison: MethodComparisonData;
  overallConfidence?: Confidence;
  overallConfidenceExplanation?: string;
}

function MethodsSummary({ methodComparison, overallConfidence, overallConfidenceExplanation }: MethodsSummaryProps) {
  return (
    <div className="space-y-4">
      {/* Methods Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-200">
              <th className="text-left py-3 text-subtext font-medium">Method</th>
              <th className="text-right py-3 text-subtext font-medium">Value</th>
              <th className="text-center py-3 text-subtext font-medium">Confidence</th>
              <th className="text-right py-3 text-subtext font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {methodComparison.methods.map((method) => (
              <tr key={method.method} className="border-b border-neutral-100">
                <td className="py-3 text-default-font font-medium">
                  {getMethodDisplayName(method.method)}
                </td>
                <td className="py-3 text-right text-default-font font-semibold">
                  {formatCurrency(method.value)}
                </td>
                <td className="py-3 text-center">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getConfidenceBgClass(method.confidence)} ${getConfidenceColor(method.confidence)}`}>
                    {method.confidence.charAt(0).toUpperCase() + method.confidence.slice(1)}
                  </span>
                </td>
                <td className="py-3 text-right">
                  {method.is_primary ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-neutral-900 text-white rounded text-xs font-medium">
                      PRIMARY
                    </span>
                  ) : (
                    <span className="text-xs text-neutral-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Overall Confidence Explanation */}
      {overallConfidenceExplanation && (
        <div className="p-3 bg-neutral-50 border border-neutral-200 rounded">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-default-font">Overall Confidence:</span>
            {overallConfidence && (
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getConfidenceBgClass(overallConfidence)} ${getConfidenceColor(overallConfidence)}`}>
                {overallConfidence.charAt(0).toUpperCase() + overallConfidence.slice(1)}
              </span>
            )}
          </div>
          <p className="text-sm text-neutral-600">{overallConfidenceExplanation}</p>
        </div>
      )}

      {/* Spread Warning */}
      {methodComparison.spread_warning && (
        <div className="p-3 bg-warning-50 border border-warning-200 rounded flex items-start gap-2">
          <span className="text-warning-600 flex-shrink-0">⚠</span>
          <p className="text-sm text-warning-800">{methodComparison.spread_warning}</p>
        </div>
      )}
    </div>
  );
}

function InputRenderer({ inputs }: { inputs: Record<string, unknown> }) {
  const type = inputs.type as string;

  // Funding Round
  if (type === 'funding_round') {
    return (
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-subtext">Round Date:</span>
            <span className="ml-2 text-default-font font-medium">{inputs.round_date as string}</span>
          </div>
          <div>
            <span className="text-subtext">Lead Investor:</span>
            <span className="ml-2 text-default-font font-medium">{inputs.lead_investor as string}</span>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="bg-neutral-50 p-3 rounded">
            <div className="text-subtext text-xs">Pre-Money Valuation</div>
            <div className="text-default-font font-semibold">{inputs.pre_money_valuation as string}</div>
          </div>
          <div className="bg-neutral-50 p-3 rounded">
            <div className="text-subtext text-xs">Amount Raised</div>
            <div className="text-default-font font-semibold">{inputs.amount_raised as string}</div>
          </div>
          <div className="bg-primary-50 p-3 rounded border border-primary-200">
            <div className="text-primary-600 text-xs font-medium">Post-Money Valuation</div>
            <div className="text-primary-700 font-semibold">{inputs.post_money_valuation as string}</div>
          </div>
        </div>
      </div>
    );
  }

  // Market Adjustment
  if (type === 'market_adjustment') {
    const direction = inputs.market_direction as string;
    const isUp = direction === 'increased';
    const changeColor = isUp ? 'text-green-600' : direction === 'decreased' ? 'text-red-600' : 'text-neutral-600';
    const dataSource = inputs.data_source as DataSourceInfo | undefined;

    return (
      <div className="space-y-4">
        <div className="bg-neutral-50 p-4 rounded">
          <div className="text-sm font-medium text-default-font mb-3">{String(inputs.index_name)} Index Movement</div>
          <div className="flex items-center justify-between">
            <div className="text-center">
              <div className="text-xs text-subtext">{inputs.round_date as string}</div>
              <div className="text-lg font-semibold text-default-font">{inputs.round_index_value as string}</div>
            </div>
            <div className="flex-1 flex items-center justify-center px-4">
              <div className="flex-1 h-0.5 bg-neutral-300"></div>
              <div className={`mx-2 px-3 py-1 rounded-full text-sm font-bold ${isUp ? 'bg-success-100 text-success-700' : 'bg-error-100 text-error-700'}`}>
                {inputs.market_change_percent as string}
              </div>
              <div className="flex-1 h-0.5 bg-neutral-300"></div>
            </div>
            <div className="text-center">
              <div className="text-xs text-subtext">{inputs.today_date as string}</div>
              <div className="text-lg font-semibold text-default-font">{inputs.today_index_value as string}</div>
            </div>
          </div>
        </div>

        <div className="bg-warning-50 border border-warning-200 p-3 rounded text-sm">
          <div className="font-medium text-warning-800 mb-1">Volatility Adjustment ({String(inputs.volatility_factor)}x factor)</div>
          <div className="text-warning-700">{inputs.volatility_explanation as string}</div>
        </div>

        <div className="text-sm">
          <span className="text-subtext">Adjusted valuation change: </span>
          <span className={`font-bold ${changeColor}`}>{inputs.adjusted_change_percent as string}</span>
        </div>

        {dataSource && <SourceCitation source={dataSource} />}
      </div>
    );
  }

  // Company Adjustments
  if (type === 'company_adjustments') {
    const adjustments = inputs.adjustments as Adjustment[];
    if (adjustments.length === 0) {
      return (
        <div className="text-sm text-subtext italic">No company-specific adjustments applied.</div>
      );
    }

    return (
      <div className="space-y-3">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-200">
              <th className="text-left py-2 text-subtext font-medium">Adjustment</th>
              <th className="text-right py-2 text-subtext font-medium">Impact</th>
              <th className="text-left py-2 pl-4 text-subtext font-medium">Reason</th>
            </tr>
          </thead>
          <tbody>
            {adjustments.map((adj, i) => (
              <tr key={i} className="border-b border-neutral-100">
                <td className="py-2 text-default-font font-medium">{adj.name}</td>
                <td className={`py-2 text-right font-semibold ${adj.impact.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                  {adj.impact}
                </td>
                <td className="py-2 pl-4 text-subtext">{adj.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="text-sm">
          <span className="text-subtext">Total adjustment: </span>
          <span className="font-bold text-default-font">{inputs.total_adjustment as string}</span>
        </div>
      </div>
    );
  }

  // Target Metrics
  if (type === 'target_metrics') {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div className="bg-neutral-50 p-3 rounded">
          <div className="text-subtext text-xs">Annual Revenue</div>
          <div className="text-default-font font-semibold">{inputs.annual_revenue as string}</div>
        </div>
        <div className="bg-neutral-50 p-3 rounded">
          <div className="text-subtext text-xs">Revenue Growth</div>
          <div className="text-default-font font-semibold">{inputs.revenue_growth as string}</div>
        </div>
        <div className="bg-neutral-50 p-3 rounded">
          <div className="text-subtext text-xs">Gross Margin</div>
          <div className="text-default-font font-semibold">{inputs.gross_margin as string}</div>
        </div>
        <div className="bg-neutral-50 p-3 rounded">
          <div className="text-subtext text-xs">Sector</div>
          <div className="text-default-font font-semibold">{inputs.sector as string}</div>
        </div>
      </div>
    );
  }

  // Comparable Companies
  if (type === 'comparable_companies') {
    const companies = inputs.companies as ComparableCompany[];
    const dataSource = inputs.data_source as DataSourceInfo | undefined;
    return (
      <div className="space-y-3">
        <div className="text-sm text-subtext">
          Data as of {inputs.data_as_of as string} for {inputs.sector as string} sector
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 bg-neutral-50">
                <th className="text-left py-2 px-3 text-subtext font-medium">Company</th>
                <th className="text-right py-2 px-3 text-subtext font-medium">Revenue</th>
                <th className="text-right py-2 px-3 text-subtext font-medium">Market Cap</th>
                <th className="text-right py-2 px-3 text-subtext font-medium">Multiple</th>
                <th className="text-right py-2 px-3 text-subtext font-medium">Growth</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.ticker} className="border-b border-neutral-100">
                  <td className="py-2 px-3">
                    <span className="font-medium text-default-font">{c.name}</span>
                    <span className="text-subtext ml-2">({c.ticker})</span>
                  </td>
                  <td className="py-2 px-3 text-right text-default-font">{c.revenue}</td>
                  <td className="py-2 px-3 text-right text-default-font">{c.market_cap}</td>
                  <td className="py-2 px-3 text-right font-semibold text-primary-600">{c.revenue_multiple}</td>
                  <td className="py-2 px-3 text-right text-default-font">{c.growth}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {dataSource && <SourceCitation source={dataSource} />}
      </div>
    );
  }

  // Multiple Statistics
  if (type === 'multiple_statistics') {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between bg-neutral-50 p-4 rounded">
          <div className="text-center">
            <div className="text-xs text-subtext">Lowest</div>
            <div className="text-lg font-semibold text-default-font">{inputs.lowest as string}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-subtext">25th %ile</div>
            <div className="text-lg font-semibold text-default-font">{inputs.percentile_25 as string}</div>
          </div>
          <div className="text-center bg-primary-100 px-4 py-2 rounded border border-primary-200">
            <div className="text-xs text-primary-600 font-medium">Median</div>
            <div className="text-xl font-bold text-primary-700">{inputs.median as string}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-subtext">75th %ile</div>
            <div className="text-lg font-semibold text-default-font">{inputs.percentile_75 as string}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-subtext">Highest</div>
            <div className="text-lg font-semibold text-default-font">{inputs.highest as string}</div>
          </div>
        </div>
        <div className="text-sm text-subtext">{inputs.explanation as string}</div>
      </div>
    );
  }

  // Private Discount
  if (type === 'private_discount') {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-4">
          <div className="bg-neutral-50 p-3 rounded text-center">
            <div className="text-xs text-subtext">Public Multiple</div>
            <div className="text-lg font-semibold text-default-font">{inputs.public_multiple as string}</div>
          </div>
          <div className="text-2xl text-neutral-400">−</div>
          <div className="bg-error-50 p-3 rounded text-center border border-error-200">
            <div className="text-xs text-error-600">Discount ({inputs.company_stage as string})</div>
            <div className="text-lg font-semibold text-error-700">{inputs.discount_percent as string}</div>
          </div>
          <div className="text-2xl text-neutral-400">=</div>
          <div className="bg-blue-50 p-3 rounded text-center border border-blue-200">
            <div className="text-xs text-primary-600 font-medium">Adjusted Multiple</div>
            <div className="text-lg font-semibold text-primary-700">{inputs.adjusted_multiple as string}</div>
          </div>
        </div>
        <div className="text-sm text-subtext">{inputs.explanation as string}</div>
      </div>
    );
  }

  // Final Calculation
  if (type === 'final_calculation') {
    return (
      <div className="flex items-center gap-4 text-lg">
        <div className="bg-neutral-50 p-3 rounded text-center">
          <div className="text-xs text-subtext">Revenue</div>
          <div className="font-semibold text-default-font">{inputs.revenue as string}</div>
        </div>
        <div className="text-2xl text-neutral-400">×</div>
        <div className="bg-neutral-50 p-3 rounded text-center">
          <div className="text-xs text-subtext">Multiple</div>
          <div className="font-semibold text-default-font">{inputs.multiple as string}</div>
        </div>
      </div>
    );
  }

  // Final Formula Summary
  if (type === 'final_formula') {
    const variables = inputs.variables as FormulaVariable[];
    return (
      <div className="space-y-4">
        {/* Formula Display - compact */}
        <div className="text-sm">
          <span className="text-subtext">Formula: </span>
          <span className="text-default-font">{inputs.formula_display as string}</span>
          <span className="text-subtext ml-2 font-mono text-xs">({inputs.formula_template as string})</span>
        </div>

        {/* Variables/Components - compact table style */}
        <div className="border border-neutral-200 rounded divide-y divide-neutral-100">
          {variables.map((variable) => (
            <div key={variable.symbol} className="flex items-center px-3 py-2 text-sm">
              <span className="w-6 h-6 rounded bg-primary-100 text-primary-600 font-semibold text-xs flex items-center justify-center flex-shrink-0">
                {variable.symbol}
              </span>
              <div className="ml-3 flex-1 min-w-0">
                <span className="font-medium text-default-font">{variable.name}</span>
                <span className="text-subtext ml-1 text-xs">— {variable.derivation}</span>
              </div>
              <span className="font-semibold text-primary-600 ml-2 flex-shrink-0">{variable.value}</span>
            </div>
          ))}
        </div>

        {/* Calculation with values - inline */}
        <div className="bg-neutral-50 border border-neutral-200 rounded px-3 py-2">
          <span className="text-xs text-subtext mr-2">Calculation:</span>
          <span className="text-sm font-mono text-default-font">{inputs.formula_with_values as string}</span>
        </div>

        {/* Final Value - compact highlight */}
        <div className="bg-primary-50 border border-primary-200 rounded px-4 py-3 flex items-center justify-between">
          <span className="text-sm font-medium text-primary-700">Final Valuation</span>
          <span className="text-xl font-bold text-primary-600">{inputs.final_value as string}</span>
        </div>
      </div>
    );
  }

  return null;
}

function StepDetails({ step }: { step: AuditStep }) {
  const [expanded, setExpanded] = useState(false); // Default closed
  const hasInputs = Object.keys(step.inputs).length > 0 && Boolean(step.inputs.type);

  return (
    <div className="rounded border border-neutral-200 bg-white overflow-hidden">
      {/* Header */}
      <div
        className={`flex items-start gap-3 p-4 cursor-pointer transition-colors ${expanded ? 'bg-white' : 'hover:bg-primary-50/30'}`}
        onClick={() => setExpanded(!expanded)}
      >
        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-xs flex items-center justify-center font-bold">
          {step.step_number}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-default-font">{step.description}</p>
          {step.result && (
            <p className="text-primary-600 font-semibold text-sm mt-1">{step.result}</p>
          )}
        </div>
        <span className="text-neutral-400 flex-shrink-0 text-sm">
          {expanded ? '−' : '+'}
        </span>
      </div>

      {/* Content body */}
      {expanded && (hasInputs || step.calculation) && (
        <div className="px-4 pb-4 pt-2 border-t border-neutral-100 space-y-4 bg-neutral-50">
          {hasInputs && <InputRenderer inputs={step.inputs} />}
          {step.calculation && (
            <div className="text-sm text-neutral-600 bg-white p-3 rounded border border-neutral-200">
              {step.calculation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Simple tab button
function MethodTab({
  result,
  isActive,
  onClick,
}: {
  result: MethodResult;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
        isActive
          ? 'border-primary-500 text-primary-500'
          : 'border-transparent text-neutral-500 hover:text-neutral-700'
      }`}
    >
      {getMethodDisplayName(result.method)}
    </button>
  );
}

export function AuditTrail({
  methodResults,
  skippedMethods,
  methodComparison,
  overallConfidence,
  overallConfidenceExplanation,
}: AuditTrailProps) {
  const [activeMethod, setActiveMethod] = useState(0);

  if (methodResults.length === 0) {
    return null;
  }

  const activeResult = methodResults[activeMethod];
  const hasMultipleMethods = methodResults.length > 1;

  return (
    <div className="bg-white border border-neutral-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-neutral-200">
        <h3 className="text-lg font-semibold text-default-font">Audit Trail</h3>
        <p className="text-sm text-subtext mt-0.5">Complete breakdown of valuation calculation</p>
      </div>

      {/* Methods Summary - Only show if multiple methods */}
      {hasMultipleMethods && methodComparison && (
        <div className="px-6 py-5">
          <div className="flex items-center mb-4">
            <h4 className="text-sm font-semibold text-default-font">Valuation Methods Summary</h4>
            {methodComparison.selection_steps.length > 0 && (
              <InfoTooltip>
                <div className="space-y-3">
                  <h5 className="font-semibold text-sm text-default-font">How We Selected the Primary Valuation</h5>
                  <ol className="space-y-2">
                    {methodComparison.selection_steps.map((step, index) => (
                      <li key={index} className="flex gap-3 text-sm">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary-100 text-primary-600 text-xs flex items-center justify-center font-bold">
                          {index + 1}
                        </span>
                        <span className="text-default-font">{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </InfoTooltip>
            )}
          </div>
          <MethodsSummary
            methodComparison={methodComparison}
            overallConfidence={overallConfidence}
            overallConfidenceExplanation={overallConfidenceExplanation}
          />
        </div>
      )}

      {/* Method Details Section */}
      <div className={`${hasMultipleMethods ? 'border-t border-neutral-200 mt-6' : 'border-t border-neutral-200'}`}>
        {/* Tab bar - only show if multiple methods */}
        {hasMultipleMethods && (
          <div className="flex px-6 pt-6 border-b border-neutral-200">
            {methodResults.map((result, index) => (
              <MethodTab
                key={result.method}
                result={result}
                isActive={index === activeMethod}
                onClick={() => setActiveMethod(index)}
              />
            ))}
          </div>
        )}

        {/* Active method header */}
        <div className="px-6 py-5 bg-primary-50/30 border-b border-primary-100">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-default-font text-base">
                {getMethodDisplayName(activeResult.method)}
              </h4>
              <p className="text-xs text-subtext mt-0.5">Step-by-step calculation</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-primary-600">{formatCurrency(activeResult.value)}</div>
              <div className={`text-xs font-semibold mt-1 ${getConfidenceColor(activeResult.confidence)}`}>
                {activeResult.confidence.charAt(0).toUpperCase() + activeResult.confidence.slice(1)} Confidence
              </div>
            </div>
          </div>
          {/* Method Confidence Explanation */}
          {activeResult.confidence_explanation && (
            <div className="mt-3 p-3 bg-white/80 rounded border border-neutral-200 text-sm text-neutral-600">
              <span className="font-medium text-neutral-700">How was this calculated? </span>
              {activeResult.confidence_explanation}
            </div>
          )}
        </div>

        {/* Steps */}
        <div className="p-6 space-y-3">
          {activeResult.warnings.length > 0 && (
            <div className="p-3 bg-warning-50 border border-warning-200 rounded mb-4">
              {activeResult.warnings.map((warning, index) => (
                <p key={index} className="text-sm text-warning-800">
                  {warning}
                </p>
              ))}
            </div>
          )}

          {activeResult.audit_trail.map((step) => (
            <StepDetails key={step.step_number} step={step} />
          ))}
        </div>
      </div>

      {/* Skipped Methods */}
      {skippedMethods.length > 0 && (
        <div className="px-6 py-4 bg-neutral-50 border-t border-neutral-200">
          <h4 className="text-sm font-medium text-subtext mb-2">Methods Not Applied</h4>
          <ul className="space-y-1">
            {skippedMethods.map((skipped) => (
              <li key={skipped.method} className="text-sm text-subtext">
                <span className="font-medium">{getMethodDisplayName(skipped.method as MethodName)}:</span>{' '}
                {skipped.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
