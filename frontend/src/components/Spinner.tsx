import React from 'react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'h-6 w-6 border-2',
  md: 'h-12 w-12 border-b-2',
  lg: 'h-16 w-16 border-b-3',
};

export const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
  function Spinner({ size = 'md', className = '' }, ref) {
    return (
      <div ref={ref} className="flex items-center justify-center">
        <div
          className={`animate-spin rounded-full border-primary-500 ${sizeClasses[size]} ${className}`}
        />
      </div>
    );
  }
);
