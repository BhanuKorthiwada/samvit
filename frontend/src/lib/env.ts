import { z } from 'zod'

/**
 * Type-safe environment variable handling with Zod validation.
 * All environment variables are validated at runtime startup.
 */

const envSchema = z.object({
  // API Configuration
  VITE_API_URL: z.string().default('/api/v1'),

  // Feature Flags
  VITE_ENABLE_DEVTOOLS: z
    .string()
    .default('true')
    .transform((v) => v === 'true'),

  // Build mode
  MODE: z.enum(['development', 'production', 'test']).default('development'),

  // Base URL for the app
  BASE_URL: z.string().default('/'),

  // Development mode flag
  DEV: z.boolean().default(true),

  // Production mode flag
  PROD: z.boolean().default(false),
})

type Env = z.infer<typeof envSchema>

function validateEnv(): Env {
  const result = envSchema.safeParse({
    VITE_API_URL: import.meta.env.VITE_API_URL,
    VITE_ENABLE_DEVTOOLS: import.meta.env.VITE_ENABLE_DEVTOOLS,
    MODE: import.meta.env.MODE,
    BASE_URL: import.meta.env.BASE_URL,
    DEV: import.meta.env.DEV,
    PROD: import.meta.env.PROD,
  })

  if (!result.success) {
    console.error('❌ Invalid environment variables:', result.error.format())
    throw new Error('Invalid environment variables')
  }

  return result.data
}

/**
 * Validated environment variables.
 * Use this instead of import.meta.env directly.
 */
export const env = validateEnv()

/**
 * Convenience helpers
 */
export const isDev = env.MODE === 'development'
export const isProd = env.MODE === 'production'
export const isTest = env.MODE === 'test'

/**
 * API base URL for making requests
 */
export const API_URL = env.VITE_API_URL
