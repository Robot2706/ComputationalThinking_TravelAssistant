import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5173,
    open: '/index.html'
  },
  build: {
    outDir: 'dist',
    minify: 'terser'
  }
})
