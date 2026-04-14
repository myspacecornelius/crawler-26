'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface EmailSegment {
  name: string;
  value: number;
  color: string;
}

interface EmailStatusDonutProps {
  data?: EmailSegment[];
}

const DEFAULT_DATA: EmailSegment[] = [
  { name: 'Verified', value: 312, color: '#10b981' },
  { name: 'Scraped', value: 88, color: '#3b82f6' },
  { name: 'Guessed', value: 2096, color: '#f59e0b' },
  { name: 'Undeliverable', value: 47, color: '#ef4444' },
  { name: 'Unknown', value: 289, color: '#9ca3af' },
];

export default function EmailStatusDonut({ data }: EmailStatusDonutProps) {
  const segments = data ?? DEFAULT_DATA;
  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Email Quality</h3>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={segments}
              cx="50%"
              cy="45%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={2}
              dataKey="value"
              strokeWidth={0}
            >
              {segments.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                fontSize: 12,
              }}
              formatter={((value: number) => [
                `${value.toLocaleString()} (${Math.round((value / total) * 100)}%)`,
              ]) as never}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: 12 }}
              formatter={(value: string) => {
                const seg = segments.find((s) => s.name === value);
                return `${value}: ${seg?.value.toLocaleString() ?? 0}`;
              }}
            />
            {/* Center label */}
            <text
              x="50%"
              y="42%"
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-gray-900"
              style={{ fontSize: 22, fontWeight: 700 }}
            >
              {total.toLocaleString()}
            </text>
            <text
              x="50%"
              y="52%"
              textAnchor="middle"
              dominantBaseline="central"
              className="fill-gray-500"
              style={{ fontSize: 11 }}
            >
              total emails
            </text>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
