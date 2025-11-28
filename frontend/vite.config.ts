import { defineConfig } from 'vite'
import { devtools } from '@tanstack/devtools-vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

import { tanstackRouter } from '@tanstack/router-plugin/vite'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    devtools(),
    tanstackRouter({
      target: 'react',
      autoCodeSplitting: true,
    }),
    viteReact(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  // Build optimizations
  build: {
    target: 'es2022',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Explicit vendor chunks
          if (id.includes('node_modules/')) {
            // React core
            if (id.includes('/react-dom/') || id.includes('/react/')) {
              return 'react-vendor'
            }
            // All Radix UI components (wildcard match)
            if (id.includes('/@radix-ui/')) {
              return 'radix-ui'
            }
            // TanStack packages
            if (id.includes('/@tanstack/react-router')) {
              return 'router'
            }
            if (id.includes('/@tanstack/react-query')) {
              return 'query'
            }
            if (id.includes('/@tanstack/react-table')) {
              return 'table'
            }
            // Charts (recharts + d3 dependencies)
            if (id.includes('/recharts/') || id.includes('/d3-')) {
              return 'charts'
            }
            // Forms
            if (id.includes('/react-hook-form/') || id.includes('/@hookform/') || id.includes('/zod/')) {
              return 'forms'
            }
            // AI SDK
            if (id.includes('/ai/') || id.includes('/@ai-sdk/')) {
              return 'ai-sdk'
            }
            // Animations
            if (id.includes('/motion/') || id.includes('/framer-motion/')) {
              return 'animations'
            }
          }
          // Return undefined for default chunking behavior
        },
      },
    },
  },

  // Development server
  server: {
    port: 3010,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  // Preview server (for testing production builds)
  preview: {
    port: 3010,
    strictPort: true,
  },
})
