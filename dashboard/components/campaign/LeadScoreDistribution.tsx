'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface LeadScoreDistributionProps {
  leads: { score?: number }[];
}

const BUCKETS = [
  { label: '0–20', min: 0, max: 20, color: '#94a3b8' },
  { label: '20–40', min: 20, max: 40, color: '#60a5fa' },
  { label: '40–60', min: 40, max: 60, color: '#f59e0b' },
  { label: '60–80', min: 60, max: 80, color: '#34d399' },
  { label: '80–100', min: 80, max: 101, color: '#10b981' },
];

export default function LeadScoreDistribution({ leads }: LeadScoreDistributionProps) {
  const data = BUCKETS.map((bucket) => ({
    name: bucket.label,
    count: leads.filter((l) => {
      const s = l.score ?? 0;
      return s >= bucket.min && s < bucket.max;
    }).length,
    color: bucket.color,
  }));

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Lead Score Distribution</h3>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barCategoryGap="20%">
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                fontSize: 12,
              }}
              formatter={((value: number | undefined) => [`${(value ?? 0).toLocaleString()} leads`, 'Count']) as never}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
