'use client';

import * as React from 'react';
import { Download } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ExportButtonProps<T> {
  data: T[];
  columns: { key: string; label: string }[];
  filename?: string;
  onSuccess?: () => void;
  className?: string;
}

export default function ExportButton<T extends Record<string, unknown>>({
  data,
  columns,
  filename = 'export.csv',
  onSuccess,
  className,
}: ExportButtonProps<T>) {
  const handleExport = () => {
    if (data.length === 0) return;

    const header = columns.map((c) => `"${c.label}"`).join(',');
    const rows = data.map((row) =>
      columns
        .map((c) => {
          const val = row[c.key];
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
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    onSuccess?.();
  };

  return (
    <button
      onClick={handleExport}
      disabled={data.length === 0}
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed',
        className
      )}
    >
      <Download className="h-4 w-4" />
      CSV
    </button>
  );
}
