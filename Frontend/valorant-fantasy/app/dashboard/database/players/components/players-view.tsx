"use client";

import { useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { professionalApi } from "@/lib/api";
import { Player } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { PlayerDetailsDialog } from "./player-details-dialog";
import { PlayersSkeleton } from "./players-skeleton";
import { AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

// Role colors matching the trading card aesthetic
const ROLE_STYLES = {
  Duelist: {
    gradient: "from-red-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-red-500/50",
    text: "text-red-400",
  },
  Controller: {
    gradient: "from-purple-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-purple-500/50",
    text: "text-purple-400",
  },
  Initiator: {
    gradient: "from-amber-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-amber-500/50",
    text: "text-amber-400",
  },
  Sentinel: {
    gradient: "from-blue-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-blue-500/50",
    text: "text-blue-400",
  },
  Flex: {
    gradient: "from-emerald-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-emerald-500/50",
    text: "text-emerald-400",
  },
};

const regions = ["ALL", "EMEA", "Americas", "Pacific", "CN"];

export function PlayersView() {
  const [currentRegion, setCurrentRegion] = useState("ALL");
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);

  // Use React Query for fetching players
  const {
    data: allPlayers = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["all-players-db"],
    queryFn: () => professionalApi.getPlayers({ limit: 500 }),
    staleTime: 1000 * 60 * 60, // 1 hour cache
  });

  const filteredPlayers = allPlayers.filter(
    (p) =>
      currentRegion === "ALL" ||
      p.region.toUpperCase() === currentRegion.toUpperCase(),
  );

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6 overflow-y-auto bg-[#0f1923]">
        <div className="w-full flex flex-col gap-2">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white uppercase tracking-tighter italic">
            Operator <span className="text-[#ff4655]">Database</span>
          </h1>
          <p className="text-sm sm:text-base text-zinc-400">
            Protocol statistics and market valuation for active VCT personnel.
          </p>
        </div>

        {/* Region Filter */}
        <div className="flex flex-wrap gap-2">
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

        <div className="w-full">
          {isLoading ? (
            <PlayersSkeleton />
          ) : isError ? (
            <div className="flex flex-col items-center justify-center p-12 text-center text-red-500">
              <AlertCircle className="size-12 mb-4" />
              <h3 className="text-xl font-bold uppercase">System Error</h3>
              <p className="text-zinc-400 max-w-md">
                Could not retrieve agent database. Please check your connection
                and try again.
              </p>
            </div>
          ) : (
            <>
              {/* Player Count */}
              <div className="mb-4">
                <p className="text-sm text-zinc-500 font-bold uppercase">
                  {filteredPlayers.length} Operators Found
                </p>
              </div>

              {/* Player Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {filteredPlayers.map((player) => {
                  const roleStyle =
                    ROLE_STYLES[player.role as keyof typeof ROLE_STYLES];

                  return (
                    <Card
                      key={player.id}
                      onClick={() => setSelectedPlayer(player)}
                      className="bg-zinc-900 border-zinc-800 overflow-hidden cursor-pointer hover:border-[#ff4655]/50 transition-all flex flex-col h-full p-0"
                    >
                      <CardContent className="p-0 flex flex-col flex-1 h-full">
                        {/* Role Badge - Top with corner decorations */}
                        <div className="relative border-b-2 border-zinc-800/50">
                          <div
                            className={`absolute inset-0 bg-gradient-to-b ${roleStyle.gradient} opacity-60`}
                          />
                          <div className="relative px-3 py-2 flex items-center justify-center">
                            {/* Left corner decoration */}
                            <div
                              className={`absolute left-2 top-1/2 -translate-y-1/2 w-4 h-0.5 ${roleStyle.border.replace("border-t-", "bg-")}`}
                            />

                            <p
                              className={`text-[10px] font-black uppercase tracking-widest ${roleStyle.text}`}
                            >
                              {player.role}
                            </p>

                            {/* Right corner decoration */}
                            <div
                              className={`absolute right-2 top-1/2 -translate-y-1/2 w-4 h-0.5 ${roleStyle.border.replace("border-t-", "bg-")}`}
                            />
                          </div>
                        </div>

                        {/* Player Image Section */}
                        <div
                          className={`relative h-40 bg-gradient-to-b ${roleStyle.gradient} flex items-center justify-center overflow-hidden`}
                        >
                          {/* Player Image */}
                          <img
                            src="/fondo_overview.jpg"
                            alt={player.name}
                            className="absolute inset-0 w-full h-full object-cover z-0"
                          />

                          {/* Team Logo Watermark */}
                          {player.team?.logo_url && (
                            <div className="absolute bottom-2 right-2 size-8 rounded bg-zinc-900/80 border border-zinc-800 p-1 backdrop-blur-sm z-20">
                              <img
                                src={player.team.logo_url}
                                alt={player.team.name}
                                className="size-full object-contain opacity-60"
                              />
                            </div>
                          )}

                          {/* Price Badge */}
                          <div className="absolute bottom-0 left-0 right-0 bg-zinc-950/90 backdrop-blur-sm border-t border-zinc-800 py-2">
                            <p className="text-sm font-black text-white italic text-center">
                              €{player.current_price.toFixed(1)}M
                            </p>
                          </div>
                        </div>

                        {/* Player Info Section */}
                        <div className="p-3 bg-zinc-950 flex-1 flex flex-col justify-end">
                          {/* Player Name */}
                          <h3 className="text-sm font-black text-white uppercase italic leading-tight mb-1 truncate">
                            {player.name}
                          </h3>

                          {/* Team Name */}
                          <div className="flex items-center gap-1 mb-3">
                            <p className="text-[9px] text-zinc-500 font-bold uppercase truncate flex-1">
                              {player.team?.name || "Independent"}
                            </p>
                          </div>

                          {/* Stats */}
                          <div className="flex items-center justify-between text-[10px]">
                            <div className="flex flex-col">
                              <span className="text-zinc-500 font-black uppercase mb-0.5">
                                Points
                              </span>
                              <span className="text-emerald-400 font-black italic">
                                {player.points.toFixed(1)}
                              </span>
                            </div>
                            <div className="flex flex-col items-end">
                              <span className="text-zinc-500 font-black uppercase mb-0.5">
                                Matches
                              </span>
                              <span className="text-white font-black italic">
                                {player.matches_played}
                              </span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </>
          )}
        </div>

        <PlayerDetailsDialog
          player={selectedPlayer}
          open={!!selectedPlayer}
          onOpenChange={(open) => !open && setSelectedPlayer(null)}
        />
      </div>
    </SidebarInset>
  );
}
