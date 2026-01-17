import React, { useState, useRef, useEffect } from 'react';

interface InfoTooltipProps {
  children: React.ReactNode;
  className?: string;
}

export const InfoTooltip = React.forwardRef<HTMLDivElement, InfoTooltipProps>(
  function InfoTooltip({ children, className = '' }, ref) {
    const [isVisible, setIsVisible] = useState(false);
    const tooltipRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      function handleClickOutside(event: MouseEvent) {
        if (tooltipRef.current && !tooltipRef.current.contains(event.target as Node)) {
          setIsVisible(false);
        }
      }

      if (isVisible) {
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
      }
    }, [isVisible]);

    return (
      <div ref={ref} className={`relative inline-block ${className}`}>
        <div ref={tooltipRef}>
          <button
            type="button"
            onMouseEnter={() => setIsVisible(true)}
            onMouseLeave={() => setIsVisible(false)}
            onClick={() => setIsVisible(!isVisible)}
            className="inline-flex items-center justify-center w-4 h-4 ml-2 text-xs text-neutral-500 hover:text-neutral-700 transition-colors"
            aria-label="More information"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="w-4 h-4"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
              />
            </svg>
          </button>

          {isVisible && (
            <div className="absolute z-50 left-0 top-full mt-2 w-96 bg-white border border-neutral-300 rounded-lg shadow-lg p-4">
              {children}
            </div>
          )}
        </div>
      </div>
    );
  }
);
