'use client';

import { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface DataPoint {
  date: string;
  verified: number;
  guessed: number;
}

interface LeadsOverTimeChartProps {
  data?: DataPoint[];
}

const RANGES = ['7d', '30d', '90d', 'All'] as const;

function generateMockData(): DataPoint[] {
  const points: DataPoint[] = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    points.push({
      date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      verified: Math.floor(Math.random() * 80 + 20),
      guessed: Math.floor(Math.random() * 150 + 50),
    });
  }
  return points;
}

export default function LeadsOverTimeChart({ data }: LeadsOverTimeChartProps) {
  const [range, setRange] = useState<(typeof RANGES)[number]>('30d');
  const chartData = data ?? generateMockData();

  const filteredData = (() => {
    if (range === '7d') return chartData.slice(-7);
    if (range === '30d') return chartData.slice(-30);
    if (range === '90d') return chartData.slice(-90);
    return chartData;
  })();

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Leads Generated</h3>
        <div className="flex gap-1">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                range === r
                  ? 'bg-brand-100 text-brand-700'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={filteredData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gradVerified" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="gradGuessed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#9ca3af' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                fontSize: 12,
              }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
            />
            <Area
              type="monotone"
              dataKey="verified"
              name="Verified"
              stackId="1"
              stroke="#10b981"
              strokeWidth={2}
              fill="url(#gradVerified)"
            />
            <Area
              type="monotone"
              dataKey="guessed"
              name="Guessed"
              stackId="1"
              stroke="#f59e0b"
              strokeWidth={2}
              fill="url(#gradGuessed)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
