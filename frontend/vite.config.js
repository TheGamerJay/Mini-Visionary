import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: process.env.NODE_ENV === 'production' ? '/static/' : '/',  // Use /static/ for production, / for dev
  build: {
    outDir: '../backend/static',     // write build straight into Flask's static/
    assetsDir: 'assets',             // folder inside static/
    emptyOutDir: true,               // wipe old hashed assets each build
    sourcemap: false,                // disable source maps in production
  },
  server: {
    port: 5173,                      // dev server (unchanged)
  }
})