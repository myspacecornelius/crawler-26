'use client';

import { Mail, Zap } from 'lucide-react';
import { cn } from '@/lib/cn';

interface ProviderCardProps {
  id: string;
  label: string;
  description: string;
  selected: boolean;
  onClick: () => void;
}

const PROVIDER_CONFIG: Record<string, { icon: typeof Mail; accent: string; bgActive: string }> = {
  instantly: {
    icon: Mail,
    accent: 'text-violet-600',
    bgActive: 'border-violet-500 bg-violet-50 ring-1 ring-violet-500',
  },
  smartlead: {
    icon: Zap,
    accent: 'text-amber-600',
    bgActive: 'border-amber-500 bg-amber-50 ring-1 ring-amber-500',
  },
};

export default function ProviderCard({ id, label, description, selected, onClick }: ProviderCardProps) {
  const config = PROVIDER_CONFIG[id] || PROVIDER_CONFIG.instantly;
  const Icon = config.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-start gap-4 p-4 rounded-xl border-2 text-left transition-all w-full',
        selected ? config.bgActive : 'border-gray-200 hover:border-gray-300 bg-white'
      )}
    >
      <div
        className={cn(
          'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
          selected ? config.accent + ' bg-white shadow-sm' : 'text-gray-400 bg-gray-100'
        )}
      >
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="font-medium text-gray-900">{label}</div>
        <div className="text-xs text-gray-500 mt-0.5">{description}</div>
      </div>
    </button>
  );
}
