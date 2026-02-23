'use client';

import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from 'recharts';

interface OutreachStatsData {
  total_leads?: number;
  emails_sent?: number;
  opens?: number;
  open_rate?: number;
  replies?: number;
  reply_rate?: number;
  bounces?: number;
  clicks?: number;
}

interface OutreachStatsChartProps {
  records: { name: string; provider_campaign_id: string }[];
  statsMap: Record<string, OutreachStatsData>;
}

export default function OutreachStatsChart({ records, statsMap }: OutreachStatsChartProps) {
  if (records.length === 0) return null;

  const data = records.slice(0, 6).map((rec) => {
    const s = statsMap[rec.provider_campaign_id] || {};
    return {
      name: rec.name.length > 16 ? rec.name.slice(0, 16) + '...' : rec.name,
      sent: s.emails_sent ?? 0,
      opens: s.opens ?? 0,
      replies: s.replies ?? 0,
    };
  });

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Outreach Performance</h3>
      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barCategoryGap="20%">
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
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
            />
            <Bar dataKey="sent" fill="#94a3b8" radius={[4, 4, 0, 0]} name="Sent" />
            <Bar dataKey="opens" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Opens" />
            <Bar dataKey="replies" fill="#10b981" radius={[4, 4, 0, 0]} name="Replies" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
