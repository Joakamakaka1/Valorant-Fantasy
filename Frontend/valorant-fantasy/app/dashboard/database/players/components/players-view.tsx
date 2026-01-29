"use client";

import { useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { DataTable } from "@/components/data-table";
import { professionalApi } from "@/lib/api";
import { Player } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { PlayerDetailsDialog } from "./player-details-dialog";
import { PlayersSkeleton } from "./players-skeleton";
import { AlertCircle } from "lucide-react";

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

  const handleRowClick = async (id: string) => {
    const player = allPlayers.find((p) => p.id.toString() === id);
    if (!player) return;
    setSelectedPlayer(player);
  };

  const filteredPlayers = allPlayers
    .filter(
      (p) =>
        currentRegion === "ALL" || p.region.toUpperCase() === currentRegion,
    )
    .map((p) => ({
      id: p.id.toString(),
      name: p.name,
      org: p.team?.name || "Independent",
      role: p.role,
      points: p.points,
      price: `€${p.current_price.toFixed(1)}M`,
      rawPrice: p.current_price,
    }));

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
            <DataTable
              data={filteredPlayers}
              onRowClick={handleRowClick}
              currentRegion={currentRegion}
              onRegionChange={setCurrentRegion}
            />
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
