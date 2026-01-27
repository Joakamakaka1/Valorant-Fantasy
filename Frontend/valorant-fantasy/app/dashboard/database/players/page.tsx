"use client";

import { useEffect, useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { DataTable } from "@/components/data-table";
import { LoadingState } from "@/components/shared/loading-state";
import { professionalApi, matchesApi } from "@/lib/api";
import { Player, PlayerMatchStats } from "@/lib/types";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function PlayerStatsPage() {
  const [allPlayers, setAllPlayers] = useState<Player[]>([]);
  const [currentRegion, setCurrentRegion] = useState("ALL");
  const [loading, setLoading] = useState(true);

  // Player Stats Dialog
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [playerStats, setPlayerStats] = useState<PlayerMatchStats[]>([]);
  const [loadingStats, setLoadingStats] = useState(false);

  useEffect(() => {
    async function loadPlayers() {
      try {
        const playersData = await professionalApi.getPlayers({ limit: 500 });
        setAllPlayers(playersData);
      } catch (error) {
        console.error("Failed to load players:", error);
      } finally {
        setLoading(false);
      }
    }
    loadPlayers();
  }, []);

  const handleRowClick = async (id: string) => {
    const player = allPlayers.find((p) => p.id.toString() === id);
    if (!player) return;

    setSelectedPlayer(player);
    setLoadingStats(true);
    setPlayerStats([]);

    try {
      const stats = await matchesApi.getPlayerStats(player.id, 5);
      setPlayerStats(stats);
    } catch (error) {
      console.error("Failed to load player stats:", error);
    } finally {
      setLoadingStats(false);
    }
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
    }));

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6 overflow-y-auto bg-[#0f1923]">
        <div className="w-full flex flex-col gap-2 border-b border-zinc-800/50 pb-8">
          <h1 className="text-5xl font-black text-white uppercase tracking-tighter italic">
            Operator <span className="text-[#ff4655]">Database</span>
          </h1>
          <p className="text-zinc-500 font-bold uppercase text-xs tracking-widest">
            Protocol statistics and market valuation for active VCT personnel.
          </p>
        </div>

        <div className="w-full">
          {loading ? (
            <LoadingState className="h-64" />
          ) : (
            <DataTable
              data={filteredPlayers}
              onRowClick={handleRowClick}
              currentRegion={currentRegion}
              onRegionChange={setCurrentRegion}
            />
          )}
        </div>

        <Dialog
          open={!!selectedPlayer}
          onOpenChange={() => setSelectedPlayer(null)}
        >
          <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-xl p-0 overflow-hidden shadow-[0_0_50px_rgba(255,70,85,0.15)]">
            {selectedPlayer && (
              <>
                <div className="bg-gradient-to-r from-[#ff4655] to-red-900 p-8">
                  <DialogHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <DialogTitle className="uppercase italic font-black text-4xl text-white tracking-tighter leading-none">
                          {selectedPlayer.name}
                        </DialogTitle>
                        <p className="text-white/70 font-black uppercase text-[10px] tracking-[0.2em] mt-2">
                          {selectedPlayer.team?.name || "Independent"} •{" "}
                          {selectedPlayer.role}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-white/50 text-[8px] font-black uppercase tracking-widest">
                          Accumulated FPts
                        </p>
                        <p className="text-4xl font-black italic">
                          {selectedPlayer.points.toFixed(1)}
                        </p>
                      </div>
                    </div>
                  </DialogHeader>
                </div>

                <div className="p-8 space-y-6">
                  <div>
                    <h3 className="text-zinc-500 font-black uppercase text-[10px] tracking-[0.3em] mb-4">
                      Tactical Performance (Last 5 Avg)
                    </h3>
                    <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-zinc-800 bg-zinc-950/50 hover:bg-transparent">
                            <TableHead className="text-[9px] font-black uppercase text-zinc-500">
                              Agent
                            </TableHead>
                            <TableHead className="text-center text-[9px] font-black uppercase text-zinc-500">
                              Matches
                            </TableHead>
                            <TableHead className="text-center text-[9px] font-black uppercase text-zinc-500">
                              K/D
                            </TableHead>
                            <TableHead className="text-center text-[9px] font-black uppercase text-zinc-500">
                              ACS
                            </TableHead>
                            <TableHead className="text-center text-[9px] font-black uppercase text-zinc-500">
                              ADR
                            </TableHead>
                            <TableHead className="text-right text-[9px] font-black uppercase text-zinc-500 pr-4">
                              Avg FPts
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {loadingStats ? (
                            <TableRow>
                              <TableCell colSpan={6} className="h-24">
                                <LoadingState message="DECRYPTING PERFORMANCE LOGS..." />
                              </TableCell>
                            </TableRow>
                          ) : playerStats.length > 0 ? (
                            Object.values(
                              playerStats.reduce(
                                (acc, stat) => {
                                  const agent = stat.agent || "Unknown";
                                  if (!acc[agent]) {
                                    acc[agent] = {
                                      agent,
                                      kills: 0,
                                      deaths: 0,
                                      acs: 0,
                                      adr: 0,
                                      fp: 0,
                                      count: 0,
                                    };
                                  }
                                  acc[agent].kills += stat.kills;
                                  acc[agent].deaths += stat.death;
                                  acc[agent].acs += stat.acs;
                                  acc[agent].adr += stat.adr;
                                  acc[agent].fp += stat.fantasy_points_earned;
                                  acc[agent].count += 1;
                                  return acc;
                                },
                                {} as Record<string, any>,
                              ),
                            )
                              .sort((a, b) => b.fp / b.count - a.fp / a.count)
                              .map((stat, idx) => (
                                <TableRow
                                  key={idx}
                                  className="border-zinc-800/50 hover:bg-white/5 transition-colors"
                                >
                                  <TableCell className="font-bold text-xs uppercase text-zinc-300">
                                    {stat.agent}
                                  </TableCell>
                                  <TableCell className="text-center text-xs font-mono text-zinc-500">
                                    {stat.count}
                                  </TableCell>
                                  <TableCell className="text-center text-xs font-mono">
                                    {(stat.kills / (stat.deaths || 1)).toFixed(
                                      2,
                                    )}
                                  </TableCell>
                                  <TableCell className="text-center text-xs">
                                    {(stat.acs / stat.count).toFixed(0)}
                                  </TableCell>
                                  <TableCell className="text-center text-xs">
                                    {(stat.adr / stat.count).toFixed(0)}
                                  </TableCell>
                                  <TableCell className="text-right font-black text-[#ff4655] italic pr-4">
                                    +{(stat.fp / stat.count).toFixed(1)}
                                  </TableCell>
                                </TableRow>
                              ))
                          ) : (
                            <TableRow>
                              <TableCell
                                colSpan={6}
                                className="h-24 text-center text-zinc-700 italic"
                              >
                                No combat data available for this operator.
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </SidebarInset>
  );
}
