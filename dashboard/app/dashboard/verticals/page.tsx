'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { listVerticals } from '@/lib/api';

interface Vertical {
  slug: string;
  name: string;
  description: string;
  seed_count: number;
  search_queries: string[];
}

const verticalIcons: Record<string, string> = {
  vc: '🚀',
  pe: '🏦',
  family_office: '🏛️',
  corp_dev: '🏢',
};

export default function VerticalsPage() {
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listVerticals()
      .then(setVerticals)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="animate-pulse text-gray-400 py-12 text-center">Loading verticals...</div>;
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Verticals</h1>
        <p className="text-sm text-gray-500 mt-1">Industry verticals available for lead generation</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {verticals.map((v) => (
          <div key={v.slug} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start gap-4">
              <div className="text-3xl">{verticalIcons[v.slug] || '📊'}</div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900">{v.name}</h2>
                <p className="text-sm text-gray-500 mt-1">{v.description}</p>
                <div className="mt-4 flex items-center gap-4">
                  <div className="text-sm">
                    <span className="font-semibold text-brand-600">{v.seed_count}</span>
                    <span className="text-gray-500 ml-1">firms in database</span>
                  </div>
                </div>
                {v.search_queries.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-gray-400 mb-1.5">Sample queries:</p>
                    <div className="flex flex-wrap gap-1.5">
                      {v.search_queries.slice(0, 3).map((q, i) => (
                        <span key={i} className="inline-block px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600 truncate max-w-[200px]">
                          {q}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                <Link
                  href={`/dashboard/campaigns/new?vertical=${v.slug}`}
                  className="inline-block mt-4 px-4 py-2 text-sm font-medium text-brand-600 border border-brand-200 rounded-lg hover:bg-brand-50 transition-colors"
                >
                  Create Campaign →
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
