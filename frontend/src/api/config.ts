/**
 * API Configuration and Shared Utilities
 */

import type { ErrorResponse } from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Get a user-friendly error message based on HTTP status code
 */
function getStatusErrorMessage(status: number): string {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input.';
    case 401:
      return 'Authentication required. Please log in.';
    case 403:
      return 'Access denied. You do not have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 408:
      return 'Request timeout. Please try again.';
    case 409:
      return 'Conflict. The resource already exists or is in an inconsistent state.';
    case 422:
      return 'Validation error. Please check your input.';
    case 429:
      return 'Too many requests. Please slow down and try again later.';
    case 500:
      return 'Internal server error. Please try again later.';
    case 502:
      return 'Bad gateway. The server is temporarily unavailable.';
    case 503:
      return 'Service unavailable. Please try again later.';
    case 504:
      return 'Gateway timeout. The server took too long to respond.';
    default:
      return `HTTP error! status: ${status}`;
  }
}

/**
 * Generic response handler for API calls
 * Provides detailed error messages based on HTTP status codes
 * @throws Error with message from API or status-specific error
 */
export async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ErrorResponse | null = null;

    // Try to parse error response
    try {
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        errorData = await response.json();
      }
    } catch {
      // If parsing fails, fall through to status-based error
    }

    // Use API error message if available, otherwise use status-based message
    const errorMessage = errorData?.message || getStatusErrorMessage(response.status);
    throw new Error(errorMessage);
  }

  return response.json();
}
