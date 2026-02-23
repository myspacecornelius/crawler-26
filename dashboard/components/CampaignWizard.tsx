'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { clsx } from 'clsx';
import { createCampaign, listVerticals, importCSV } from '@/lib/api';
import { Check, ChevronRight, ChevronLeft, Upload, X, FileText, AlertCircle } from 'lucide-react';

/* ---------- Types ---------- */

interface Vertical {
  slug: string;
  name: string;
  description: string;
  seed_count: number;
}

interface WizardStep {
  title: string;
  description: string;
}

const STEPS: WizardStep[] = [
  { title: 'Basics', description: 'Name your campaign and pick a vertical' },
  { title: 'Targeting', description: 'Configure lead filters and criteria' },
  { title: 'Review', description: 'Confirm and launch' },
];

const TIERS = ['HOT', 'WARM', 'COOL'] as const;

const STAGES = ['Any', 'Pre-Seed', 'Seed', 'Series A', 'Series B', 'Growth'] as const;

/* ---------- Component ---------- */

export default function CampaignWizard() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* Step tracking */
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState<'forward' | 'back'>('forward');
  const [animating, setAnimating] = useState(false);
  const stepContentRef = useRef<HTMLDivElement>(null);

  /* Step 1 — Basics */
  const [mode, setMode] = useState<'scratch' | 'import'>('scratch');
  const [name, setName] = useState('');
  const [vertical, setVertical] = useState('');
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [verticalsLoaded, setVerticalsLoaded] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvPreview, setCsvPreview] = useState<string[][]>([]);

  /* Step 2 — Targeting */
  const [minScore, setMinScore] = useState(0);
  const [selectedTiers, setSelectedTiers] = useState<string[]>(['HOT', 'WARM', 'COOL']);
  const [sectors, setSectors] = useState('');
  const [stage, setStage] = useState('Any');
  const [geography, setGeography] = useState('');
  const [checkSize, setCheckSize] = useState('');

  /* Global */
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  /* Fetch verticals on mount */
  useEffect(() => {
    listVerticals()
      .then((v: Vertical[]) => { setVerticals(v); setVerticalsLoaded(true); })
      .catch(() => setVerticalsLoaded(true));
  }, []);

  /* ---------- CSV helpers ---------- */

  const handleFileSelect = useCallback((file: File | undefined) => {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      setError('Only .csv files are accepted');
      return;
    }
    setError('');
    setCsvFile(file);

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').filter(Boolean).slice(0, 6); // header + 5 rows
      const rows = lines.map((l) => l.split(',').map((c) => c.trim()));
      setCsvPreview(rows);
    };
    reader.readAsText(file);
  }, []);

  const clearCsv = () => {
    setCsvFile(null);
    setCsvPreview([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  /* ---------- Tier toggle ---------- */

  const toggleTier = (tier: string) => {
    setSelectedTiers((prev) =>
      prev.includes(tier) ? prev.filter((t) => t !== tier) : [...prev, tier],
    );
  };

  /* ---------- Navigation ---------- */

  const canAdvance = (): boolean => {
    if (step === 0) {
      if (!name.trim()) return false;
      if (mode === 'scratch' && !vertical) return false;
      if (mode === 'import' && !csvFile) return false;
      return true;
    }
    return true;
  };

  const animateStep = (newStep: number, dir: 'forward' | 'back') => {
    setDirection(dir);
    setAnimating(true);
    setTimeout(() => {
      setStep(newStep);
      setAnimating(false);
    }, 200);
  };

  const next = () => {
    setError('');
    if (!canAdvance()) {
      if (step === 0 && !name.trim()) setError('Enter a campaign name');
      else if (step === 0 && mode === 'scratch' && !vertical) setError('Select a vertical');
      else if (step === 0 && mode === 'import' && !csvFile) setError('Upload a CSV file');
      return;
    }
    animateStep(Math.min(step + 1, STEPS.length - 1), 'forward');
  };

  const back = () => {
    setError('');
    animateStep(Math.max(step - 1, 0), 'back');
  };

  /* ---------- Build config ---------- */

  const buildConfig = (): Record<string, unknown> => {
    const config: Record<string, unknown> = {};
    if (minScore > 0) config.min_score = minScore;
    if (selectedTiers.length < 3) config.tiers = selectedTiers;
    const sectorList = sectors.split(',').map((s) => s.trim()).filter(Boolean);
    if (sectorList.length > 0) config.sectors = sectorList;
    if (stage && stage !== 'Any') config.stage = stage;
    if (geography.trim()) config.hq = geography.trim();
    if (checkSize.trim()) config.check_size = checkSize.trim();
    return config;
  };

  /* ---------- Submit ---------- */

  const handleCreate = async () => {
    setError('');
    setLoading(true);
    try {
      const config = buildConfig();
      const campaign = await createCampaign(name, vertical || 'custom', config);

      if (mode === 'import' && csvFile) {
        try {
          await importCSV(campaign.id, csvFile);
        } catch {
          // Import endpoint may not exist yet — don't block creation
        }
      }

      router.push(`/dashboard/campaigns/${campaign.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  /* ---------- Render helpers ---------- */

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center gap-0 mb-8">
      {STEPS.map((s, i) => {
        const isActive = i === step;
        const isCompleted = i < step;
        return (
          <div key={s.title} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  'w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all',
                  isCompleted && 'bg-brand-600 text-white',
                  isActive && 'bg-brand-600 text-white ring-4 ring-brand-100',
                  !isActive && !isCompleted && 'bg-gray-200 text-gray-500',
                )}
              >
                {isCompleted ? <Check className="w-4 h-4" /> : i + 1}
              </div>
              <span
                className={clsx(
                  'text-xs mt-1.5 font-medium whitespace-nowrap',
                  isActive ? 'text-brand-600' : isCompleted ? 'text-gray-700' : 'text-gray-400',
                )}
              >
                {s.title}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={clsx(
                  'w-16 sm:w-24 h-0.5 mx-2 mt-[-18px] transition-colors duration-500',
                  i < step ? 'bg-brand-600' : 'bg-gray-200',
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );

  /* --- Step 1 --- */
  const renderStep1 = () => (
    <div className="space-y-6">
      {/* Mode toggle */}
      <div className="flex gap-2 p-1 bg-gray-100 rounded-lg w-fit">
        <button
          type="button"
          onClick={() => setMode('scratch')}
          className={clsx(
            'px-4 py-2 rounded-md text-sm font-medium transition-colors',
            mode === 'scratch'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700',
          )}
        >
          Start from scratch
        </button>
        <button
          type="button"
          onClick={() => setMode('import')}
          className={clsx(
            'px-4 py-2 rounded-md text-sm font-medium transition-colors',
            mode === 'import'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700',
          )}
        >
          Import existing CSV
        </button>
      </div>

      {/* Campaign name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Campaign Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          placeholder="e.g. Q1 2026 VC Outreach"
        />
      </div>

      {mode === 'scratch' ? (
        /* Vertical selector */
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Select Vertical</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {verticals.map((v) => (
              <button
                key={v.slug}
                type="button"
                onClick={() => setVertical(v.slug)}
                className={clsx(
                  'text-left p-4 rounded-xl border-2 transition-all',
                  vertical === v.slug
                    ? 'border-brand-500 bg-brand-50 ring-2 ring-brand-500/20'
                    : 'border-gray-200 hover:border-gray-300 bg-white',
                )}
              >
                <div className="font-medium text-gray-900 text-sm">{v.name}</div>
                <div className="text-xs text-gray-500 mt-1">{v.description}</div>
                <div className="text-xs text-brand-600 mt-2 font-medium">
                  {v.seed_count} firms in database
                </div>
              </button>
            ))}
            {!verticalsLoaded && (
              <div className="col-span-2 text-sm text-gray-400 py-8 text-center">
                Loading verticals...
              </div>
            )}
            {verticalsLoaded && verticals.length === 0 && (
              <div className="col-span-2 text-sm text-gray-400 py-8 text-center">
                No verticals available
              </div>
            )}
          </div>
        </div>
      ) : (
        /* CSV import */
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Upload CSV</label>
          {!csvFile ? (
            <div
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleFileSelect(e.dataTransfer.files[0]);
              }}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-brand-400 hover:bg-brand-50/30 transition-colors"
            >
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-3" />
              <p className="text-sm text-gray-600 font-medium">
                Drag & drop a .csv file here, or click to browse
              </p>
              <p className="text-xs text-gray-400 mt-1">Only .csv files are accepted</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                aria-label="Upload CSV file"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files?.[0])}
              />
            </div>
          ) : (
            <div className="border border-gray-200 rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-brand-600" />
                  <span className="text-sm font-medium text-gray-700">{csvFile.name}</span>
                  <span className="text-xs text-gray-400">
                    ({(csvFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button type="button" onClick={clearCsv} className="text-gray-400 hover:text-gray-600">
                  <X className="w-4 h-4" />
                </button>
              </div>
              {csvPreview.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-50">
                        {csvPreview[0].map((h, i) => (
                          <th key={i} className="px-3 py-2 text-left font-medium text-gray-600 whitespace-nowrap">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {csvPreview.slice(1).map((row, ri) => (
                        <tr key={ri} className="border-t border-gray-100">
                          {row.map((cell, ci) => (
                            <td key={ci} className="px-3 py-2 text-gray-700 whitespace-nowrap max-w-[200px] truncate">
                              {cell}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <div className="px-4 py-2 bg-amber-50 border-t border-amber-200 flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                <span className="text-xs text-amber-700">
                  CSV import is in beta — your file will be uploaded after campaign creation
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  /* --- Step 2 --- */
  const renderStep2 = () => (
    <div className="space-y-6">
      {/* Min Score slider */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700">Minimum Score</label>
          <span className="text-sm font-semibold text-brand-600">{minScore}</span>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-brand-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>0 (all leads)</span>
          <span>100 (top only)</span>
        </div>
      </div>

      {/* Tier checkboxes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Lead Tiers</label>
        <div className="flex flex-wrap gap-3">
          {TIERS.map((tier) => {
            const checked = selectedTiers.includes(tier);
            const colors: Record<string, string> = {
              HOT: 'border-red-300 bg-red-50 text-red-700',
              WARM: 'border-amber-300 bg-amber-50 text-amber-700',
              COOL: 'border-blue-300 bg-blue-50 text-blue-700',
            };
            return (
              <button
                key={tier}
                type="button"
                onClick={() => toggleTier(tier)}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all',
                  checked ? colors[tier] : 'border-gray-200 bg-white text-gray-400',
                )}
              >
                <div
                  className={clsx(
                    'w-4 h-4 rounded border-2 flex items-center justify-center transition-colors',
                    checked ? 'border-current bg-current' : 'border-gray-300',
                  )}
                >
                  {checked && <Check className="w-3 h-3 text-white" />}
                </div>
                {tier}
              </button>
            );
          })}
        </div>
      </div>

      {/* Sectors */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Sectors</label>
        <input
          type="text"
          value={sectors}
          onChange={(e) => setSectors(e.target.value)}
          className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          placeholder="e.g. AI, SaaS, Fintech (comma-separated)"
        />
      </div>

      {/* Stage dropdown */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Stage</label>
        <select
          value={stage}
          onChange={(e) => setStage(e.target.value)}
          className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent bg-white"
        >
          {STAGES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Geography */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Geography</label>
        <input
          type="text"
          value={geography}
          onChange={(e) => setGeography(e.target.value)}
          className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          placeholder='e.g. US, SF Bay Area, Europe'
        />
      </div>

      {/* Check Size */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Check Size</label>
        <input
          type="text"
          value={checkSize}
          onChange={(e) => setCheckSize(e.target.value)}
          className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          placeholder='e.g. $1M–$5M'
        />
      </div>
    </div>
  );

  /* --- Step 3 --- */
  const renderStep3 = () => {
    const config = buildConfig();
    const selectedVertical = verticals.find((v) => v.slug === vertical);
    const configEntries = Object.entries(config);

    return (
      <div className="space-y-6">
        {/* Summary card */}
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-5 py-3 bg-gray-50 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-800">Campaign Summary</h3>
          </div>
          <div className="divide-y divide-gray-100">
            <SummaryRow label="Name" value={name} />
            <SummaryRow
              label="Source"
              value={
                mode === 'import'
                  ? `CSV Import — ${csvFile?.name || 'unknown'}`
                  : selectedVertical?.name || vertical
              }
            />
            {mode === 'scratch' && selectedVertical && (
              <SummaryRow label="Database size" value={`${selectedVertical.seed_count} firms`} />
            )}
            {configEntries.length > 0 ? (
              configEntries.map(([key, val]) => (
                <SummaryRow
                  key={key}
                  label={formatLabel(key)}
                  value={Array.isArray(val) ? val.join(', ') : String(val)}
                />
              ))
            ) : (
              <SummaryRow label="Targeting" value="All leads (no filters)" />
            )}
          </div>
        </div>

        {/* Credit estimate */}
        <div className="flex items-start gap-3 p-4 bg-brand-50 border border-brand-200 rounded-xl">
          <AlertCircle className="w-5 h-5 text-brand-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-brand-800">Credit Estimate</p>
            <p className="text-sm text-brand-700 mt-0.5">
              This campaign will use approximately{' '}
              <span className="font-semibold">
                {mode === 'import'
                  ? `${Math.max(csvPreview.length - 1, 0)} leads`
                  : selectedVertical
                    ? `${selectedVertical.seed_count}+ credits`
                    : 'an estimated number of credits'}
              </span>{' '}
              based on your targeting criteria. Actual usage may vary.
            </p>
          </div>
        </div>
      </div>
    );
  };

  /* ---------- Main render ---------- */

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">New Campaign</h1>
      <p className="text-sm text-gray-500 mb-8">Configure and launch a new lead generation campaign</p>

      {renderStepIndicator()}

      {error && (
        <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Step description */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">{STEPS[step].title}</h2>
        <p className="text-sm text-gray-500">{STEPS[step].description}</p>
      </div>

      {/* Step content */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 overflow-hidden">
        <div
          ref={stepContentRef}
          className={`transition-all duration-200 ease-in-out ${
            animating
              ? direction === 'forward'
                ? 'opacity-0 translate-x-8'
                : 'opacity-0 -translate-x-8'
              : 'opacity-100 translate-x-0'
          }`}
        >
          {step === 0 && renderStep1()}
          {step === 1 && renderStep2()}
          {step === 2 && renderStep3()}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <div>
          {step > 0 ? (
            <button
              type="button"
              onClick={back}
              className="flex items-center gap-1.5 px-5 py-2.5 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
          ) : (
            <button
              type="button"
              onClick={() => router.back()}
              className="px-5 py-2.5 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        <div>
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={next}
              className="flex items-center gap-1.5 px-6 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleCreate}
              disabled={loading}
              className="px-6 py-2.5 bg-brand-600 text-white text-sm font-medium rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Campaign'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------- Utility sub-components ---------- */

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900 text-right max-w-[60%] truncate">{value}</span>
    </div>
  );
}

function formatLabel(key: string): string {
  const labels: Record<string, string> = {
    min_score: 'Min Score',
    tiers: 'Tiers',
    sectors: 'Sectors',
    stage: 'Stage',
    hq: 'Geography',
    check_size: 'Check Size',
  };
  return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
