export interface Drone {
  id: string;
  name: string;
  status: 'IDLE' | 'ASSIGNED' | 'FLYING' | 'MAINTENANCE';
  battery: number;
  position: { lat: number; lng: number };
  currentMission?: string;
  lastUpdate: Date;
}

export interface Zone {
  id: string;
  name: string;
  status: 'UNASSIGNED' | 'IN_PROGRESS' | 'COMPLETED';
  coordinates: { lat: number; lng: number }[];
  area: number;
  detectedDiseases: string[];
  assignedDrones: string[];
  progress: number;
}

export interface Mission {
  id: string;
  droneId: string;
  zoneId: string;
  startTime: Date;
  endTime: Date;
  status: 'COMPLETED' | 'FAILED' | 'CANCELLED';
  diseaseFound: string[];
  areaCovered: number;
  sprayTime: number;
}

export interface SwarmStats {
  totalDrones: number;
  activeDrones: number;
  missionsToday: number;
  completedZones: number;
  totalCoverage: number;
  averageEfficiency: number;
}
