"use client";

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
import { LoadingState } from "@/components/shared/loading-state";
import { Player, PlayerMatchStats } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { matchesApi } from "@/lib/api";

interface PlayerDetailsDialogProps {
  player: Player | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface AggregatedStat {
  agent: string;
  kills: number;
  deaths: number;
  acs: number;
  adr: number;
  fp: number;
  count: number;
}

export function PlayerDetailsDialog({
  player,
  open,
  onOpenChange,
}: PlayerDetailsDialogProps) {
  // Fetch stats only when player is selected and dialog is open
  const { data: playerStats = [], isLoading } = useQuery<PlayerMatchStats[]>({
    queryKey: ["player-stats", player?.id],
    queryFn: async () => {
      if (!player) return [];
      const res = await matchesApi.getPlayerStats(player.id, 5);
      return res as unknown as PlayerMatchStats[];
    },
    enabled: !!player && open,
  });

  if (!player) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-xl p-0 overflow-hidden">
        <div className="bg-gradient-to-r from-[#ff4655] to-red-900 p-8">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div>
                <DialogTitle className="uppercase italic font-black text-4xl text-white tracking-tighter leading-none">
                  {player.name}
                </DialogTitle>
                <p className="text-white/70 font-black uppercase text-[10px] tracking-[0.2em] mt-2">
                  {player.team?.name || "Independent"} • {player.role}
                </p>
              </div>
              <div className="text-right">
                <p className="text-white/50 text-[8px] font-black uppercase tracking-widest">
                  Accumulated FPts
                </p>
                <p className="text-4xl font-black italic">
                  {player.points.toFixed(1)}
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
                  {isLoading ? (
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
                        {} as Record<string, AggregatedStat>,
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
                            {(stat.kills / (stat.deaths || 1)).toFixed(2)}
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
      </DialogContent>
    </Dialog>
  );
}
