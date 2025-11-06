-- CreateTable
CREATE TABLE "drones" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'IDLE',
    "last_heartbeat" DATETIME,
    "battery_level" REAL,
    "assigned_at" DATETIME
);

-- CreateTable
CREATE TABLE "zones" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "bounds" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'UNASSIGNED',
    "priority_score" REAL NOT NULL DEFAULT 1.0,
    "completed_at" DATETIME
);

-- CreateTable
CREATE TABLE "tasks" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "drone_id" TEXT NOT NULL,
    "zone_id" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'ASSIGNED',
    "assigned_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "started_at" DATETIME,
    "completed_at" DATETIME,
    CONSTRAINT "tasks_drone_id_fkey" FOREIGN KEY ("drone_id") REFERENCES "drones" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "tasks_zone_id_fkey" FOREIGN KEY ("zone_id") REFERENCES "zones" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "formations" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "drone_positions" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT false
);

-- CreateTable
CREATE TABLE "formation_drones" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "drone_id" TEXT NOT NULL,
    "formation_id" TEXT NOT NULL,
    "assigned_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "formation_drones_drone_id_fkey" FOREIGN KEY ("drone_id") REFERENCES "drones" ("id") ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT "formation_drones_formation_id_fkey" FOREIGN KEY ("formation_id") REFERENCES "formations" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "detection_records" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "timestamp" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "image_path" TEXT NOT NULL,
    "disease_type" TEXT NOT NULL,
    "confidence" REAL NOT NULL,
    "coordinates" TEXT NOT NULL,
    "severity" TEXT NOT NULL,
    "latitude" REAL,
    "longitude" REAL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
