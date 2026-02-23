'use client';

import * as React from 'react';
import { Download, Send, X } from 'lucide-react';
import { cn } from '@/lib/cn';

interface BulkActionsProps {
  count: number;
  onExport?: () => void;
  onPushCRM?: () => void;
  onDeselect: () => void;
  className?: string;
}

export default function BulkActions({ count, onExport, onPushCRM, onDeselect, className }: BulkActionsProps) {
  if (count === 0) return null;

  return (
    <div
      className={cn(
        'fixed bottom-6 left-1/2 -translate-x-1/2 z-50',
        'flex items-center gap-3 px-5 py-3 bg-gray-900 text-white rounded-xl shadow-2xl',
        'animate-slideUp',
        className
      )}
    >
      <span className="text-sm font-medium whitespace-nowrap">
        {count} {count === 1 ? 'row' : 'rows'} selected
      </span>
      <div className="w-px h-5 bg-gray-700" />
      {onExport && (
        <button
          onClick={onExport}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
        >
          <Download className="h-3.5 w-3.5" />
          Export Selected
        </button>
      )}
      {onPushCRM && (
        <button
          onClick={onPushCRM}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
        >
          <Send className="h-3.5 w-3.5" />
          Push to CRM
        </button>
      )}
      <button
        onClick={onDeselect}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
      >
        <X className="h-3.5 w-3.5" />
        Deselect All
      </button>
    </div>
  );
}
