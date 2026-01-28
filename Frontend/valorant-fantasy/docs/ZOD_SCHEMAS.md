# How to Use Zod Schemas for Runtime Validation

## Overview

The `lib/schemas.ts` file provides Zod schemas for runtime validation of API responses. This gives you:

1. **Type Safety**: Infer TypeScript types from schemas
2. **Runtime Validation**: Validate data at runtime to catch API contract violations
3. **Single Source of Truth**: Types and validation rules in one place

---

## Basic Usage

### 1. Import Schema and Type

```typescript
import { UserSchema, type User } from "@/lib/schemas";
```

### 2. Validate Data

```typescript
// Parse and validate (throws if invalid)
const user = UserSchema.parse(apiResponse);

// Safe parse (returns result object)
const result = UserSchema.safeParse(apiResponse);
if (result.success) {
  const user = result.data;
} else {
  console.error(result.error);
}
```

---

## Integration Examples

### Example 1: Validating API Responses

```typescript
// lib/api.ts
import { UserSchema, LeagueSchema } from "@/lib/schemas";

export const authApi = {
  getMe: async (): Promise<User> => {
    const response = await api.get("/auth/me");

    // Validate response at runtime
    return UserSchema.parse(response);
  },
};

export const leaguesApi = {
  getAll: async (): Promise<League[]> => {
    const response = await api.get("/leagues");

    // Validate array of leagues
    return z.array(LeagueSchema).parse(response);
  },
};
```

### Example 2: Form Validation (Already Implemented)

```typescript
// components/auth/register-form.tsx
import { z } from "zod";

const registerSchema = z.object({
  email: z.string().email("Invalid email format"),
  username: z.string().min(3).max(20),
  password: z.string().min(8),
});

// TypeScript type inferred from schema
type RegisterFormValues = z.infer<typeof registerSchema>;
```

### Example 3: Server Actions with Validation

```typescript
// lib/actions/league-actions.ts
"use server";

import { LeagueSchema } from "@/lib/schemas";

export async function createLeague(name: string, maxTeams: number) {
  const response = await fetch(`${API_URL}/leagues`, {
    method: "POST",
    body: JSON.stringify({ name, max_teams: maxTeams }),
  });

  const data = await response.json();

  // Validate before returning
  return LeagueSchema.parse(data);
}
```

---

## Benefits

### ✅ Catch API Contract Violations Early

```typescript
// If backend changes User.email to User.emailAddress,
// Zod will throw an error immediately instead of causing
// silent bugs in production
const user = UserSchema.parse(apiResponse); // ❌ Throws clear error
```

### ✅ Type Inference

```typescript
// No need for manual type definitions
export type User = z.infer<typeof UserSchema>;
export type League = z.infer<typeof LeagueSchema>;
```

### ✅ Safe Optional Chaining

```typescript
const team = player.team?.name; // TypeScript knows this is safe
```

---

## Migration Strategy (Optional)

If you want to gradually add validation to existing API calls:

### Step 1: Start with Critical Endpoints

```typescript
// Validate auth endpoints first (highest priority)
authApi.getMe(); // Add UserSchema.parse()
authApi.login(); // Add TokenResponseSchema.parse()
```

### Step 2: Add to New Features

All new API calls should use schema validation from the start.

### Step 3: Add to Existing Code Gradually

When you modify existing API calls, add validation at that time.

---

## Production Considerations

### Performance

Zod validation is fast, but you can skip it in production if needed:

```typescript
const shouldValidate = process.env.NODE_ENV === "development";

const user = shouldValidate
  ? UserSchema.parse(apiResponse)
  : (apiResponse as User);
```

### Error Handling

```typescript
try {
  const user = UserSchema.parse(apiResponse);
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error("API validation failed:", error.errors);
    // Handle validation error (show user-friendly message)
  }
}
```

---

## Current Status

✅ All schemas defined in `lib/schemas.ts`  
✅ Form validation using Zod (login, register)  
⚠️ API response validation: **Optional** (not yet implemented)

**Recommendation**: Start adding API validation when you notice backend changes causing bugs, or during major refactors.
