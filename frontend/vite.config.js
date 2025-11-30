import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 5173,
    proxy: {
      '^/api/.*': {
        // Forward to the IPv4 localhost address where Flask is bound
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        // Strip the /api prefix so backend routes remain as /login, /register, etc.
        rewrite: (path) => path.replace(/^\/api/, ''),
        // Rewrite cookie domain set by the backend to 'localhost' so browser accepts it
        cookieDomainRewrite: 'localhost'
      }
    }
  }
})