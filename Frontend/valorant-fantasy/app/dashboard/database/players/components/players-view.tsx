"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { professionalApi } from "@/lib/api";
import { Player } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { PlayerDetailsDialog } from "./player-details-dialog";
import { PlayersSkeleton } from "./players-skeleton";
import { AlertCircle } from "lucide-react";
import { PlayerCard } from "./player-card";
import { RegionFilter } from "@/components/region-filter";

const REGIONS = ["ALL", "EMEA", "Americas", "Pacific", "CN"];
const INITIAL_LOAD = 30; // Initial number of players to show
const LOAD_MORE = 24; // Number of players to load on scroll

export function PlayersView() {
  const [currentRegion, setCurrentRegion] = useState("ALL");
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [displayCount, setDisplayCount] = useState(INITIAL_LOAD);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Use React Query for fetching players
  const {
    data: allPlayers = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["all-players-db"],
    queryFn: () => professionalApi.getPlayers({ limit: 300 }),
    staleTime: 1000 * 60 * 60, // 1 hour cache
  });

  const filteredPlayers = allPlayers.filter(
    (p) =>
      currentRegion === "ALL" ||
      p.region.toUpperCase() === currentRegion.toUpperCase(),
  );

  // Reset display count when region changes
  useEffect(() => {
    setDisplayCount(INITIAL_LOAD);
  }, [currentRegion]);

  // Infinite scroll implementation
  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      if (!target) return;

      if (target.isIntersecting && displayCount < filteredPlayers.length) {
        setDisplayCount((prev) =>
          Math.min(prev + LOAD_MORE, filteredPlayers.length),
        );
      }
    },
    [displayCount, filteredPlayers.length],
  );

  useEffect(() => {
    const element = loadMoreRef.current;
    if (!element) return;

    // Create observer
    observerRef.current = new IntersectionObserver(handleObserver, {
      root: null,
      rootMargin: "400px", // Start loading before reaching the bottom
      threshold: 0.1,
    });

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [handleObserver]);

  // Only display the first N players
  const displayedPlayers = filteredPlayers.slice(0, displayCount);
  const hasMore = displayCount < filteredPlayers.length;

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
        <RegionFilter
          regions={REGIONS}
          currentRegion={currentRegion}
          onRegionChange={setCurrentRegion}
        />

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
                  {filteredPlayers.length} Players Found
                  {displayCount < filteredPlayers.length}
                </p>
              </div>

              {/* Player Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {displayedPlayers.map((player) => (
                  <PlayerCard
                    key={player.id}
                    player={player}
                    onClick={setSelectedPlayer}
                  />
                ))}
              </div>

              {/* Intersection Observer Target & Loading Indicator */}
              {hasMore && (
                <div
                  ref={loadMoreRef}
                  className="flex items-center justify-center py-8"
                >
                  <div className="flex flex-col items-center gap-2">
                    <div className="size-8 border-2 border-[#ff4655] border-t-transparent rounded-full animate-spin" />
                    <p className="text-xs text-zinc-500 font-bold uppercase">
                      Loading more operators...
                    </p>
                  </div>
                </div>
              )}

              {/* End message */}
              {!hasMore && displayedPlayers.length > 0 && (
                <div className="flex items-center justify-center py-8">
                  <p className="text-xs text-zinc-600 font-bold uppercase">
                    All operators loaded
                  </p>
                </div>
              )}
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
