/**
 * @file types.ts
 * @description Core TypeScript interfaces mirroring the Backend schemas.
 * Used for type-safe API communication and state management.
 */

// ============================================================================
// AUTH & USER TYPES
// ============================================================================

export type UserRole = "user" | "admin";

export interface User {
  id: number;
  email: string;
  username: string;
  role: UserRole;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  role?: UserRole;
}

// ============================================================================
// LEAGUE TYPES
// ============================================================================

export type LeagueStatus = "drafting" | "active" | "finished";

export interface League {
  id: number;
  name: string;
  admin_user_id: number;
  invite_code: string;
  created_at: string;
  max_teams: number;
  status: LeagueStatus;
}

export interface LeagueMember {
  id: number;
  league_id: number;
  user_id: number;
  team_name: string;
  budget: number;
  selected_team_id: number | null;
  is_admin: boolean;
  joined_at: string;
  total_points: number;
  team_value: number;
  user?: User;
  members_league?: League;
}

export interface RosterEntry {
  id: number;
  league_member_id: number;
  player_id: number;
  is_starter: boolean;
  is_bench: boolean;
  role_position: string | null;
  total_value_team: number;
}

// ============================================================================
// PROFESSIONAL DATA TYPES
// ============================================================================

export type Region = "EMEA" | "Americas" | "Pacific" | "CN";
export type PlayerRole =
  | "Duelist"
  | "Initiator"
  | "Controller"
  | "Sentinel"
  | "Flex";

export interface Team {
  id: number;
  name: string;
  region: Region;
  logo_url: string | null;
}

export interface PlayerBasic {
  id: number;
  name: string;
  team_id?: number;
  role: "Duelist" | "Initiator" | "Controller" | "Sentinel" | "Flex";
}

export interface Player {
  id: number;
  name: string;
  role: PlayerRole;
  region: Region;
  team_id: number | null;
  current_price: number;
  base_price: number;
  points: number;
  matches_played: number;
  photo_url: string | null;
  team?: Team; // Optional relation loaded via join
}

export interface PriceHistory {
  id: number;
  player_id: number;
  date: string;
  price: number;
}

// ============================================================================
// MATCH & STATISTICS TYPES
// ============================================================================

export type MatchStatus = "upcoming" | "live" | "completed";

export interface Match {
  id: number;
  vlr_match_id: string;
  date: string | null;
  status: MatchStatus;
  tournament_name: string | null;
  stage: string | null;
  vlr_url: string | null;
  is_processed: boolean;
  format: string | null;
  team_a_id: number | null;
  team_b_id: number | null;
  score_team_a: number;
  score_team_b: number;
  team_a?: Team;
  team_b?: Team;
  player_stats?: PlayerMatchStats[];
}

export interface PlayerMatchStats {
  id: number;
  match_id: number;
  player_id: number;
  agent: string | null;
  kills: number;
  death: number;
  assists: number;
  acs: number;
  adr: number;
  kast: number;
  hs_percent: number;
  rating: number;
  first_kills: number;
  first_deaths: number;
  clutches_won: number;
  fantasy_points_earned: number;
  player?: Player;
}

// ============================================================================
// API ERROR TYPES
// ============================================================================

export interface AppError {
  status_code: number;
  error_code: string;
  message: string;
  details?: any;
}

// ============================================================================
// DASHBOARD TYPES
// ============================================================================

export interface PointsHistoryItem {
  recorded_at: string;
  total_points: number;
  global_rank: number | null;
}

export interface DashboardOverview {
  total_points: number;
  global_rank: string;
  active_leagues: number;
  available_budget: string;
  points_history: PointsHistoryItem[];
}
