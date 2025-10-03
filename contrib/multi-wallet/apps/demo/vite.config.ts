import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  root: __dirname,                          // <-- kunci root ke apps/demo
  plugins: [react()],
  server: {
    host: true,
    port: 4321,
    strictPort: true,
    fs: { allow: [path.resolve(__dirname, '..', '..')] } // boleh akses repo root
  },
  resolve: { preserveSymlinks: true }
})
