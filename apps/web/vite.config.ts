/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // In development the browser talks to Vite, which forwards /api to the FastAPI server (same origin, so cookies just work).
  server: { proxy: { '/api': 'http://localhost:8000' } },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    css: false,
  },
})
