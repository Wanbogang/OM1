'use client';

import { SwarmStats as SwarmStatsType } from '@/types/swarm';

interface SwarmStatsProps {
  stats: SwarmStatsType;
}

export default function SwarmStats({ stats }: SwarmStatsProps) {
  const statCards = [
    {
      title: 'Total Drones',
      value: stats.totalDrones.toString(),
      icon: '🚁',
      color: 'bg-blue-50 border-blue-200',
      textColor: 'text-blue-700'
    },
    {
      title: 'Active Drones',
      value: stats.activeDrones.toString(),
      icon: '🟢',
      color: 'bg-green-50 border-green-200',
      textColor: 'text-green-700'
    },
    {
      title: 'Missions Today',
      value: stats.missionsToday.toString(),
      icon: '📋',
      color: 'bg-purple-50 border-purple-200',
      textColor: 'text-purple-700'
    },
    {
      title: 'Completed Zones',
      value: stats.completedZones.toString(),
      icon: '✅',
      color: 'bg-emerald-50 border-emerald-200',
      textColor: 'text-emerald-700'
    },
    {
      title: 'Total Coverage (ha)',
      value: stats.totalCoverage.toFixed(1),
      icon: '🌾',
      color: 'bg-amber-50 border-amber-200',
      textColor: 'text-amber-700'
    },
    {
      title: 'Avg Efficiency',
      value: `${stats.averageEfficiency}%`,
      icon: '📊',
      color: 'bg-indigo-50 border-indigo-200',
      textColor: 'text-indigo-700'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      {statCards.map((card, index) => (
        <div
          key={index}
          className={`border-2 rounded-lg p-4 ${card.color} transition-all duration-200 hover:shadow-md`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className={`text-2xl font-bold ${card.textColor} mt-1`}>
                {card.value}
              </p>
            </div>
            <span className="text-2xl">{card.icon}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
