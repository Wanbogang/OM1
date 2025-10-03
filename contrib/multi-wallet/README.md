# Multi-Wallet (WalletConnect v2 + MetaMask)

This contribution adds a modular wallet adapter interface and two providers:
- WalletConnect v2 (QR flow)
- MetaMask (browser extension, EIP-1193)

A small demo app shows Connect → Sign → Send Tx on Sepolia.

Demo videos:
- WalletConnect: https://youtu.be/cYVlOdt4F2s
- MetaMask: https://youtu.be/3_D-PE3ZYBk

Quick start (demo):
1) Copy env: apps/demo/.env.example → apps/demo/.env, fill VITE_WC_PROJECT_ID.
2) Run dev server from apps/demo: `npx vite --host 0.0.0.0 --port 4321`
3) Open http://localhost:4321 (via SSH tunnel if remote).
