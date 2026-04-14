'use client';

import * as React from 'react';
import { cn } from '@/lib/cn';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
  className?: string;
}

export default function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 px-4', className)}>
      <div className="mb-4 text-gray-300">{icon}</div>
      <h3 className="text-base font-semibold text-gray-900 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-500 mb-4 text-center max-w-sm">{description}</p>}
      {action && (
        action.href ? (
          <a
            href={action.href}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-[hsl(var(--primary))] rounded-lg hover:bg-[hsl(var(--primary))]/90 transition-colors"
          >
            {action.label}
          </a>
        ) : (
          <button
            onClick={action.onClick}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-[hsl(var(--primary))] rounded-lg hover:bg-[hsl(var(--primary))]/90 transition-colors"
          >
            {action.label}
          </button>
        )
      )}
    </div>
  );
}
