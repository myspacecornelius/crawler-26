'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { motion } from 'framer-motion';
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
  neutral: 'from-brand-600 to-brand-400',
};

const SPARK_COLOR: Record<string, string> = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#f59e0b',
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
    <motion.div
      whileHover={{ y: -5, scale: 1.01 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className={`glass-card hive-border rounded-xl overflow-hidden ${className}`}
    >
      {/* Top gradient accent */}
      <div className={`h-1 bg-gradient-to-r ${GRADIENT[changeType]}`} />
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">{label}</p>
            <p className="text-2xl font-bold mt-1 text-gray-100 drop-shadow-sm">
              {isNumeric ? animatedValue.toLocaleString() : value}
            </p>
            {change && (
              <div className="flex items-center gap-1 mt-1">
                <TrendIcon className={`w-3.5 h-3.5 ${changeType === 'positive' ? 'text-emerald-400' :
                    changeType === 'negative' ? 'text-red-400' : 'text-gray-500'
                  }`} />
                <p className={`text-xs font-medium ${changeType === 'positive' ? 'text-emerald-400' :
                    changeType === 'negative' ? 'text-red-400' : 'text-gray-400'
                  }`}>
                  {change}
                </p>
              </div>
            )}
          </div>
          <motion.div
            whileHover={{ rotate: 15, scale: 1.1 }}
            className="w-10 h-10 rounded-lg bg-brand-500/10 text-brand-500 border border-brand-500/20 flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_-3px_rgba(245,158,11,0.2)]"
          >
            {icon}
          </motion.div>
        </div>
      </div>
      {sparklineData && sparklineData.length > 1 && (
        <div className="px-5 pb-4">
          <MiniSparkline data={sparklineData} color={SPARK_COLOR[changeType]} height={30} />
        </div>
      )}
    </motion.div>
  );
}
