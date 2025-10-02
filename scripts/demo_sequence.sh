#!/usr/bin/env bash
set -euo pipefail

echo "== OM1 Gazebo Demo (Milestone-1) =="
echo

echo "[1/3] Version check"
if command -v gazebo >/dev/null 2>&1; then
  gazebo --version || true
  command -v gzserver >/dev/null 2>&1 && gzserver --version || true
else
  docker run --rm osrf/ros:noetic-desktop-full bash -lc 'gazebo --version || true; gzserver --version || true'
fi
echo

echo "[2/3] Deterministic run #1 (seed=12345)"
SEED=12345 ./scripts/gazebo_run_deterministic.sh
echo

echo "[3/3] Deterministic run #2 (seed=12345)"
SEED=12345 ./scripts/gazebo_run_deterministic.sh
echo

echo "[done] Both runs completed with the same fixed seed (12345)."
echo "Quickstart: ./scripts/gazebo_setup.sh ; then SEED=12345 ./scripts/gazebo_run_deterministic.sh"
