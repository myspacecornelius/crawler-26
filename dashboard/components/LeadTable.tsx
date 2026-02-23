'use client';

import { useState } from 'react';

interface Lead {
  id: string;
  name: string;
  email: string;
  email_status: 'scraped' | 'guessed' | 'verified' | 'catch_all' | 'undeliverable' | 'unknown';
  linkedin: string;
  fund: string;
  role: string;
  sectors: string;
  score: number;
  tier: string;
}

interface LeadTableProps {
  leads: Lead[];
  total: number;
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  onFilterChange: (filters: Record<string, string>) => void;
}

const emailStatusColors: Record<string, string> = {
  verified: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  scraped: 'bg-blue-100 text-blue-700 border-blue-200',
  guessed: 'bg-amber-100 text-amber-700 border-amber-200',
  catch_all: 'bg-purple-100 text-purple-700 border-purple-200',
  undeliverable: 'bg-red-100 text-red-700 border-red-200',
  unknown: 'bg-gray-100 text-gray-500 border-gray-200',
};

const tierColors: Record<string, string> = {
  HOT: 'bg-red-100 text-red-700 border-red-200',
  WARM: 'bg-amber-100 text-amber-700 border-amber-200',
  COOL: 'bg-blue-100 text-blue-700 border-blue-200',
};

export default function LeadTable({ leads, total, page, perPage, onPageChange, onFilterChange }: LeadTableProps) {
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [hqFilter, setHqFilter] = useState('');
  const [emailStatusFilter, setEmailStatusFilter] = useState('');
  const totalPages = Math.ceil(total / perPage);

  const handleSearch = () => {
    const filters: Record<string, string> = {};
    if (search) filters.search = search;
    if (tierFilter) filters.tier = tierFilter;
    if (stageFilter) filters.stage = stageFilter;
    if (sectorFilter) filters.sector = sectorFilter;
    if (hqFilter) filters.hq = hqFilter;
    if (emailStatusFilter) filters.email_status = emailStatusFilter;
    onFilterChange(filters);
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Search leads..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 max-w-sm px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
        <select
          value={tierFilter}
          onChange={(e) => { setTierFilter(e.target.value); setTimeout(handleSearch, 0); }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Tiers</option>
          <option value="HOT">HOT</option>
          <option value="WARM">WARM</option>
          <option value="COOL">COOL</option>
        </select>
        <select
          value={stageFilter}
          onChange={(e) => { setStageFilter(e.target.value); setTimeout(handleSearch, 0); }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Stages</option>
          <option value="pre-seed">Pre-Seed</option>
          <option value="seed">Seed</option>
          <option value="series-a">Series A</option>
          <option value="series-b">Series B</option>
          <option value="growth">Growth</option>
        </select>
        <input
          type="text"
          placeholder="Sector (e.g. AI, SaaS)"
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="max-w-[160px] px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Geography (e.g. US, NYC)"
          value={hqFilter}
          onChange={(e) => setHqFilter(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="max-w-[160px] px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={emailStatusFilter}
          onChange={(e) => { setEmailStatusFilter(e.target.value); setTimeout(handleSearch, 0); }}
          className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Email Status</option>
          <option value="verified">Verified</option>
          <option value="scraped">Scraped</option>
          <option value="guessed">Guessed</option>
          <option value="catch_all">Catch-All</option>
          <option value="undeliverable">Undeliverable</option>
        </select>
        <button
          onClick={handleSearch}
          className="px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
        >
          Filter
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Role</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Fund</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Score</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Tier</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">LinkedIn</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{lead.name}</td>
                  <td className="px-4 py-3">
                    {lead.email !== 'N/A' ? (
                      <span className="inline-flex items-center gap-1">
                        <a href={`mailto:${lead.email}`} className="text-brand-600 hover:underline">
                          {lead.email}
                        </a>
                        {lead.email_status && lead.email_status !== 'unknown' && (
                          <span className={`ml-1.5 inline-block px-1.5 py-0.5 text-[10px] font-medium rounded border ${emailStatusColors[lead.email_status] || emailStatusColors.unknown}`}>
                            {lead.email_status}
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{lead.role !== 'N/A' ? lead.role : '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{lead.fund}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full"
                          style={{ width: `${Math.min(lead.score, 100)}%` }}
                        />
                      </div>
                      <span className="text-gray-500 text-xs">{lead.score}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full border ${tierColors[lead.tier] || tierColors.COOL}`}>
                      {lead.tier}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {lead.linkedin !== 'N/A' ? (
                      <a
                        href={lead.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-600 hover:underline text-xs"
                      >
                        Profile →
                      </a>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {leads.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-gray-400">
                    No leads found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
            <p className="text-sm text-gray-500">
              Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, total)} of {total}
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Prev
              </button>
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
