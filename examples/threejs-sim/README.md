# OM1 × Three.js Mini Simulator (PoC)

A minimal Three.js simulator with an HTTP/WS bridge compatible with an OM1-style control loop.

## Bridge (Node/Express + WS)

- **POST** `/action` with body `{ v, w }` → applies motion; returns
  `{ reward, done, info: { steps, collisions, minDist } }`
- **POST** `/reset` → resets the episode
- **WS** `/ws` broadcasts every ~50 ms:
