import axios, { AxiosError } from "axios";
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

// In a HttpOnly Cookie architecture, the client cannot read the token.
// Therefore, the browser must send the cookie automatically.
// This requires the API to be on the same domain (via Next.js Middleware Proxy)
// We FORCE the use of /api relative path to ensure cookies are sent to Next.js
// Basic Setup
const API_BASE_URL = "/api";

/**
 * ApiClient Wrapper
 *
 * Wraps Axios to provide type-safe methods that match our interceptor logic.
 * The interceptor unwraps the response (returns data directly), so we need
 * to reflect that in the return types (Promise<T> instead of Promise<AxiosResponse<T>>).
 */
class ApiClient {
  private axiosInstance: import("axios").AxiosInstance;

  constructor(baseURL: string) {
    this.axiosInstance = axios.create({
      baseURL,
      withCredentials: true,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.axiosInstance.interceptors.response.use(
      (response) => {
        if (response.data?.success && "data" in response.data) {
          return response.data.data;
        }
        return response.data;
      },
      (error: AxiosError<any>) => {
        const errorData = error.response?.data;
        const errorMessage =
          errorData?.error?.message || errorData?.detail || error.message;

        // Mutate error object to be more useful
        error.message = errorMessage;
        return Promise.reject(error);
      },
    );
  }

  // Generic methods that match the interceptor's behavior
  async get<T>(
    url: string,
    config?: import("axios").AxiosRequestConfig,
  ): Promise<T> {
    return this.axiosInstance.get(url, config) as Promise<T>;
  }

  async post<T>(
    url: string,
    data?: any,
    config?: import("axios").AxiosRequestConfig,
  ): Promise<T> {
    return this.axiosInstance.post(url, data, config) as Promise<T>;
  }

  async put<T>(
    url: string,
    data?: any,
    config?: import("axios").AxiosRequestConfig,
  ): Promise<T> {
    return this.axiosInstance.put(url, data, config) as Promise<T>;
  }

  async patch<T>(
    url: string,
    data?: any,
    config?: import("axios").AxiosRequestConfig,
  ): Promise<T> {
    return this.axiosInstance.patch(url, data, config) as Promise<T>;
  }

  async delete<T>(
    url: string,
    config?: import("axios").AxiosRequestConfig,
  ): Promise<T> {
    return this.axiosInstance.delete(url, config) as Promise<T>;
  }
}

export const api = new ApiClient(API_BASE_URL);

// ============================================================================
// AUTH API
// Data fetching methods for Client Components (Server Actions used for mutations)
// ============================================================================

// ============================================================================
// AUTH API
// Data fetching methods for Client Components (Server Actions used for mutations)
// ============================================================================

export const authApi = {
  // Login/Register are better handled via Server Actions for Cookie setting
  // But we keep them here if needed for client-side only flows (not recommended with HttpOnly)

  getMe: () => api.get<User>("/auth/me"),
};

export const leaguesApi = {
  getAll: () => api.get<League[]>("/leagues"),
  getMyLeagues: () => api.get<LeagueMember[]>("/leagues/my"),
  getById: (id: number) => api.get<League>(`/leagues/${id}`),
  getByInviteCode: (code: string) => api.get<League>(`/leagues/invite/${code}`),
  getRankings: (leagueId: number) =>
    api.get<LeagueMember[]>(`/leagues/${leagueId}/rankings`),
  getMembers: (leagueId: number) =>
    api.get<LeagueMember[]>(`/leagues/${leagueId}/members`),
  getMemberRoster: (memberId: number) =>
    api.get<RosterEntry[]>(`/leagues/members/${memberId}/roster`),
  addPlayerToRoster: (memberId: number, data: any) =>
    api.post<RosterEntry>(`/leagues/members/${memberId}/roster`, data),
  removePlayerFromRoster: (rosterId: number) =>
    api.delete<void>(`/leagues/roster/${rosterId}`),
  updateMember: (memberId: number, data: any) =>
    api.patch<LeagueMember>(`/leagues/members/${memberId}`, data),
  create: (name: string, maxTeams: number) =>
    api.post<League>("/leagues/", {
      name,
      max_teams: maxTeams,
    }),
  join: (leagueId: number, teamName: string) =>
    api.post<LeagueMember>(`/leagues/${leagueId}/join`, null, {
      params: { team_name: teamName },
    }),
};

export const professionalApi = {
  getPlayers: (params?: any) =>
    api.get<Player[]>("/professional/players", { params }),
  getTeams: (params?: any) =>
    api.get<Team[]>("/professional/teams", { params }),
};

export const matchesApi = {
  getAll: (params?: any) => api.get<Match[]>("/matches", { params }),
  getPlayerStats: (playerId: number, recent?: number) =>
    api.get<any[]>(`/matches/players/${playerId}/stats`, {
      params: { recent },
    }),
};

export const dashboardApi = {
  getOverview: () => api.get<DashboardOverview>("/dashboard/overview"),
};

export default api;
