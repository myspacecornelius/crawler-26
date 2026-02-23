'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface FundRow {
  fund: string;
  contacts: number;
  quality: number; // 0–1 extraction quality score
}

interface FundCoverageBarProps {
  data?: FundRow[];
}

const DEFAULT_DATA: FundRow[] = [
  { fund: 'Sequoia Capital', contacts: 142, quality: 0.9 },
  { fund: 'Andreessen Horowitz', contacts: 128, quality: 0.85 },
  { fund: 'Lightspeed Venture', contacts: 96, quality: 0.8 },
  { fund: 'Accel Partners', contacts: 87, quality: 0.75 },
  { fund: 'Benchmark Capital', contacts: 76, quality: 0.7 },
  { fund: 'Greylock Partners', contacts: 68, quality: 0.65 },
  { fund: 'Index Ventures', contacts: 61, quality: 0.6 },
  { fund: 'Founders Fund', contacts: 55, quality: 0.55 },
  { fund: 'NEA', contacts: 49, quality: 0.5 },
  { fund: 'General Catalyst', contacts: 44, quality: 0.45 },
];

function qualityColor(q: number): string {
  if (q >= 0.8) return '#10b981';
  if (q >= 0.6) return '#f59e0b';
  return '#ef4444';
}

export default function FundCoverageBar({ data }: FundCoverageBarProps) {
  const rows = data ?? DEFAULT_DATA;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Top Funds by Coverage</h3>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="fund"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
              width={130}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                fontSize: 12,
              }}
              formatter={((value: number) => [`${value} contacts`, 'Contacts']) as never}
            />
            <Bar dataKey="contacts" radius={[0, 4, 4, 0]} barSize={18}>
              {rows.map((entry, index) => (
                <Cell key={`bar-${index}`} fill={qualityColor(entry.quality)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
