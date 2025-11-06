// frontend/next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // ... (konfigurasi lain yang sudah ada)
};

// --- TAMBAHKAN INI ---
async function headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        {
          key: 'ngrok-skip-browser-warning',
          value: 'true',
        },
        {
          key: 'Service-Worker-Allowed',
          value: 'false',
        },
      ],
    },
  ];
}

// --- GANTI INI ---
module.exports = nextConfig;
