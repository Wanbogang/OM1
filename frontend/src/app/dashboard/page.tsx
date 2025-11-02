// src/app/dashboard/page.tsx

'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Type definition for the analytics data structure
interface AnalyticsData {
  recent_detections: any[];
  disease_counts: {
    [key: string]: number;
  };
  time_series_data: { date: string; count: number }[]; // <-- NEW TYPE
}

// ... (Komponen SummaryCard dan PredictionWidget tetap sama) ...

const SummaryCard = ({ title, value, bgColor }: { title: string; value: string | number; bgColor: string }) => (
  <div className={`${bgColor} p-6 rounded-lg shadow text-white`}>
    <h3 className="text-lg font-semibold">{title}</h3>
    <p className="text-3xl font-bold mt-2">{value}</p>
  </div>
);

const PredictionWidget = () => {
  const [selectedDisease, setSelectedDisease] = useState<string>('');
  const [prediction, setPrediction] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const knownDiseases = ['leaf_blight', 'fungal_infection', 'pest_damage', 'bacterial_spot'];

  const handlePredict = async () => {
    if (!selectedDisease) return;
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5001/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ disease_type: selectedDisease }),
      });
      const data = await response.json();
      if (response.ok) {
        setPrediction(data.predicted_confidence);
      }
    } catch (error) {
      console.error("Prediction failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Quick Prediction</h3>
      <select
        value={selectedDisease}
        onChange={(e) => setSelectedDisease(e.target.value)}
        className="w-full p-2 border rounded-md mb-4"
      >
        <option value="">Select a disease</option>
        {knownDiseases.map(d => <option key={d} value={d}>{d.replace('_', ' ')}</option>)}
      </select>
      <button
        onClick={handlePredict}
        disabled={isLoading || !selectedDisease}
        className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 disabled:bg-gray-400"
      >
        {isLoading ? 'Predicting...' : 'Predict'}
      </button>
      {prediction !== null && (
        <p className="mt-4 text-center text-lg font-semibold">
          Predicted Confidence: {(prediction * 100).toFixed(2)}%
        </p>
      )}
    </div>
  );
};


export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5001/analytics');
        if (!response.ok) {
          throw new Error('Failed to fetch analytics data');
        }
        const result = await response.json();
        setData(result.data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Prepare data for the bar chart
  const chartData = data
    ? Object.entries(data.disease_counts).map(([disease, count]) => ({
        name: disease.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        count: count,
      }))
    : [];

  if (loading) return <p className="text-center mt-10">Loading dashboard...</p>;
  if (error) return <p className="text-center mt-10 text-red-500">Error: {error}</p>;
  if (!data) return <p className="text-center mt-10">No data available.</p>;

  console.log("Data received by frontend:", data);

  const totalDetections = data.recent_detections.length;
  const mostCommonDisease = Object.keys(data.disease_counts).reduce((a, b) => 
    data.disease_counts[a] > data.disease_counts[b] ? a : b, ''
  ).replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-8">
        Crop Health Monitoring Dashboard - Found {data?.time_series_data?.length || 0} days of data
      </h1
>
      K<h1 className="text-3xl font-bold text-gray-800 mb-8">Crop Health Monitoring Dashboard</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <SummaryCard title="Total Detections" value={totalDetections} bgColor="bg-blue-500" />
        <SummaryCard title="Most Common Disease" value={mostCommonDisease || 'N/A'} bgColor="bg-red-500" />
        <SummaryCard title="Unique Disease Types" value={Object.keys(data.disease_counts).length} bgColor="bg-green-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Bar Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Disease Detection Counts</h2>
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
        </div>

        {/* NEW: Line Chart for Time-Series */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Detection Trend Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.time_series_data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#82ca9d" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Prediction Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 lg:col-start-3">
          <PredictionWidget />
        </div>
      </div>
    </div>
  );
}
