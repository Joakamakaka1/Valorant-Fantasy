/**
 * @file schemas.ts
 * @description Zod schemas for runtime validation of API responses.
 *
 * This file provides:
 * 1. Runtime validation of data from the backend
 * 2. Single source of truth for type definitions
 * 3. Automatic type inference for TypeScript
 *
 * Usage:
 * ```typescript
 * import { UserSchema, type User } from '@/lib/schemas';
 *
 * const userData = UserSchema.parse(apiResponse); // Validates at runtime
 * ```
 */

import { z } from "zod";

// ============================================================================
// AUTH & USER SCHEMAS
// ============================================================================

export const UserRoleSchema = z.enum(["user", "admin"]);

export const UserSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  username: z.string(),
  role: UserRoleSchema,
  created_at: z.string().optional(),
});

export const TokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
  user: UserSchema,
});

export const LoginDataSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export const RegisterDataSchema = z.object({
  email: z.string().email(),
  username: z.string().min(3).max(20),
  password: z.string().min(8),
  role: UserRoleSchema.optional(),
});

// ============================================================================
// LEAGUE SCHEMAS
// ============================================================================

export const LeagueStatusSchema = z.enum(["drafting", "active", "finished"]);

export const LeagueSchema = z.object({
  id: z.number(),
  name: z.string(),
  admin_user_id: z.number(),
  invite_code: z.string(),
  created_at: z.string(),
  max_teams: z.number(),
  status: LeagueStatusSchema,
});

export const LeagueMemberSchema = z.object({
  id: z.number(),
  league_id: z.number(),
  user_id: z.number(),
  team_name: z.string(),
  budget: z.number(),
  selected_team_id: z.number().nullable(),
  is_admin: z.boolean(),
  joined_at: z.string(),
  total_points: z.number(),
  team_value: z.number(),
  user: UserSchema.optional(),
  members_league: LeagueSchema.optional(),
});

export const RosterEntrySchema = z.object({
  id: z.number(),
  league_member_id: z.number(),
  player_id: z.number(),
  is_starter: z.boolean(),
  is_bench: z.boolean(),
  role_position: z.string().nullable(),
  total_value_team: z.number(),
});

// ============================================================================
// PROFESSIONAL DATA SCHEMAS
// ============================================================================

export const RegionSchema = z.enum(["EMEA", "Americas", "Pacific", "CN"]);

export const PlayerRoleSchema = z.enum([
  "Duelist",
  "Initiator",
  "Controller",
  "Sentinel",
  "Flex",
]);

export const TeamSchema = z.object({
  id: z.number(),
  name: z.string(),
  region: RegionSchema,
  logo_url: z.string().nullable(),
});

export const PlayerBasicSchema = z.object({
  id: z.number(),
  name: z.string(),
  team_id: z.number().optional(),
  role: PlayerRoleSchema,
});

export const PlayerSchema = z.object({
  id: z.number(),
  name: z.string(),
  role: PlayerRoleSchema,
  region: RegionSchema,
  team_id: z.number().nullable(),
  current_price: z.number(),
  base_price: z.number(),
  points: z.number(),
  matches_played: z.number(),
  team: TeamSchema.optional(),
});

export const PriceHistorySchema = z.object({
  id: z.number(),
  player_id: z.number(),
  date: z.string(),
  price: z.number(),
});

// ============================================================================
// MATCH & STATISTICS SCHEMAS
// ============================================================================

export const MatchStatusSchema = z.enum(["upcoming", "live", "completed"]);

export const PlayerMatchStatsSchema = z.object({
  id: z.number(),
  match_id: z.number(),
  player_id: z.number(),
  agent: z.string().nullable(),
  kills: z.number(),
  death: z.number(),
  assists: z.number(),
  acs: z.number(),
  adr: z.number(),
  kast: z.number(),
  hs_percent: z.number(),
  rating: z.number(),
  first_kills: z.number(),
  first_deaths: z.number(),
  clutches_won: z.number(),
  fantasy_points_earned: z.number(),
  player: PlayerSchema.optional(),
});

export const MatchSchema = z.object({
  id: z.number(),
  vlr_match_id: z.string(),
  date: z.string().nullable(),
  status: MatchStatusSchema,
  tournament_name: z.string().nullable(),
  stage: z.string().nullable(),
  vlr_url: z.string().nullable(),
  is_processed: z.boolean(),
  format: z.string().nullable(),
  team_a_id: z.number().nullable(),
  team_b_id: z.number().nullable(),
  score_team_a: z.number(),
  score_team_b: z.number(),
  team_a: TeamSchema.optional(),
  team_b: TeamSchema.optional(),
  player_stats: z.array(PlayerMatchStatsSchema).optional(),
});

// ============================================================================
// DASHBOARD SCHEMAS
// ============================================================================

export const PointsHistoryItemSchema = z.object({
  recorded_at: z.string(),
  total_points: z.number(),
  global_rank: z.number().nullable(),
});

export const DashboardOverviewSchema = z.object({
  total_points: z.number(),
  global_rank: z.string(),
  active_leagues: z.number(),
  available_budget: z.string(),
  points_history: z.array(PointsHistoryItemSchema),
});

// ============================================================================
// API ERROR SCHEMA
// ============================================================================

export const AppErrorSchema = z.object({
  status_code: z.number(),
  error_code: z.string(),
  message: z.string(),
  details: z.any().optional(),
});

// ============================================================================
// INFERRED TYPES (Alternative to manual types.ts)
// ============================================================================

// Export inferred types for use throughout the application
export type UserRole = z.infer<typeof UserRoleSchema>;
export type User = z.infer<typeof UserSchema>;
export type TokenResponse = z.infer<typeof TokenResponseSchema>;
export type LoginData = z.infer<typeof LoginDataSchema>;
export type RegisterData = z.infer<typeof RegisterDataSchema>;

export type LeagueStatus = z.infer<typeof LeagueStatusSchema>;
export type League = z.infer<typeof LeagueSchema>;
export type LeagueMember = z.infer<typeof LeagueMemberSchema>;
export type RosterEntry = z.infer<typeof RosterEntrySchema>;

export type Region = z.infer<typeof RegionSchema>;
export type PlayerRole = z.infer<typeof PlayerRoleSchema>;
export type Team = z.infer<typeof TeamSchema>;
export type PlayerBasic = z.infer<typeof PlayerBasicSchema>;
export type Player = z.infer<typeof PlayerSchema>;
export type PriceHistory = z.infer<typeof PriceHistorySchema>;

export type MatchStatus = z.infer<typeof MatchStatusSchema>;
export type Match = z.infer<typeof MatchSchema>;
export type PlayerMatchStats = z.infer<typeof PlayerMatchStatsSchema>;

export type PointsHistoryItem = z.infer<typeof PointsHistoryItemSchema>;
export type DashboardOverview = z.infer<typeof DashboardOverviewSchema>;
export type AppError = z.infer<typeof AppErrorSchema>;
