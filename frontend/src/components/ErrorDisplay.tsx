import React from 'react';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  variant?: 'page' | 'inline';
  className?: string;
}

export const ErrorDisplay = React.forwardRef<HTMLDivElement, ErrorDisplayProps>(
  function ErrorDisplay(
    {
      title = 'Error',
      message,
      onRetry,
      variant = 'inline',
      className = '',
    },
    ref
  ) {
    const baseClasses = 'bg-error-50 border border-error-200 rounded-lg';
    const variantClasses = variant === 'page' ? 'p-12 text-center' : 'p-4';

    return (
      <div ref={ref} className={`${baseClasses} ${variantClasses} ${className}`}>
        {variant === 'page' && (
          <div className="w-16 h-16 bg-error-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-error-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        )}

        <h2
          className={`font-semibold text-error-800 ${
            variant === 'page' ? 'text-lg mb-2' : 'text-base'
          }`}
        >
          {title}
        </h2>
        <p
          className={`text-error-700 ${
            variant === 'page' ? 'text-base mb-6' : 'text-sm mt-1'
          }`}
        >
          {message}
        </p>

        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-4 px-6 py-2 bg-error-600 text-white rounded-lg font-medium hover:bg-error-700 transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }
);
