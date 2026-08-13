import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://localhost:8007'
  const usePolling = (process.env.CHOKIDAR_USEPOLLING ?? env.CHOKIDAR_USEPOLLING) === 'true'

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      allowedHosts: [
        'localhost',
        // Deliberately allow Cloudflare Quick Tunnel subdomains for local demos.
        '.trycloudflare.com',
      ],
      proxy: {
        '/api': proxyTarget,
        '/media': proxyTarget,
      },
      watch: usePolling ? { usePolling: true } : undefined,
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      globals: true,
    },
  }
})
