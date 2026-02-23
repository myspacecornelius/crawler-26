interface StatsCardProps {
  label: string;
  value: string | number;
  icon: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
}

export default function StatsCard({ label, value, icon, change, changeType = 'neutral' }: StatsCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="text-2xl font-bold mt-1 text-gray-900">{value}</p>
          {change && (
            <p className={`text-xs mt-1 font-medium ${
              changeType === 'positive' ? 'text-emerald-600' :
              changeType === 'negative' ? 'text-red-500' : 'text-gray-500'
            }`}>
              {change}
            </p>
          )}
        </div>
        <span className="text-2xl">{icon}</span>
      </div>
    </div>
  );
}
