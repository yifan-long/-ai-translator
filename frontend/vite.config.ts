import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 让 `@` 指向 src 目录，避免一堆 ../../../
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 跨域代理：前端 localhost:5173 → 后端 127.0.0.1:8000
    // 写 /api/v1 的请求会被代理到 http://127.0.0.1:8000/api/v1
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
