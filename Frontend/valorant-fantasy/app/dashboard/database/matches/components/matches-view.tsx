"use client";

import { useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { matchesApi } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";
import { MatchCard } from "./match-card";
import { MatchesSkeleton } from "./matches-skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

export function MatchesView() {
  const [statusFilter, setStatusFilter] = useState("live");
  const [currentRegion, setCurrentRegion] = useState("ALL");

  const regions = ["ALL", "AMERICAS", "EMEA", "PACIFIC", "CN"];

  const {
    data: allMatches = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["matches"],
    queryFn: async () => {
      const data = await matchesApi.getAll({ limit: 500 });
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

      if (currentRegion === "ALL") return true;
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
          <h1 className="text-5xl font-black text-white uppercase tracking-tighter italic">
            Match <span className="text-[#ff4655]">Results</span>
          </h1>
          <p className="text-zinc-400">
            Recent and upcoming matches across all VCT tournaments.
          </p>
        </div>

        {/* Region Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {regions.map((region) => (
            <Button
              key={region}
              variant={currentRegion === region ? "outline" : "ghost"}
              size="sm"
              className={`h-8 font-black uppercase tracking-tighter italic transition-all ${
                currentRegion === region
                  ? "border-[#ff4655] bg-[#ff4655]/10 text-white"
                  : "text-zinc-500 hover:text-white"
              }`}
              onClick={() => setCurrentRegion(region)}
            >
              {region}
            </Button>
          ))}
        </div>

        <Tabs
          defaultValue="live"
          value={statusFilter}
          onValueChange={setStatusFilter}
          className="w-full"
        >
          <TabsList className="bg-zinc-900/40 border border-zinc-800 w-full justify-start p-1 h-12 rounded-xl">
            <TabsTrigger
              value="live"
              className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-600 data-[state=active]:to-red-500 data-[state=active]:text-white px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all animate-pulse data-[state=active]:animate-pulse"
            >
              🔴 Live
            </TabsTrigger>
            <TabsTrigger
              value="all"
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all"
            >
              All Matches
            </TabsTrigger>
            <TabsTrigger
              value="upcoming"
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all"
            >
              Upcoming
            </TabsTrigger>
            <TabsTrigger
              value="completed"
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all"
            >
              Completed
            </TabsTrigger>
          </TabsList>
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
