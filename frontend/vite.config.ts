import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://localhost:8007'

  return {
    plugins: [react()],
    server: {
      allowedHosts: [
        'localhost',
        '.trycloudflare.com'  // Permite todos los subdominios de trycloudflare.com
      ],      
      proxy: {
        '/api': proxyTarget,
        '/media': proxyTarget,
      },
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      globals: true,
    },
  }
})
