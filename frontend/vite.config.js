import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Локально API крутиться на 8001 (див. README). Префікс /api зрізаємо — так само, як nginx у Docker
const apiTarget = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8001'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Recharts важкий і рідко змінюється — окремий чанк краще кешується
        manualChunks: {
          charts: ['recharts'],
          vendor: ['react', 'react-dom', 'react-router-dom', '@tanstack/react-query'],
        },
      },
    },
  },
  test: {
    environment: 'node',
  },
})
