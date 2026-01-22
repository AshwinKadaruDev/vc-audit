import { useState, useEffect, useRef } from 'react';
import type { CompanyData, PortfolioCompany } from '../types';
import { CompaniesAPI, PortfolioCompaniesAPI } from '../api';
import { STAGES, LEAD_INVESTORS, ADJUSTMENT_PRESETS } from '../constants';

// Fisher-Yates shuffle
function shuffleArray<T>(array: T[]): T[] {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

interface CompanyFormProps {
  onProcess: (data: CompanyData) => void;
  loading: boolean;
}

function createEmptyCompanyData(defaultSector: string): CompanyData {
  return {
    company: {
      id: 'custom',
      name: '',
      sector: defaultSector,
      stage: 'series_a',
    },
    financials: {},
    adjustments: [],
  };
}

export function CompanyForm({ onProcess, loading }: CompanyFormProps) {
  const [sectors, setSectors] = useState<string[]>([]);
  const [formData, setFormData] = useState<CompanyData>(createEmptyCompanyData('saas'));
  const [randomizing, setRandomizing] = useState(false);
  const [selectedAdjustmentId, setSelectedAdjustmentId] = useState<string>('');

  // Round-robin randomization: cycle through shuffled companies
  const companiesRef = useRef<PortfolioCompany[]>([]);
  const indexRef = useRef(0);

  useEffect(() => {
    CompaniesAPI.listSectors()
      .then((sectorList) => {
        setSectors(sectorList);
        if (sectorList.length > 0 && !sectorList.includes(formData.company.sector)) {
          setFormData(prev => ({
            ...prev,
            company: { ...prev.company, sector: sectorList[0] },
          }));
        }
      })
      .catch(console.error);
  }, []);

  const handleRandomize = async () => {
    setRandomizing(true);
    try {
      // Fetch and shuffle companies on first click, or reshuffle when we've cycled through all
      if (companiesRef.current.length === 0 || indexRef.current >= companiesRef.current.length) {
        const allCompanies = await PortfolioCompaniesAPI.list();
        companiesRef.current = shuffleArray(allCompanies);
        indexRef.current = 0;
      }

      // Get next company in the shuffled list
      const randomCompany = companiesRef.current[indexRef.current];
      indexRef.current++;

      // Convert PortfolioCompany to CompanyData format
      const companyData: CompanyData = {
        company: {
          id: randomCompany.id,
          name: randomCompany.name,
          sector: randomCompany.sector_id,
          stage: randomCompany.stage,
          founded_date: randomCompany.founded_date,
        },
        financials: randomCompany.financials || {},
        last_round: randomCompany.last_round || undefined,
        adjustments: randomCompany.adjustments || [],
      };

      setFormData(companyData);
    } catch (error) {
      console.error('Failed to randomize company:', error);
    } finally {
      setRandomizing(false);
    }
  };

  const updateCompany = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      company: { ...prev.company, [field]: value },
    }));
  };

  const updateFinancials = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      financials: { ...prev.financials, [field]: value || undefined },
    }));
  };

  const updateLastRound = (field: string, value: string) => {
    if (!value && !formData.last_round) return;

    setFormData(prev => {
      if (!value && prev.last_round) {
        const newRound = { ...prev.last_round, [field]: undefined };
        const hasValues = Object.values(newRound).some(v => v);
        return {
          ...prev,
          last_round: hasValues ? newRound as CompanyData['last_round'] : undefined,
        };
      }
      return {
        ...prev,
        last_round: { ...prev.last_round, [field]: value } as CompanyData['last_round'],
      };
    });
  };

  const addPresetAdjustment = () => {
    if (!selectedAdjustmentId) return;

    const preset = ADJUSTMENT_PRESETS.find(p => p.id === selectedAdjustmentId);
    if (!preset) return;

    // Check if already added
    if (formData.adjustments.some(a => a.name === preset.name)) {
      setSelectedAdjustmentId('');
      return;
    }

    setFormData(prev => ({
      ...prev,
      adjustments: [...prev.adjustments, {
        name: preset.name,
        factor: preset.factor,
        reason: preset.reason,
      }],
    }));
    setSelectedAdjustmentId('');
  };

  const removeAdjustment = (index: number) => {
    setFormData(prev => ({
      ...prev,
      adjustments: prev.adjustments.filter((_, i) => i !== index),
    }));
  };

  const isValid = formData.company.name.trim() !== '';

  const availableAdjustments = ADJUSTMENT_PRESETS.filter(
    preset => !formData.adjustments.some(a => a.name === preset.name)
  );

  const positiveAdjustments = availableAdjustments.filter(a => a.category === 'positive');
  const negativeAdjustments = availableAdjustments.filter(a => a.category === 'negative');

  return (
    <div className="bg-neutral-0 border border-neutral-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-neutral-border bg-neutral-50">
        <h2 className="text-lg font-semibold text-default-font">Company Information</h2>
        <p className="text-sm text-subtext mt-1">
          Enter company details manually or select an existing company to prefill
        </p>
      </div>

      <div className="p-6 space-y-6">
        {/* Randomize Button */}
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-primary-700">Quick Start</p>
              <p className="text-xs text-primary-600 mt-1">
                Fill with sample portfolio company data
              </p>
            </div>
            <button
              type="button"
              onClick={handleRandomize}
              disabled={randomizing}
              className="px-4 py-2 bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-600 disabled:bg-primary-400 transition-colors flex items-center gap-2"
            >
              {randomizing ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Randomize
                </>
              )}
            </button>
          </div>
        </div>

        {/* Basic Info */}
        <div>
          <h3 className="text-sm font-semibold text-default-font mb-3 flex items-center">
            <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-xs flex items-center justify-center mr-2">1</span>
            Basic Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-subtext mb-1">Company Name *</label>
              <input
                type="text"
                value={formData.company.name}
                onChange={(e) => updateCompany('name', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Sector</label>
              <select
                value={formData.company.sector}
                onChange={(e) => updateCompany('sector', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sectors.map((sector) => (
                  <option key={sector} value={sector}>
                    {sector.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Stage</label>
              <select
                value={formData.company.stage}
                onChange={(e) => updateCompany('stage', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {STAGES.map((stage) => (
                  <option key={stage.value} value={stage.value}>
                    {stage.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Financials */}
        <div>
          <h3 className="text-sm font-semibold text-default-font mb-3 flex items-center">
            <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-xs flex items-center justify-center mr-2">2</span>
            Financial Metrics
            <span className="text-xs text-subtext font-normal ml-2">(Leave blank if not available)</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-subtext mb-1">Annual Revenue (TTM)</label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-subtext">$</span>
                <input
                  type="number"
                  value={formData.financials.revenue_ttm || ''}
                  onChange={(e) => updateFinancials('revenue_ttm', e.target.value)}
                  className="w-full pl-7 pr-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="10000000"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Revenue Growth (YoY)</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  value={formData.financials.revenue_growth_yoy || ''}
                  onChange={(e) => updateFinancials('revenue_growth_yoy', e.target.value)}
                  className="w-full pr-20 px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.50"
                />
                <span className="absolute right-3 top-2 text-subtext text-xs">(0.5 = 50%)</span>
              </div>
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Gross Margin</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  value={formData.financials.gross_margin || ''}
                  onChange={(e) => updateFinancials('gross_margin', e.target.value)}
                  className="w-full pr-20 px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.75"
                />
                <span className="absolute right-3 top-2 text-subtext text-xs">(0.75 = 75%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Last Funding Round */}
        <div>
          <h3 className="text-sm font-semibold text-default-font mb-3 flex items-center">
            <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-xs flex items-center justify-center mr-2">3</span>
            Last Funding Round
            <span className="text-xs text-subtext font-normal ml-2">(Required for Last Round method)</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-subtext mb-1">Round Date</label>
              <input
                type="date"
                value={formData.last_round?.date || ''}
                onChange={(e) => updateLastRound('date', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Lead Investor</label>
              <select
                value={formData.last_round?.lead_investor || ''}
                onChange={(e) => updateLastRound('lead_investor', e.target.value)}
                className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select lead investor --</option>
                {LEAD_INVESTORS.map((investor) => (
                  <option key={investor} value={investor}>
                    {investor}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Pre-Money Valuation</label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-subtext">$</span>
                <input
                  type="number"
                  value={formData.last_round?.valuation_pre || ''}
                  onChange={(e) => updateLastRound('valuation_pre', e.target.value)}
                  className="w-full pl-7 pr-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="40000000"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Amount Raised</label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-subtext">$</span>
                <input
                  type="number"
                  value={formData.last_round?.amount_raised || ''}
                  onChange={(e) => updateLastRound('amount_raised', e.target.value)}
                  className="w-full pl-7 pr-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="10000000"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-subtext mb-1">Post-Money Valuation</label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-subtext">$</span>
                <input
                  type="number"
                  value={formData.last_round?.valuation_post || ''}
                  onChange={(e) => updateLastRound('valuation_post', e.target.value)}
                  className="w-full pl-7 pr-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="50000000"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Adjustments */}
        <div>
          <h3 className="text-sm font-semibold text-default-font mb-3 flex items-center">
            <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-600 text-xs flex items-center justify-center mr-2">4</span>
            Company-Specific Adjustments
            <span className="text-xs text-subtext font-normal ml-2">(Optional)</span>
          </h3>

          {formData.adjustments.length > 0 && (
            <div className="space-y-2 mb-4">
              {formData.adjustments.map((adj, index) => {
                const isPositive = parseFloat(adj.factor) >= 1;
                return (
                  <div
                    key={index}
                    className={`flex items-center justify-between p-3 rounded-lg border ${
                      isPositive
                        ? 'bg-success-50 border-success-200'
                        : 'bg-error-50 border-error-200'
                    }`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className={`font-medium ${isPositive ? 'text-success-800' : 'text-error-800'}`}>
                          {adj.name}
                        </span>
                        <span className={`text-sm font-semibold px-2 py-0.5 rounded ${
                          isPositive ? 'bg-success-200 text-success-800' : 'bg-error-200 text-error-800'
                        }`}>
                          {isPositive ? '+' : ''}{((parseFloat(adj.factor) - 1) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className={`text-sm mt-1 ${isPositive ? 'text-success-700' : 'text-error-700'}`}>
                        {adj.reason}
                      </p>
                    </div>
                    <button
                      onClick={() => removeAdjustment(index)}
                      className={`ml-4 p-1 rounded hover:bg-opacity-50 ${
                        isPositive ? 'text-success-600 hover:bg-success-200' : 'text-error-600 hover:bg-error-200'
                      }`}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {availableAdjustments.length > 0 && (
            <div className="flex gap-3">
              <select
                value={selectedAdjustmentId}
                onChange={(e) => setSelectedAdjustmentId(e.target.value)}
                className="flex-1 px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select an adjustment to add --</option>
                {positiveAdjustments.length > 0 && (
                  <optgroup label="Positive Adjustments">
                    {positiveAdjustments.map((preset) => (
                      <option key={preset.id} value={preset.id}>
                        {preset.name} (+{((parseFloat(preset.factor) - 1) * 100).toFixed(0)}%)
                      </option>
                    ))}
                  </optgroup>
                )}
                {negativeAdjustments.length > 0 && (
                  <optgroup label="Negative Adjustments">
                    {negativeAdjustments.map((preset) => (
                      <option key={preset.id} value={preset.id}>
                        {preset.name} ({((parseFloat(preset.factor) - 1) * 100).toFixed(0)}%)
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
              <button
                onClick={addPresetAdjustment}
                disabled={!selectedAdjustmentId}
                className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:bg-neutral-300 disabled:cursor-not-allowed transition-colors"
              >
                Add
              </button>
            </div>
          )}

          {availableAdjustments.length === 0 && formData.adjustments.length > 0 && (
            <p className="text-sm text-subtext italic">All available adjustments have been added.</p>
          )}
        </div>
      </div>

      {/* Process Button */}
      <div className="p-4 border-t border-neutral-border bg-neutral-50">
        <button
          onClick={() => onProcess(formData)}
          disabled={!isValid || loading}
          className="w-full py-3 bg-primary-500 text-white rounded-lg font-semibold hover:bg-primary-600 disabled:bg-neutral-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Processing Valuation...' : 'Process Valuation'}
        </button>
        {!isValid && (
          <p className="text-sm text-red-600 mt-2 text-center">Please enter a company name</p>
        )}
      </div>
    </div>
  );
}
