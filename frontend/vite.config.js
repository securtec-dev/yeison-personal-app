import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE || '/',
  server: {
    port: 5173,
    proxy: { '/api': 'http://backend:8000', '/media': 'http://backend:8000' }
  }
})
