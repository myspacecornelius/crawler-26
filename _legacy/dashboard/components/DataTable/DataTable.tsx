'use client';

import * as React from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/cn';
import TableSkeleton from './TableSkeleton';
import EmptyState from '@/components/EmptyState';
import { InboxIcon } from 'lucide-react';

/* ── Types ────────────────────────────────────────── */

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  className?: string;
  hidden?: boolean;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  total: number;
  page: number;
  perPage: number;
  loading?: boolean;
  selectable?: boolean;
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  onPageChange: (page: number) => void;
  onPerPageChange?: (perPage: number) => void;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
  emptyMessage?: string;
  emptyDescription?: string;
  emptyIcon?: React.ReactNode;
  emptyAction?: { label: string; href?: string; onClick?: () => void };
  rowKey: (row: T) => string;
  visibleColumns?: Set<string>;
}

/* ── Pagination ───────────────────────────────────── */

function Pagination({
  page,
  totalPages,
  total,
  perPage,
  onPageChange,
  onPerPageChange,
}: {
  page: number;
  totalPages: number;
  total: number;
  perPage: number;
  onPageChange: (p: number) => void;
  onPerPageChange?: (pp: number) => void;
}) {
  const from = (page - 1) * perPage + 1;
  const to = Math.min(page * perPage, total);

  const getPages = (): (number | '...')[] => {
    const pages: (number | '...')[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }
    pages.push(1);
    if (page > 3) pages.push('...');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push('...');
    pages.push(totalPages);
    return pages;
  };

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
      <div className="flex items-center gap-3">
        <p className="text-sm text-gray-500">
          Showing <span className="font-medium text-gray-700">{from.toLocaleString()}</span>–
          <span className="font-medium text-gray-700">{to.toLocaleString()}</span> of{' '}
          <span className="font-medium text-gray-700">{total.toLocaleString()}</span>
        </p>
        {onPerPageChange && (
          <select
            value={perPage}
            onChange={(e) => onPerPageChange(Number(e.target.value))}
            aria-label="Rows per page"
            className="px-2 py-1 text-xs border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            {[20, 50, 100].map((n) => (
              <option key={n} value={n}>
                {n} / page
              </option>
            ))}
          </select>
        )}
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-2.5 py-1 text-sm rounded border border-gray-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          ←
        </button>
        {getPages().map((p, idx) =>
          p === '...' ? (
            <span key={`ellipsis-${idx}`} className="px-1.5 text-sm text-gray-400">
              …
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={cn(
                'min-w-[32px] px-2.5 py-1 text-sm rounded border transition-colors',
                p === page
                  ? 'border-brand-500 bg-brand-50 text-brand-700 font-medium'
                  : 'border-gray-300 hover:bg-white text-gray-600'
              )}
            >
              {p}
            </button>
          )
        )}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-2.5 py-1 text-sm rounded border border-gray-300 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          →
        </button>
      </div>
    </div>
  );
}

/* ── DataTable ────────────────────────────────────── */

export default function DataTable<T>({
  columns,
  data,
  total,
  page,
  perPage,
  loading = false,
  selectable = false,
  selectedIds,
  onSelectionChange,
  onPageChange,
  onPerPageChange,
  onSort,
  sortKey,
  sortDirection,
  emptyMessage = 'No data found',
  emptyDescription,
  emptyIcon,
  emptyAction,
  rowKey,
  visibleColumns,
}: DataTableProps<T>) {
  const totalPages = Math.ceil(total / perPage);

  const visibleCols = columns.filter((col) => {
    if (col.hidden) return false;
    if (visibleColumns && !visibleColumns.has(col.key)) return false;
    return true;
  });

  const allSelected = data.length > 0 && selectedIds != null && data.every((row) => selectedIds.has(rowKey(row)));
  const someSelected = selectedIds != null && selectedIds.size > 0 && !allSelected;

  const handleSelectAll = () => {
    if (!onSelectionChange || !selectedIds) return;
    if (allSelected) {
      const next = new Set(selectedIds);
      data.forEach((row) => next.delete(rowKey(row)));
      onSelectionChange(next);
    } else {
      const next = new Set(selectedIds);
      data.forEach((row) => next.add(rowKey(row)));
      onSelectionChange(next);
    }
  };

  const handleSelectRow = (id: string) => {
    if (!onSelectionChange || !selectedIds) return;
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    onSelectionChange(next);
  };

  const handleSort = (key: string) => {
    if (!onSort) return;
    if (sortKey === key) {
      onSort(key, sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      onSort(key, 'asc');
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {loading ? (
        <TableSkeleton columns={visibleCols.length + (selectable ? 1 : 0)} rows={5} />
      ) : data.length === 0 ? (
        <EmptyState
          icon={emptyIcon || <InboxIcon className="h-12 w-12" />}
          title={emptyMessage}
          description={emptyDescription}
          action={emptyAction}
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 z-10">
                <tr className="bg-gray-50 border-b border-gray-200">
                  {selectable && (
                    <th className="w-10 px-4 py-3">
                      <input
                        type="checkbox"
                        checked={allSelected}
                        ref={(el) => {
                          if (el) el.indeterminate = someSelected;
                        }}
                        onChange={handleSelectAll}
                        aria-label="Select all rows"
                        className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                      />
                    </th>
                  )}
                  {visibleCols.map((col) => (
                    <th
                      key={col.key}
                      className={cn(
                        'text-left px-4 py-3 font-medium text-gray-500',
                        col.sortable && 'cursor-pointer select-none hover:text-gray-700',
                        col.className
                      )}
                      onClick={col.sortable ? () => handleSort(col.key) : undefined}
                    >
                      <span className="inline-flex items-center gap-1">
                        {col.label}
                        {col.sortable && (
                          sortKey === col.key ? (
                            sortDirection === 'asc' ? (
                              <ChevronUp className="h-3.5 w-3.5 text-brand-600" />
                            ) : (
                              <ChevronDown className="h-3.5 w-3.5 text-brand-600" />
                            )
                          ) : (
                            <ChevronsUpDown className="h-3.5 w-3.5 text-gray-300" />
                          )
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((row) => {
                  const id = rowKey(row);
                  const isSelected = selectedIds?.has(id);
                  return (
                    <tr
                      key={id}
                      className={cn(
                        'hover:bg-gray-50 transition-colors',
                        isSelected && 'bg-brand-50/50'
                      )}
                    >
                      {selectable && (
                        <td className="w-10 px-4 py-3">
                          <input
                            type="checkbox"
                            checked={!!isSelected}
                            onChange={() => handleSelectRow(id)}
                            aria-label={`Select row ${id}`}
                            className="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                          />
                        </td>
                      )}
                      {visibleCols.map((col) => (
                        <td key={col.key} className={cn('px-4 py-3', col.className)}>
                          {col.render
                            ? col.render(row)
                            : String((row as never as Record<string, unknown>)[col.key] ?? '')}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <Pagination
              page={page}
              totalPages={totalPages}
              total={total}
              perPage={perPage}
              onPageChange={onPageChange}
              onPerPageChange={onPerPageChange}
            />
          )}
        </>
      )}
    </div>
  );
}
