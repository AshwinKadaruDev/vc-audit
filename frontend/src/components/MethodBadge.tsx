import type { MethodName, Confidence } from '../types';
import { getMethodDisplayName } from '../utils/formatting';

interface MethodBadgeProps {
  method: MethodName;
  confidence?: Confidence;
}

const confidenceColors: Record<Confidence, string> = {
  high: 'bg-success-100 text-success-800 border-success-200',
  medium: 'bg-warning-100 text-warning-800 border-warning-200',
  low: 'bg-error-100 text-error-800 border-error-200',
};

export function MethodBadge({ method, confidence }: MethodBadgeProps) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-100 text-neutral-700 border border-neutral-200">
        {getMethodDisplayName(method, false)}
      </span>
      {confidence && (
        <span
          className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${confidenceColors[confidence]}`}
        >
          {confidence}
        </span>
      )}
    </span>
  );
}
