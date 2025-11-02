// src/app/predict/page.tsx

'use client';

import { useState } from 'react';

export default function PredictPage() {
  const [selectedDisease, setSelectedDisease] = useState<string>('');
  const [prediction, setPrediction] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Daftar penyakit yang kita ketahui ada di model
  // Nanti kita bisa buat ini dinamis dengan mengambil dari API /analytics
  const knownDiseases = [
    'leaf_blight',
    'fungal_infection',
    'pest_damage',
    'bacterial_spot',
  ];

  const handlePredict = async () => {
    if (!selectedDisease) {
      setError('Please select a disease type.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await fetch('http://localhost:5001/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ disease_type: selectedDisease }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      setPrediction(data.predicted_confidence);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">Disease Confidence Predictor</h1>
        
        <div className="mb-4">
          <label htmlFor="disease-select" className="block text-sm font-medium text-gray-700 mb-2">
            Select Disease Type
          </label>
          <select
            id="disease-select"
            value={selectedDisease}
            onChange={(e) => setSelectedDisease(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">-- Choose a disease --</option>
            {knownDiseases.map((disease) => (
              <option key={disease} value={disease}>
                {disease.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handlePredict}
          disabled={isLoading || !selectedDisease}
          className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Predicting...' : 'Predict Confidence'}
        </button>

        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
            Error: {error}
          </div>
        )}

        {prediction !== null && (
          <div className="mt-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded-md">
            <p className="font-semibold">Prediction Result:</p>
            <p className="text-lg">
              Predicted Confidence for <strong>{selectedDisease.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</strong> is:
            </p>
            <p className="text-2xl font-bold">{(prediction * 100).toFixed(2)}%</p>
          </div>
        )}
      </div>
    </div>
  );
}
