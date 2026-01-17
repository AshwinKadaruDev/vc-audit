import type { Confidence } from '../types';

/**
 * Gets the badge classes for a confidence level
 */
export function getConfidenceBadgeClass(confidence: string): string {
  switch (confidence) {
    case 'high':
      return 'bg-success-100 text-success-800';
    case 'medium':
      return 'bg-warning-100 text-warning-800';
    case 'low':
      return 'bg-error-100 text-error-800';
    default:
      return 'bg-neutral-100 text-neutral-800';
  }
}

/**
 * Gets the text color class for a confidence level
 */
export function getConfidenceColor(confidence: Confidence | string): string {
  switch (confidence) {
    case 'high':
      return 'text-success-600';
    case 'medium':
      return 'text-warning-600';
    case 'low':
      return 'text-error-600';
    default:
      return 'text-neutral-600';
  }
}

/**
 * Gets the background color class for a confidence level
 */
export function getConfidenceBgClass(confidence: Confidence | string): string {
  switch (confidence) {
    case 'high':
      return 'bg-success-50';
    case 'medium':
      return 'bg-warning-50';
    case 'low':
      return 'bg-error-50';
    default:
      return 'bg-neutral-50';
  }
}

/**
 * Capitalizes the first letter of a confidence level
 */
export function getConfidenceLabel(confidence: string): string {
  return confidence.charAt(0).toUpperCase() + confidence.slice(1);
}
