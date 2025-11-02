// src/app/dashboard/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface DetectionRecord {
  id: string;
  timestamp: string;
  disease_type: string;
  confidence: number;
  severity: string;
}

interface AnalyticsData {
  recent_detections: DetectionRecord[];
  disease_counts: { [key: string]: number };
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await fetch('http://localhost:5001/analytics');
        if (!response.ok) {
          throw new Error('Failed to fetch analytics data');
        }
        const data = await response.json();
        if (data.status === 'success') {
          setAnalytics(data.data);
        } else {
          throw new Error(data.message || 'Unknown error');
        }
      } catch (err: any) {
        console.error("Failed to fetch analytics:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  // Prepare data for the chart
  const chartData = analytics 
    ? Object.entries(analytics.disease_counts).map(([disease, count]) => ({
        name: disease.replace('_', ' '),
        count: count,
      }))
    : [];

  if (loading) {
    return <p className="p-8">Loading dashboard...</p>;
  }

  if (error) {
    return <p className="p-8 text-red-500">Error: {error}</p>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">SmartFarm Analytics Dashboard</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Disease Detection Count</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p>No detection data available yet.</p>
        )}
      </div>
      
      {/* You can add more widgets here in the future */}
    </div>
  );
}
