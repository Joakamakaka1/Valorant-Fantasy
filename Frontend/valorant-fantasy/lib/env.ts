/**
 * @file env.ts
 * @description Type-safe environment variables with Zod validation.
 *
 * This ensures that required environment variables are set and have valid values
 * at build time and runtime.
 *
 * Usage:
 * ```typescript
 * import { env } from '@/lib/env';
 *
 * const backendUrl = env.BACKEND_URL;
 * ```
 */

import { z } from "zod";

// Define the schema for environment variables
const envSchema = z.object({
  // Backend configuration
  BACKEND_URL: z
    .string()
    .url()
    .default("http://127.0.0.1:8000/api/v1")
    .describe("Backend API base URL"),

  // Node environment
  NODE_ENV: z
    .enum(["development", "production", "test"])
    .default("development"),

  // Optional: Public environment variables (accessible in browser)
  NEXT_PUBLIC_APP_URL: z
    .string()
    .url()
    .optional()
    .describe("Public URL of the application"),
});

// Parse and validate environment variables
const parseEnv = () => {
  try {
    return envSchema.parse({
      BACKEND_URL: process.env.BACKEND_URL,
      NODE_ENV: process.env.NODE_ENV,
      NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error("❌ Invalid environment variables:");
      console.error(error.issues);
      throw new Error("Invalid environment variables");
    }
    throw error;
  }
};

/**
 * Type-safe environment variables.
 *
 * This object is validated at import time, ensuring that all required
 * environment variables are set with valid values.
 */
export const env = parseEnv();

// Type export for use in other files
export type Env = z.infer<typeof envSchema>;
