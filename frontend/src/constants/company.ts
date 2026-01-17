/**
 * Company-related Constants
 *
 * Static data for company stages and investor options.
 */

import type { CompanyStage } from '../types';

export interface StageOption {
  value: CompanyStage;
  label: string;
}

export const STAGES: StageOption[] = [
  { value: 'seed', label: 'Seed' },
  { value: 'series_a', label: 'Series A' },
  { value: 'series_b', label: 'Series B' },
  { value: 'series_c', label: 'Series C' },
  { value: 'growth', label: 'Growth' },
];

export const LEAD_INVESTORS = [
  'Sequoia Capital',
  'Andreessen Horowitz',
  'Y Combinator',
  'Accel',
  'Benchmark',
  'Index Ventures',
  'Lightspeed Venture Partners',
  'Greylock Partners',
  'Bessemer Venture Partners',
  'First Round Capital',
  'Founders Fund',
  'Kleiner Perkins',
  'NEA',
  'General Catalyst',
  'Tiger Global',
  'Insight Partners',
  'Other',
] as const;

export type LeadInvestor = (typeof LEAD_INVESTORS)[number];
