'use client';

import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { getFundPortfolio } from '@/lib/api';

interface PortfolioCompany {
  id: string;
  company_name: string;
  fund_name: string;
  sector: string;
  stage: string;
  url: string;
  year?: number;
  scraped_at: string;
}

interface PortfolioResponse {
  fund_name: string;
  companies: PortfolioCompany[];
  total: number;
}

const SECTOR_COLORS: Record<string, string> = {
  ai: 'bg-purple-100 text-purple-700',
  'artificial intelligence': 'bg-purple-100 text-purple-700',
  'machine learning': 'bg-purple-100 text-purple-700',
  saas: 'bg-blue-100 text-blue-700',
  software: 'bg-blue-100 text-blue-700',
  fintech: 'bg-emerald-100 text-emerald-700',
  finance: 'bg-emerald-100 text-emerald-700',
  health: 'bg-red-100 text-red-700',
  healthcare: 'bg-red-100 text-red-700',
  biotech: 'bg-red-100 text-red-700',
  crypto: 'bg-amber-100 text-amber-700',
  web3: 'bg-amber-100 text-amber-700',
  blockchain: 'bg-amber-100 text-amber-700',
  ecommerce: 'bg-pink-100 text-pink-700',
  'e-commerce': 'bg-pink-100 text-pink-700',
  consumer: 'bg-pink-100 text-pink-700',
  security: 'bg-slate-100 text-slate-700',
  cybersecurity: 'bg-slate-100 text-slate-700',
  devtools: 'bg-indigo-100 text-indigo-700',
  infrastructure: 'bg-indigo-100 text-indigo-700',
  education: 'bg-teal-100 text-teal-700',
  edtech: 'bg-teal-100 text-teal-700',
  climate: 'bg-green-100 text-green-700',
  cleantech: 'bg-green-100 text-green-700',
};

function getSectorColor(sector: string): string {
  const key = sector.toLowerCase();
  return SECTOR_COLORS[key] || 'bg-gray-100 text-gray-700';
}

const SUGGESTED_FUNDS = ['Sequoia Capital', 'a16z', 'Benchmark', 'Accel', 'Greylock Partners'];

