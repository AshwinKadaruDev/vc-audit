import type { CompanyListItem } from '../types';

interface CompanySelectorProps {
  companies: CompanyListItem[];
  selectedCompany: string | null;
  onSelect: (companyId: string) => void;
  onRunValuation: () => void;
  loading: boolean;
}

export function CompanySelector({
  companies,
  selectedCompany,
  onSelect,
  onRunValuation,
  loading,
}: CompanySelectorProps) {
  return (
    <div className="bg-neutral-0 border border-neutral-border rounded-lg p-6">
      <h2 className="text-lg font-semibold text-default-font mb-4">
        Select Company
      </h2>
      <div className="flex gap-4">
        <select
          value={selectedCompany || ''}
          onChange={(e) => onSelect(e.target.value)}
          className="flex-1 px-3 py-2 border border-neutral-300 rounded-md text-default-font bg-neutral-0 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        >
          <option value="">Choose a company...</option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.name} ({company.sector} - {company.stage.replace('_', ' ')})
            </option>
          ))}
        </select>
        <button
          onClick={onRunValuation}
          disabled={!selectedCompany || loading}
          className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:bg-neutral-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Running...' : 'Run Valuation'}
        </button>
      </div>
    </div>
  );
}
