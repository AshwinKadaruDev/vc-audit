import { useNavigate } from 'react-router-dom';
import { useRunAndSaveValuation } from '../hooks/mutations/useRunAndSaveValuation';
import { CompanyForm } from '../components/CompanyForm';
import type { CompanyData } from '../types';

export function NewValuationPage() {
  const navigate = useNavigate();
  const { mutate: runAndSave, isPending: loading, error } = useRunAndSaveValuation();

  const handleProcess = (companyData: CompanyData) => {
    runAndSave(companyData, {
      onSuccess: (result) => {
        // Navigate to the detail page with the new valuation ID
        navigate(`/valuations/${result.id}`);
      },
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <CompanyForm onProcess={handleProcess} loading={loading} />

      {error && (
        <div className="bg-error-50 border border-error-200 rounded-xl shadow-sm p-4">
          <p className="text-error-800 font-medium">Valuation Error</p>
          <p className="text-error-700 text-sm mt-1">
            {error instanceof Error ? error.message : 'Valuation failed'}
          </p>
        </div>
      )}
    </div>
  );
}
