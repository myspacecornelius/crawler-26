'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import MiniSparkline from '@/components/charts/MiniSparkline';

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  sparklineData?: number[];
  className?: string;
}

const GRADIENT: Record<string, string> = {
  positive: 'from-emerald-400 to-emerald-600',
  negative: 'from-red-400 to-red-600',
  neutral: 'from-brand-400 to-brand-600',
};

const SPARK_COLOR: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#4c6ef5',
};

function useAnimatedNumber(target: number, duration = 800) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number>();

  useEffect(() => {
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplay(Math.round(from + (target - from) * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return display;
}

export default function StatsCard({
  label,
  value,
  icon,
  change,
  changeType = 'neutral',
  sparklineData,
  className = '',
}: StatsCardProps) {
  const numericValue = typeof value === 'number' ? value : parseInt(String(value).replace(/,/g, ''), 10);
  const isNumeric = !isNaN(numericValue);
  const animatedValue = useAnimatedNumber(isNumeric ? numericValue : 0);

  const TrendIcon =
    changeType === 'positive' ? TrendingUp :
    changeType === 'negative' ? TrendingDown : Minus;

  return (
    <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow ${className}`}>
      {/* Top gradient accent */}
      <div className={`h-1 bg-gradient-to-r ${GRADIENT[changeType]}`} />
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-gray-500">{label}</p>
            <p className="text-2xl font-bold mt-1 text-gray-900">
              {isNumeric ? animatedValue.toLocaleString() : value}
            </p>
            {change && (
              <div className="flex items-center gap-1 mt-1">
                <TrendIcon className={`w-3.5 h-3.5 ${
                  changeType === 'positive' ? 'text-emerald-500' :
                  changeType === 'negative' ? 'text-red-500' : 'text-gray-400'
                }`} />
                <p className={`text-xs font-medium ${
                  changeType === 'positive' ? 'text-emerald-600' :
                  changeType === 'negative' ? 'text-red-500' : 'text-gray-500'
                }`}>
                  {change}
                </p>
              </div>
            )}
          </div>
          <div className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center flex-shrink-0">
            {icon}
          </div>
        </div>
      </div>
      {sparklineData && sparklineData.length > 1 && (
        <MiniSparkline data={sparklineData} color={SPARK_COLOR[changeType]} height={30} />
      )}
    </div>
  );
}
