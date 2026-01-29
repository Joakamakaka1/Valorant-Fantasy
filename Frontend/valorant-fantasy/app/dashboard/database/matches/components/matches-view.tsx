"use client";

import { useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { matchesApi } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";
import { MatchCard } from "./match-card";
import { MatchesSkeleton } from "./matches-skeleton";
import { AlertCircle } from "lucide-react";

export function MatchesView() {
  const [statusFilter, setStatusFilter] = useState("live");

  const {
    data: allMatches = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["matches"],
    queryFn: async () => {
      const data = await matchesApi.getAll({});
      // Sort: Newest first
      return data.sort((a, b) => {
        const dateA = a.date ? new Date(a.date).getTime() : 0;
        const dateB = b.date ? new Date(b.date).getTime() : 0;
        return dateB - dateA;
      });
    },
    staleTime: 1000 * 60 * 5, // 5 minutes cache
  });

  // Filter client-side
  const filteredMatches = allMatches.filter((match) => {
    if (statusFilter === "all") return true;
    if (statusFilter === "upcoming") return match.status === "upcoming";
    if (statusFilter === "live") return match.status === "live";
    if (statusFilter === "completed") return match.status === "completed";
    return true;
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
