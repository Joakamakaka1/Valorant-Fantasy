/**
 * @file api.ts
 * @description Axios-based API client with automatic token attachment and error handling.
 */

import axios from "axios";
import {
  LoginData,
  RegisterData,
  TokenResponse,
  User,
  League,
  LeagueMember,
  RosterEntry,
  Player,
  Team,
  Match,
  DashboardOverview,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to add token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      // Modern way to set headers in Axios 1.x
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Interceptor to handle token expiration/auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url;

    if (status === 401) {
      console.warn(`[API 401] Unauthorized access to: ${url}`);

      // Only clear session if we are not already on login/register pages
      // to avoid breaking the auth flow itself on initial failures
      const isAuthPath =
        typeof window !== "undefined" &&
        (window.location.pathname.includes("/login") ||
          window.location.pathname.includes("/register"));

      if (typeof window !== "undefined" && !isAuthPath) {
        console.error("Session expired or invalid token. Clearing storage.");
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        // Optional: Trigger a redirect or event
        // window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

// ============================================================================
// AUTH API
// ============================================================================

export const authApi = {
  login: async (data: LoginData): Promise<TokenResponse> => {
    // Backend expects 'username' and 'password' in Form Data for /login/token (FastAPI spec)
    // or JSON if custom endpoint. Check backend implementation.
    // backend uer.py: class UserLogin(BaseModel): email: EmailStr, password: str
    const response = await api.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post<User>("/auth/register", data);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>("/auth/me");
    return response.data;
  },
};

export const leaguesApi = {
  getAll: async (): Promise<League[]> => {
    const response = await api.get<League[]>("/leagues/");
    return response.data;
  },
  getMyLeagues: async (): Promise<LeagueMember[]> => {
    const response = await api.get<LeagueMember[]>("/leagues/my");
    return response.data;
  },

  getById: async (id: number): Promise<League> => {
    const response = await api.get<League>(`/leagues/${id}`);
    return response.data;
  },
  getByInviteCode: async (code: string): Promise<League> => {
    const response = await api.get<League>(`/leagues/invite/${code}`);
    return response.data;
  },
  getRankings: async (leagueId: number): Promise<LeagueMember[]> => {
    const response = await api.get<LeagueMember[]>(
      `/leagues/${leagueId}/rankings`,
    );
    return response.data;
  },
  getMembers: async (leagueId: number): Promise<LeagueMember[]> => {
    const response = await api.get<LeagueMember[]>(
      `/leagues/${leagueId}/members`,
    );
    return response.data;
  },
  getMemberRoster: async (memberId: number): Promise<RosterEntry[]> => {
    const response = await api.get<RosterEntry[]>(
      `/leagues/members/${memberId}/roster`,
    );
    return response.data;
  },
  addPlayerToRoster: async (
    memberId: number,
    data: any,
  ): Promise<RosterEntry> => {
    const response = await api.post<RosterEntry>(
      `/leagues/members/${memberId}/roster`,
      data,
    );
    return response.data;
  },
  removePlayerFromRoster: async (rosterId: number): Promise<void> => {
    await api.delete(`/leagues/roster/${rosterId}`);
  },
  updateMember: async (memberId: number, data: any): Promise<LeagueMember> => {
    const response = await api.patch<LeagueMember>(
      `/leagues/members/${memberId}`,
      data,
    );
    return response.data;
  },
  create: async (name: string, maxTeams: number): Promise<League> => {
    const response = await api.post<League>("/leagues/", {
      name,
      max_teams: maxTeams,
    });
    return response.data;
  },
  join: async (leagueId: number, teamName: string): Promise<LeagueMember> => {
    const response = await api.post<LeagueMember>(
      `/leagues/${leagueId}/join`,
      null,
      {
        params: { team_name: teamName },
      },
    );
    return response.data;
  },
};

export const professionalApi = {
  getPlayers: async (params?: any): Promise<Player[]> => {
    const response = await api.get<Player[]>("/professional/players", {
      params,
    });
    return response.data;
  },
  getTeams: async (params?: any): Promise<Team[]> => {
    const response = await api.get<Team[]>("/professional/teams", { params });
    return response.data;
  },
};

export const matchesApi = {
  getAll: async (params?: any): Promise<Match[]> => {
    const response = await api.get<Match[]>("/matches/", { params });
    return response.data;
  },
  getPlayerStats: async (playerId: number, recent?: number): Promise<any[]> => {
    const response = await api.get(`/matches/players/${playerId}/stats`, {
      params: { recent },
    });
    return response.data;
  },
};

export const dashboardApi = {
  getOverview: async (): Promise<DashboardOverview> => {
    const response = await api.get<DashboardOverview>("/dashboard/overview");
    return response.data;
  },
};

export default api;
