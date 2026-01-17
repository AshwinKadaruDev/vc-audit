import type { MethodName } from '../types';

/**
 * Formats a number or string as currency with appropriate suffix (K, M, B)
 */
export function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(num)) {
    return '$0';
  }

  if (num >= 1_000_000_000) {
    return `$${(num / 1_000_000_000).toFixed(2)}B`;
  }
  if (num >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(2)}M`;
  }
  if (num >= 1_000) {
    return `$${(num / 1_000).toFixed(2)}K`;
  }
  return `$${num.toFixed(2)}`;
}

/**
 * Formats a date string as a human-readable date
 */
export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Gets the display name for a valuation method
 */
export function getMethodDisplayName(method: MethodName, includeMethodSuffix = true): string {
  const names: Record<MethodName, string> = {
    last_round: 'Last Round',
    comparables: 'Comparables',
  };

  const baseName = names[method] || method.replace('_', ' ');
  return includeMethodSuffix ? `${baseName} Method` : baseName;
}

/**
 * Formats a percentage value
 */
export function formatPercentage(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(num)) {
    return '0%';
  }

  return `${num.toFixed(1)}%`;
}

/**
 * Formats a large number with commas
 */
export function formatNumber(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;

  if (isNaN(num)) {
    return '0';
  }

  return num.toLocaleString('en-US');
}
