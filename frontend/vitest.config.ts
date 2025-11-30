import { URL, fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [viteReact()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    // Test file patterns
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['**/node_modules/**', '**/dist/**'],

    // Environment - jsdom for React components
    environment: 'jsdom',
    globals: true,

    // Setup files for test utilities
    setupFiles: ['./src/test/setup.ts'],

    // Execution
    pool: 'forks',
    fileParallelism: true,
    testTimeout: 10000,

    // Mocking behavior - reset state between tests
    clearMocks: true,
    restoreMocks: true,

    // Coverage configuration
    coverage: {
      provider: 'v8',
      enabled: false,
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.{test,spec}.{ts,tsx}',
        'src/test/**',
        'src/routeTree.gen.ts',
        'src/main.tsx',
      ],
    },
  },
})
