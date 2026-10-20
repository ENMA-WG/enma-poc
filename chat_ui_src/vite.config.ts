import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // desktop_viewer/server/api_server.py serves this directory as static
    // files at "/"; chat_ui/README.md documents the same contract.
    outDir: '../src/desktop_viewer/chat_ui',
    emptyOutDir: true,
  },
})
