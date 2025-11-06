// frontend/src/app/swarm/page.tsx
'use client';

import { useState, useEffect } from 'react';
import io, { Socket } from 'socket.io-client';

// --- Definisi Tipe Data (tetap sama) ---
interface Drone { id: string; name: string; status: string; battery_level: number; }
interface Zone { id: string; name: string; status: string; drone?: Drone; }
interface Task { id: string; status: string; drone: Drone; zone: Zone; created_at: string; }

export default function SwarmPage() {
  const [drones, setDrones] = useState<Drone[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Inisialisasi Socket.IO
    const socket: Socket = io('http://localhost:5001');

    socket.on('connect', () => {
      console.log('Connected to swarm server!');
    });

    // Dengarkan event 'swarm_update' dari backend
    socket.on('swarm_update', (data: any) => {
      console.log('Received swarm update:', data.message);
      // Tambahkan log ke state
      setLogs(prevLogs => [data.message, ...prevLogs.slice(0, 4)]); // Simpan 5 log terbaru
      
      // Fetch ulang data untuk mendapatkan status terbaru
      fetchData(); 
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from swarm server.');
    });

    // Fungsi untuk mengambil data
    const fetchData = async () => {
      try {
        const [dronesRes, zonesRes, tasksRes] = await Promise.all([
          fetch('http://localhost:5001/api/drones'),
          fetch('http://localhost:5001/api/zones'),
          fetch('http://localhost:5001/api/tasks'),
        ]);

        if (!dronesRes.ok || !zonesRes.ok || !tasksRes.ok) {
          throw new Error('One or more API requests failed');
        }

        const dronesData = await dronesRes.json();
        const zonesData = await zonesRes.json();
        const tasksData = await tasksRes.json();

        setDrones(dronesData);
        setZones(zonesData);
        setTasks(tasksData);
      } catch (error) {
        console.error("Failed to fetch swarm data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    // Ambil data pertama kali
    fetchData();

    // Cleanup saat komponen tidak lagi digunakan (penting!)
    return () => {
      socket.disconnect();
    };
  }, []); // [] agar efek hanya berjalan sekali saat komponen dimuat

  // Fungsi helper untuk menentukan warna status
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'IDLE':
      case 'COMPLETED':
        return 'bg-green-200 text-green-800';
      case 'ASSIGNED':
      case 'IN_PROGRESS':
      case 'FLYING':
        return 'bg-yellow-200 text-yellow-800';
      case 'UNASSIGNED':
        return 'bg-red-200 text-red-800';
      default:
        return 'bg-gray-200 text-gray-800';
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading swarm data...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Swarm Intelligence Dashboard</h1>
      
      {/* Tambahkan bagian untuk Real-time Logs */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-2">Real-time Activity Log</h2>
        <ul className="space-y-1 text-sm text-blue-800">
          {logs.length === 0 ? <li>Waiting for activity...</li> : logs.map((log, index) => <li key={index}>• {log}</li>)}
        </ul>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Drone Status */}
        <div className="p-4 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-3">Drone Status</h2>
          <ul className="space-y-2">
            {drones.map(drone => (
              <li key={drone.id} className="flex justify-between items-center p-2 border rounded">
                <span>{drone.name}</span>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusColor(drone.status)}`}>{drone.status}</span>
                  <p className="text-xs text-gray-600 mt-1">Battery: {drone.battery_level}%</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Zone Status */}
        <div className="p-4 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-3">Zone Status</h2>
          <ul className="space-y-2">
            {zones.map(zone => (
              <li key={zone.id} className="flex justify-between items-center p-2 border rounded">
                <span>{zone.name}</span>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded text-xs font-bold ${getStatusColor(zone.status)}`}>{zone.status}</span>
                  {zone.drone && <p className="text-xs text-gray-600 mt-1">{zone.drone.name}</p>}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Task History */}
        <div className="p-4 bg-white rounded-lg shadow lg:col-span-1">
          <h2 className="text-xl font-semibold mb-3">Recent Tasks</h2>
          <ul className="space-y-2 max-h-64 overflow-y-auto">
            {tasks.slice(0, 5).map(task => (
              <li key={task.id} className="text-sm p-2 border rounded">
                <p className="font-semibold">{task.drone.name} → {task.zone.name}</p>
                <p className="text-gray-600">Status: {task.status}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
