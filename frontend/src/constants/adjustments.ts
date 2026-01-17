/**
 * Valuation Adjustment Presets
 *
 * Pre-defined company-specific adjustments that auditors can apply
 * to modify valuation estimates based on qualitative factors.
 */

export interface AdjustmentPreset {
  id: string;
  name: string;
  factor: string;
  reason: string;
  category: 'positive' | 'negative';
}

export const ADJUSTMENT_PRESETS: AdjustmentPreset[] = [
  // Positive adjustments
  {
    id: 'strong_team',
    name: 'Strong Team',
    factor: '1.05',
    reason: 'Experienced founding team with prior exits',
    category: 'positive',
  },
  {
    id: 'market_leader',
    name: 'Market Leader',
    factor: '1.08',
    reason: 'Leading position in target market segment',
    category: 'positive',
  },
  {
    id: 'enterprise_traction',
    name: 'Enterprise Traction',
    factor: '1.10',
    reason: 'Signed contracts with Fortune 500 customers',
    category: 'positive',
  },
  {
    id: 'strong_retention',
    name: 'Strong Retention',
    factor: '1.06',
    reason: 'Net revenue retention above 120%',
    category: 'positive',
  },
  {
    id: 'proprietary_tech',
    name: 'Proprietary Technology',
    factor: '1.07',
    reason: 'Defensible IP or patents in core technology',
    category: 'positive',
  },
  {
    id: 'network_effects',
    name: 'Network Effects',
    factor: '1.08',
    reason: 'Product benefits from strong network effects',
    category: 'positive',
  },
  {
    id: 'capital_efficient',
    name: 'Capital Efficient',
    factor: '1.05',
    reason: 'Demonstrated ability to grow efficiently',
    category: 'positive',
  },
  {
    id: 'strategic_partnerships',
    name: 'Strategic Partnerships',
    factor: '1.04',
    reason: 'Key partnerships with industry leaders',
    category: 'positive',
  },
  // Negative adjustments
  {
    id: 'key_person_risk',
    name: 'Key Person Risk',
    factor: '0.95',
    reason: 'Heavy dependence on founder or key employee',
    category: 'negative',
  },
  {
    id: 'high_competition',
    name: 'High Competition',
    factor: '0.92',
    reason: 'Intense competition from well-funded players',
    category: 'negative',
  },
  {
    id: 'customer_concentration',
    name: 'Customer Concentration',
    factor: '0.93',
    reason: 'Top 3 customers represent >50% of revenue',
    category: 'negative',
  },
  {
    id: 'regulatory_risk',
    name: 'Regulatory Risk',
    factor: '0.90',
    reason: 'Operates in heavily regulated industry',
    category: 'negative',
  },
  {
    id: 'slow_growth',
    name: 'Slower Growth',
    factor: '0.95',
    reason: 'Growth has decelerated below sector average',
    category: 'negative',
  },
  {
    id: 'high_churn',
    name: 'High Churn',
    factor: '0.92',
    reason: 'Customer churn above industry benchmark',
    category: 'negative',
  },
  {
    id: 'technical_debt',
    name: 'Technical Debt',
    factor: '0.94',
    reason: 'Significant technical debt requiring investment',
    category: 'negative',
  },
  {
    id: 'limited_runway',
    name: 'Limited Runway',
    factor: '0.93',
    reason: 'Less than 12 months of runway remaining',
    category: 'negative',
  },
];
