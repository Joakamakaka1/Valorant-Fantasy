"use client";

import { useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { matchesApi, tournamentsApi } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";
import { MatchCard } from "./match-card";
import { MatchesSkeleton } from "./matches-skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function MatchesView() {
  const [statusFilter, setStatusFilter] = useState("live");
  const [currentRegion, setCurrentRegion] = useState("ALL");
  const [tournamentFilter, setTournamentFilter] = useState<string>("all");

  const regions = ["ALL", "AMERICAS", "EMEA", "PACIFIC", "CN"];

  // Fetch tournaments
  const { data: tournaments = [] } = useQuery({
    queryKey: ["tournaments"],
    queryFn: () => tournamentsApi.getAll(),
    staleTime: 1000 * 60 * 10, // 10 minutes cache
  });

  // Helper to simplify tournament names
  const simplifyTournamentName = (name: string) => {
    // Simplify Kickoff tournaments to just "Kickoff 2026"
    if (name.includes("Kickoff") && name.includes("2026")) {
      return "Kickoff 2026";
    }
    return name;
  };

  // Check if selected tournament is international (Masters/Champions)
  const selectedTournament = tournaments.find(
    (t) => t.id.toString() === tournamentFilter,
  );
  const isInternationalTournament =
    selectedTournament?.name.includes("Masters") ||
    selectedTournament?.name.includes("Champions");

  const {
    data: allMatches = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["matches", tournamentFilter],
    queryFn: async () => {
      const params =
        tournamentFilter !== "all"
          ? { tournament_id: parseInt(tournamentFilter), limit: 500 }
          : { limit: 500 };
      const data = await matchesApi.getAll(params);
      // Sort: Newest first (consistent with backend but reinforced here)
      return data.sort((a, b) => {
        const dateA = a.date ? new Date(a.date).getTime() : 0;
        const dateB = b.date ? new Date(b.date).getTime() : 0;
        return dateB - dateA;
      });
    },
    staleTime: 1000 * 60 * 5, // 5 minutes cache
  });

  // Filter and Sort matches
  const filteredMatches = allMatches
    .filter((match) => {
      // 1. Status Filter
      let statusMatch = true;
      if (statusFilter !== "all") {
        if (statusFilter === "upcoming")
          statusMatch = match.status === "upcoming";
        else if (statusFilter === "live") statusMatch = match.status === "live";
        else if (statusFilter === "completed")
          statusMatch = match.status === "completed";
      }

      if (!statusMatch) return false;

      // 2. Region Filter Logic
      const tournament = match.tournament_name?.toUpperCase() || "";
      const teamAName = match.team_a?.name?.toUpperCase() || "";
      const teamBName = match.team_b?.name?.toUpperCase() || "";

      // Regions from teams (strictly excluding TBD)
      const regionA =
        teamAName && !teamAName.includes("TBD")
          ? match.team_a?.region?.toUpperCase()
          : null;
      const regionB =
        teamBName && !teamBName.includes("TBD")
          ? match.team_b?.region?.toUpperCase()
          : null;

      // Hierarchical Detection
      const detectedRegion = (() => {
        if (tournament.includes("AMERICAS")) return "AMERICAS";
        if (tournament.includes("EMEA")) return "EMEA";
        if (tournament.includes("PACIFIC")) return "PACIFIC";
        if (tournament.includes("CHINA") || tournament.includes("CN"))
          return "CN";

        // Fallback to team regions if tournament is generic
        if (regionA === "AMERICAS" || regionB === "AMERICAS") return "AMERICAS";
        if (regionA === "EMEA" || regionB === "EMEA") return "EMEA";
        if (regionA === "PACIFIC" || regionB === "PACIFIC") return "PACIFIC";
        if (regionA === "CN" || regionB === "CN") return "CN";

        return null;
      })();

      // Skip region filter for international tournaments (Masters/Champions)
      if (currentRegion === "ALL" || isInternationalTournament) return true;
      return detectedRegion === currentRegion;
    })
    .sort((a, b) => {
      const dateA = a.date ? new Date(a.date).getTime() : 0;
      const dateB = b.date ? new Date(b.date).getTime() : 0;

      // 'all' and 'upcoming' sort oldest-to-newest (ascending)
      // 'completed' and 'live' sort newest-to-oldest (descending)
      const isAscending = statusFilter === "all" || statusFilter === "upcoming";
      return isAscending ? dateA - dateB : dateB - dateA;
    });

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6 overflow-y-auto">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white uppercase tracking-tighter italic">
            Match <span className="text-[#ff4655]">Results</span>
          </h1>
          <p className="text-sm sm:text-base text-zinc-400">
            Recent and upcoming matches across all VCT tournaments.
          </p>
        </div>

        {/* Tournament Filter */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <label className="text-sm font-bold text-zinc-400 uppercase tracking-wide">
            Tournament:
          </label>
          <Select value={tournamentFilter} onValueChange={setTournamentFilter}>
            <SelectTrigger className="w-full sm:w-[300px] bg-zinc-900/40 border-zinc-800 text-white [&>span[data-radix-select-icon]]:hidden">
              <div className="flex-1 text-left">
                <SelectValue placeholder="All Tournaments" />
              </div>
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="all" className="text-white">
                All Tournaments
              </SelectItem>
              {tournaments.map((tournament) => (
                <SelectItem
                  key={tournament.id}
                  value={tournament.id.toString()}
                  className="text-white"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold ${
                        tournament.status === "ONGOING"
                          ? "bg-green-600"
                          : tournament.status === "UPCOMING"
                            ? "bg-blue-600"
                            : "bg-gray-600"
                      }`}
                    >
                      {tournament.status}
                    </span>
                    {simplifyTournamentName(tournament.name)}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Region Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 -mx-4 px-4 md:mx-0 md:px-0 md:flex-wrap no-scrollbar">
          {regions.map((region) => (
            <button
              key={region}
              onClick={() => setCurrentRegion(region)}
              className={`px-4 py-2 rounded-lg text-xs font-black uppercase italic transition-all border ${
                currentRegion === region
                  ? "bg-[#ff4655] text-white border-[#ff4655] shadow-lg"
                  : "bg-zinc-900/40 text-zinc-500 border-zinc-800 hover:border-zinc-700 hover:text-white"
              }`}
            >
              {region}
            </button>
          ))}
        </div>

        <Tabs
          defaultValue="live"
          value={statusFilter}
          onValueChange={setStatusFilter}
          className="w-full"
        >
          <div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0 no-scrollbar">
            <TabsList className="bg-zinc-900/40 border border-zinc-800 w-full min-w-max md:min-w-0 justify-start md:justify-between p-1 h-10 md:h-12 rounded-xl">
              <TabsTrigger
                value="live"
                className="flex-1 data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-600 data-[state=active]:to-red-500 data-[state=active]:text-white px-4 md:px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all animate-pulse data-[state=active]:animate-pulse text-xs md:text-sm whitespace-nowrap"
              >
                🔴 Live
              </TabsTrigger>
              <TabsTrigger
                value="all"
                className="flex-1 data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-4 md:px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all text-xs md:text-sm whitespace-nowrap"
              >
                All Matches
              </TabsTrigger>
              <TabsTrigger
                value="upcoming"
                className="flex-1 data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-4 md:px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all text-xs md:text-sm whitespace-nowrap"
              >
                Upcoming
              </TabsTrigger>
              <TabsTrigger
                value="completed"
                className="flex-1 data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-4 md:px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all text-xs md:text-sm whitespace-nowrap"
              >
                Completed
              </TabsTrigger>
            </TabsList>
          </div>
        </Tabs>

        {isLoading ? (
          <MatchesSkeleton />
        ) : isError ? (
          <div className="flex flex-col items-center justify-center p-12 text-center text-red-500">
            <AlertCircle className="size-12 mb-4" />
            <h3 className="text-xl font-bold uppercase">System Error</h3>
            <p className="text-zinc-400 max-w-md">
              Could not retrieve matches. Please check your connection and try
              again.
            </p>
          </div>
        ) : (
          <div
            key={statusFilter}
            className="animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            {filteredMatches.length === 0 ? (
              <p className="text-zinc-500 italic">No matches found.</p>
            ) : (
              <div className="grid gap-4">
                {filteredMatches.map((match) => (
                  <MatchCard key={match.id} match={match} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </SidebarInset>
  );
}
