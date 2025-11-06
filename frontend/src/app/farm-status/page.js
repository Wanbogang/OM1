'use client';

import { useState, useEffect } from 'react';
import Head from 'next/head';

// Fungsi helper untuk memformat timestamp
function formatTimestamp(isoString) {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default function FarmStatusPage() {
  const [sensorData, setSensorData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fungsi untuk mengambil data dari API
    async function fetchData() {
      try {
        const response = await fetch('http://localhost:5001/api/sensors/latest');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSensorData(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []); // [] berarti efek ini hanya berjalan sekali saat komponen dimuat

  return (
    <>
      <Head>
        <title>Farm Status - SmartFarm</title>
        <meta name="description" content="Real-time sensor data from the farm" />
      </Head>

      <main style={{ padding: '2rem' }}>
        <h1>Kondisi Pertanian Real-Time</h1>
        <p>Data terbaru dari sensor yang terpasang di lahan.</p>

        {loading && <p>Memuat data sensor...</p>}
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}

        {!loading && !error && (
          <div style={{ marginTop: '2rem' }}>
            {sensorData.length === 0 ? (
              <p>Belum ada data sensor.</p>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f2f2f2', textAlign: 'left' }}>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>Sensor ID</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>Tipe</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>Nilai</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>Satuan</th>
                    <th style={{ padding: '8px', border: '1px solid #ddd' }}>Waktu</th>
                  </tr>
                </thead>
                <tbody>
                  {sensorData.map((data) => (
                    <tr key={data.id}>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{data.sensorId}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{data.type}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{data.value}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{data.unit}</td>
                      <td style={{ padding: '8px', border: '1px solid #ddd' }}>{formatTimestamp(data.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </main>
    </>
  );
}