export default function PortfolioPage() {
  const [query, setQuery] = useState('');
  const [fundName, setFundName] = useState('');
  const [companies, setCompanies] = useState<PortfolioCompany[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  // Filters
  const [sectorFilter, setSectorFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [yearMin, setYearMin] = useState('');
  const [yearMax, setYearMax] = useState('');

  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const doSearch = useCallback(async (fund: string, p: number) => {
    if (!fund.trim()) return;
    setLoading(true);
    setError('');
    try {
      const params: Record<string, string> = {
        page: String(p),
        per_page: String(perPage),
      };
      const data: PortfolioResponse = await getFundPortfolio(fund.trim(), params);
      setCompanies(data.companies || []);
      setTotalCount(data.total || 0);
      setFundName(data.fund_name || fund.trim());
      setSearched(true);
      setPage(p);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolio');
      setCompanies([]);
      setTotalCount(0);
      setSearched(true);
    }
    setLoading(false);
  }, [perPage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSectorFilter('');
    setStageFilter('');
    setYearMin('');
    setYearMax('');
    doSearch(query, 1);
  };

  const handleChipClick = (fund: string) => {
    setQuery(fund);
    setSectorFilter('');
    setStageFilter('');
    setYearMin('');
    setYearMax('');
    doSearch(fund, 1);
  };

  // Debounced search on query change
  useEffect(() => {
    if (!query.trim()) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      doSearch(query, 1);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, doSearch]);

  // Derived filter options from results
  const sectors = useMemo(() => {
    const s = new Set<string>();
    companies.forEach((c) => { if (c.sector) s.add(c.sector); });
    return Array.from(s).sort();
  }, [companies]);

  const stages = useMemo(() => {
    const s = new Set<string>();
    companies.forEach((c) => { if (c.stage) s.add(c.stage); });
    return Array.from(s).sort();
  }, [companies]);

  // Client-side filtered results
  const filtered = useMemo(() => {
    return companies.filter((c) => {
      if (sectorFilter && c.sector !== sectorFilter) return false;
      if (stageFilter && c.stage !== stageFilter) return false;
      if (yearMin && c.year && c.year < Number(yearMin)) return false;
      if (yearMax && c.year && c.year > Number(yearMax)) return false;
      return true;
    });
  }, [companies, sectorFilter, stageFilter, yearMin, yearMax]);

  const totalPages = Math.ceil(totalCount / perPage);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Portfolio Explorer</h1>
        <p className="text-sm text-gray-500 mt-1">Search a fund to explore their portfolio companies</p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative max-w-2xl mx-auto">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search fund name (e.g. Sequoia, a16z, Benchmark)..."
            className="w-full px-5 py-4 text-base border border-gray-200 rounded-2xl shadow-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white placeholder-gray-400"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 bg-brand-600 text-white text-sm font-medium rounded-xl hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 max-w-2xl mx-auto">
          {error}
        </div>
      )}

      {/* Empty State */}
      {!searched && !loading && (
        <div className="text-center py-16">
          <div className="text-5xl mb-4">🏢</div>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">Search for a fund to explore their portfolio</h2>
          <p className="text-sm text-gray-400 mb-6">Enter a fund name above to see their portfolio companies</p>
          <div className="flex flex-wrap justify-center gap-2">
            {SUGGESTED_FUNDS.map((fund) => (
              <button
                key={fund}
                onClick={() => handleChipClick(fund)}
                className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-700 hover:bg-brand-50 hover:border-brand-300 hover:text-brand-700 transition-colors shadow-sm"
              >
                {fund}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {searched && !error && (
        <>
          {/* Fund heading + count */}
          <div className="flex items-center gap-3 mb-5">
            <h2 className="text-xl font-bold text-gray-900">{fundName}</h2>
            <span className="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full bg-brand-100 text-brand-700">
              {filtered.length} {filtered.length !== totalCount ? `of ${totalCount}` : ''} companies
            </span>
          </div>

          {/* Filter Bar */}
          {companies.length > 0 && (
            <div className="flex flex-wrap items-center gap-3 mb-6 bg-white border border-gray-200 rounded-xl p-4">
              <div>
                <label htmlFor="sector-filter" className="block text-xs font-medium text-gray-500 mb-1">Sector</label>
                <select
                  id="sector-filter"
                  value={sectorFilter}
                  onChange={(e) => setSectorFilter(e.target.value)}
                  className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All sectors</option>
                  {sectors.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="stage-filter" className="block text-xs font-medium text-gray-500 mb-1">Stage</label>
                <select
                  id="stage-filter"
                  value={stageFilter}
                  onChange={(e) => setStageFilter(e.target.value)}
                  className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                >
                  <option value="">All stages</option>
                  {stages.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Year range</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={yearMin}
                    onChange={(e) => setYearMin(e.target.value)}
                    placeholder="From"
                    className="w-20 px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                  <span className="text-gray-400 text-sm">–</span>
                  <input
                    type="number"
                    value={yearMax}
                    onChange={(e) => setYearMax(e.target.value)}
                    placeholder="To"
                    className="w-20 px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  />
                </div>
              </div>

              {(sectorFilter || stageFilter || yearMin || yearMax) && (
                <button
                  onClick={() => { setSectorFilter(''); setStageFilter(''); setYearMin(''); setYearMax(''); }}
                  className="mt-5 text-xs font-medium text-gray-500 hover:text-gray-700 underline"
                >
                  Clear filters
                </button>
              )}
            </div>
          )}

          {/* Company Grid */}
          {filtered.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {filtered.map((company, idx) => (
                <div
                  key={company.id || `${company.company_name}-${idx}`}
                  className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <h3 className="font-semibold text-gray-900 text-sm leading-tight">{company.company_name}</h3>
                    {company.year && (
                      <span className="text-xs text-gray-400 whitespace-nowrap">{company.year}</span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {company.sector && (
                      <span className={`inline-block px-2.5 py-0.5 text-xs font-medium rounded-full ${getSectorColor(company.sector)}`}>
                        {company.sector}
                      </span>
                    )}
                    {company.stage && (
                      <span className="inline-block px-2.5 py-0.5 text-xs font-medium rounded-full border border-gray-300 text-gray-600">
                        {company.stage}
                      </span>
                    )}
                  </div>

                  {company.url && (
                    <a
                      href={company.url.startsWith('http') ? company.url : `https://${company.url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-medium text-brand-600 hover:text-brand-700"
                    >
                      Visit website →
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400 text-sm">
              {companies.length > 0 ? 'No companies match your filters.' : 'No portfolio companies found for this fund.'}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 mb-8">
              <button
                onClick={() => doSearch(query, page - 1)}
                disabled={page <= 1 || loading}
                className="px-4 py-2 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                ← Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => doSearch(query, page + 1)}
                disabled={page >= totalPages || loading}
                className="px-4 py-2 text-sm font-medium border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {/* Loading overlay for subsequent searches */}
      {loading && searched && (
        <div className="text-center py-12">
          <div className="animate-pulse text-gray-400">Loading portfolio...</div>
        </div>
      )}
    </div>
  );
}
