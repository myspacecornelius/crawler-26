'use client';

import { useState, useMemo, useCallback } from 'react';
import { Search, Users } from 'lucide-react';
import { DataTable, ColumnToggle, BulkActions, ExportButton, FilterBar } from '@/components/DataTable';
import { useToast } from '@/components/ui/Toast';
import type { Column } from '@/components/DataTable';

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
  loading?: boolean;
  onPageChange: (page: number) => void;
  onFilterChange: (filters: Record<string, string>) => void;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
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

const allColumns: Column<Lead>[] = [
  {
    key: 'name',
    label: 'Name',
    sortable: true,
    render: (lead) => <span className="font-medium text-gray-900">{lead.name}</span>,
  },
  {
    key: 'email',
    label: 'Email',
    sortable: true,
    render: (lead) =>
      lead.email !== 'N/A' ? (
        <span className="inline-flex items-center gap-1">
          <a href={`mailto:${lead.email}`} className="text-brand-600 hover:underline">
            {lead.email}
          </a>
          {lead.email_status && lead.email_status !== 'unknown' && (
            <span
              className={`ml-1.5 inline-block px-1.5 py-0.5 text-[10px] font-medium rounded border ${emailStatusColors[lead.email_status] || emailStatusColors.unknown}`}
            >
              {lead.email_status}
            </span>
          )}
        </span>
      ) : (
        <span className="text-gray-400">—</span>
      ),
  },
  {
    key: 'role',
    label: 'Role',
    sortable: true,
    render: (lead) => (
      <span className="text-gray-600">{lead.role !== 'N/A' ? lead.role : '—'}</span>
    ),
  },
  {
    key: 'fund',
    label: 'Fund',
    sortable: true,
    render: (lead) => <span className="text-gray-600">{lead.fund}</span>,
  },
  {
    key: 'score',
    label: 'Score',
    sortable: true,
    render: (lead) => (
      <div className="flex items-center gap-2">
        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full"
            style={{ width: `${Math.min(lead.score, 100)}%` }}
          />
        </div>
        <span className="text-gray-500 text-xs">{lead.score}</span>
      </div>
    ),
  },
  {
    key: 'tier',
    label: 'Tier',
    sortable: true,
    render: (lead) => (
      <span
        className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full border ${tierColors[lead.tier] || tierColors.COOL}`}
      >
        {lead.tier}
      </span>
    ),
  },
  {
    key: 'linkedin',
    label: 'LinkedIn',
    render: (lead) =>
      lead.linkedin !== 'N/A' ? (
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
      ),
  },
];

export default function LeadTable({
  leads,
  total,
  page,
  perPage,
  loading = false,
  onPageChange,
  onFilterChange,
  onSort,
  sortKey,
  sortDirection,
}: LeadTableProps) {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [hqFilter, setHqFilter] = useState('');
  const [emailStatusFilter, setEmailStatusFilter] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set(allColumns.map((c) => c.key))
  );

  const activeFilterCount = [tierFilter, stageFilter, sectorFilter, hqFilter, emailStatusFilter].filter(Boolean).length;

  const handleSearch = useCallback(() => {
    const filters: Record<string, string> = {};
    if (search) filters.search = search;
    if (tierFilter) filters.tier = tierFilter;
    if (stageFilter) filters.stage = stageFilter;
    if (sectorFilter) filters.sector = sectorFilter;
    if (hqFilter) filters.hq = hqFilter;
    if (emailStatusFilter) filters.email_status = emailStatusFilter;
    onFilterChange(filters);
  }, [search, tierFilter, stageFilter, sectorFilter, hqFilter, emailStatusFilter, onFilterChange]);

  const clearAllFilters = () => {
    setTierFilter('');
    setStageFilter('');
    setSectorFilter('');
    setHqFilter('');
    setEmailStatusFilter('');
    setSearch('');
    onFilterChange({});
  };

  const exportColumns = useMemo(
    () => allColumns.filter((c) => visibleColumns.has(c.key)).map((c) => ({ key: c.key, label: c.label })),
    [visibleColumns]
  );

  const selectedLeads = useMemo(
    () => leads.filter((l) => selectedIds.has(l.id)),
    [leads, selectedIds]
  );

  const handleExportSelected = () => {
    if (selectedLeads.length === 0) return;
    const header = exportColumns.map((c) => `"${c.label}"`).join(',');
    const rows = selectedLeads.map((row) =>
      exportColumns
        .map((c) => {
          const val = (row as unknown as Record<string, unknown>)[c.key];
          const str = val == null ? '' : String(val);
          return `"${str.replace(/"/g, '""')}"`;
        })
        .join(',')
    );
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads-selected-${selectedLeads.length}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast({ title: 'Export complete', description: `${selectedLeads.length} leads exported`, variant: 'success' });
  };

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search leads..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>
        <FilterBar activeCount={activeFilterCount} onClearAll={clearAllFilters}>
          <select
            value={tierFilter}
            onChange={(e) => { setTierFilter(e.target.value); setTimeout(handleSearch, 0); }}
            aria-label="Filter by tier"
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
          >
            <option value="">All Tiers</option>
            <option value="HOT">HOT</option>
            <option value="WARM">WARM</option>
            <option value="COOL">COOL</option>
          </select>
          <select
            value={stageFilter}
            onChange={(e) => { setStageFilter(e.target.value); setTimeout(handleSearch, 0); }}
            aria-label="Filter by stage"
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
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
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <input
            type="text"
            placeholder="Geography (e.g. US, NYC)"
            value={hqFilter}
            onChange={(e) => setHqFilter(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <select
            value={emailStatusFilter}
            onChange={(e) => { setEmailStatusFilter(e.target.value); setTimeout(handleSearch, 0); }}
            aria-label="Filter by email status"
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
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
            Apply
          </button>
        </FilterBar>
        <ColumnToggle
          columns={allColumns}
          visibleKeys={visibleColumns}
          onChange={setVisibleColumns}
          tableId="leads"
        />
        <ExportButton
          data={leads as unknown as Record<string, unknown>[]}
          columns={exportColumns}
          filename={`leads-page${page}.csv`}
          onSuccess={() => toast({ title: 'CSV exported', variant: 'success' })}
        />
      </div>

      {/* Table */}
      <DataTable<Lead>
        columns={allColumns}
        data={leads}
        total={total}
        page={page}
        perPage={perPage}
        loading={loading}
        selectable
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        onPageChange={onPageChange}
        onSort={onSort}
        sortKey={sortKey}
        sortDirection={sortDirection}
        rowKey={(row) => row.id}
        visibleColumns={visibleColumns}
        emptyMessage="No leads found"
        emptyDescription="Try adjusting your filters or run a new campaign to discover leads."
        emptyIcon={<Users className="h-12 w-12" />}
      />

      {/* Bulk actions */}
      <BulkActions
        count={selectedIds.size}
        onExport={handleExportSelected}
        onPushCRM={() => {
          window.location.href = '/dashboard/crm';
        }}
        onDeselect={() => setSelectedIds(new Set())}
      />
    </div>
  );
}
