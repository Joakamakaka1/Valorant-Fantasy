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
  Tournament,
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
  getAll: (config?: import("axios").AxiosRequestConfig) =>
    api.get<League[]>("/leagues", config),
  getMyLeagues: (config?: import("axios").AxiosRequestConfig) =>
    api.get<LeagueMember[]>("/leagues/my", config),
  getById: (id: number, config?: import("axios").AxiosRequestConfig) =>
    api.get<League>(`/leagues/${id}`, config),
  getByInviteCode: (
    code: string,
    config?: import("axios").AxiosRequestConfig,
  ) => api.get<League>(`/leagues/invite/${code}`, config),
  getRankings: (
    leagueId: number,
    config?: import("axios").AxiosRequestConfig,
  ) => api.get<LeagueMember[]>(`/leagues/${leagueId}/rankings`, config),
  getMembers: (leagueId: number, config?: import("axios").AxiosRequestConfig) =>
    api.get<LeagueMember[]>(`/leagues/${leagueId}/members`, config),
  getMemberRoster: (
    memberId: number,
    config?: import("axios").AxiosRequestConfig,
  ) => api.get<RosterEntry[]>(`/leagues/members/${memberId}/roster`, config),
  addPlayerToRoster: (
    memberId: number,
    data: any,
    config?: import("axios").AxiosRequestConfig,
  ) =>
    api.post<RosterEntry>(`/leagues/members/${memberId}/roster`, data, config),
  removePlayerFromRoster: (
    rosterId: number,
    config?: import("axios").AxiosRequestConfig,
  ) => api.delete<void>(`/leagues/roster/${rosterId}`, config),
  updateMember: (
    memberId: number,
    data: any,
    config?: import("axios").AxiosRequestConfig,
  ) => api.patch<LeagueMember>(`/leagues/members/${memberId}`, data, config),
  create: (
    name: string,
    maxTeams: number,
    config?: import("axios").AxiosRequestConfig,
  ) =>
    api.post<League>(
      "/leagues/",
      {
        name,
        max_teams: maxTeams,
      },
      config,
    ),
  join: (
    leagueId: number,
    teamName: string,
    config?: import("axios").AxiosRequestConfig,
  ) =>
    api.post<LeagueMember>(`/leagues/${leagueId}/join`, null, {
      ...config,
      params: { team_name: teamName },
    }),
};

export const professionalApi = {
  getPlayers: (params?: any, config?: import("axios").AxiosRequestConfig) =>
    api.get<Player[]>("/professional/players", { params, ...config }),
  getTeams: (params?: any, config?: import("axios").AxiosRequestConfig) =>
    api.get<Team[]>("/professional/teams", { params, ...config }),
};

export const matchesApi = {
  getAll: (params?: any, config?: import("axios").AxiosRequestConfig) =>
    api.get<Match[]>("/matches", { params, ...config }),
  getPlayerStats: (playerId: number, recent?: number) =>
    api.get<any[]>(`/matches/players/${playerId}/stats`, {
      params: { recent },
    }),
};

export const tournamentsApi = {
  getAll: (params?: any, config?: import("axios").AxiosRequestConfig) =>
    api.get<Tournament[]>("/tournaments", { params, ...config }),
  getOngoing: (config?: import("axios").AxiosRequestConfig) =>
    api.get<Tournament | null>("/tournaments/ongoing", config),
  getById: (id: number, config?: import("axios").AxiosRequestConfig) =>
    api.get<Tournament>(`/tournaments/${id}`, config),
};

export default api;
