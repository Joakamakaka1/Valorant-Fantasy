"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Calendar, ExternalLink, Trophy } from "lucide-react";
import { Match, Player } from "@/lib/types";

// Interface for aggregated player stats
interface AggregatedPlayerStat {
  player: Player | undefined;
  kills: number;
  deaths: number;
  assists: number;
  fantasy_points: number;
  agents: Set<string>;
}

interface MatchCardProps {
  match: Match;
}

export function MatchCard({ match }: MatchCardProps) {
  return (
    <Card className="border-zinc-800/50 bg-zinc-900/40">
      <CardHeader className="pb-2">
        <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs sm:text-sm text-zinc-500">
            <Calendar className="size-4 sm:size-5" />
            {match.date ? new Date(match.date).toLocaleDateString() : "TBD"}
          </div>

          {/* Centered Status Badge - hide on very small screens to prevent overlap */}
          <div className="hidden sm:block sm:absolute sm:left-1/2 sm:-translate-x-1/2">
            <div
              className={`text-[10px] font-bold uppercase px-3 py-1 rounded-full border ${
                match.status === "live"
                  ? "bg-red-500/10 text-red-500 border-red-500/20 animate-pulse"
                  : match.status === "completed"
                    ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                    : "bg-blue-500/10 text-blue-500 border-blue-500/20"
              }`}
            >
              {match.status}
            </div>
          </div>

          {match.vlr_url && (
            <a
              href={match.vlr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-600 hover:text-[#ff4655] transition-colors"
              title="View on VLR.gg"
            >
              <ExternalLink className="size-4 sm:size-5" />
            </a>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 sm:gap-8 mb-6">
          <div className="flex-1 basis-0 min-w-0 flex w-full sm:w-auto items-center justify-center sm:justify-end gap-2 sm:gap-3 order-1">
            <span className="font-bold text-sm sm:text-lg text-white text-center sm:text-right truncate max-w-full">
              {match.team_a?.name || "TBD"}
            </span>
            {match.team_a?.logo_url && (
              <img
                src={match.team_a.logo_url}
                alt=""
                className="size-8 sm:size-10 object-contain shrink-0"
              />
            )}
          </div>

          <div className="flex items-center gap-3 sm:gap-4 px-4 sm:px-6 py-2 sm:py-3 bg-black/40 rounded-xl min-w-[100px] sm:min-w-[120px] justify-center border border-zinc-800/50 order-2 shrink-0">
            <span
              className={`text-2xl sm:text-3xl font-black ${
                match.score_team_a > match.score_team_b
                  ? "text-[#ff4655]"
                  : "text-white"
              }`}
            >
              {match.score_team_a}
            </span>
            <span className="text-zinc-600 font-bold text-lg sm:text-xl">
              :
            </span>
            <span
              className={`text-2xl sm:text-3xl font-black ${
                match.score_team_b > match.score_team_a
                  ? "text-[#ff4655]"
                  : "text-white"
              }`}
            >
              {match.score_team_b}
            </span>
          </div>

          <div className="flex-1 basis-0 min-w-0 flex w-full sm:w-auto items-center justify-center sm:justify-start gap-2 sm:gap-3 order-3">
            {match.team_b?.logo_url && (
              <img
                src={match.team_b.logo_url}
                alt=""
                className="size-8 sm:size-10 object-contain shrink-0"
              />
            )}
            <span className="font-bold text-sm sm:text-lg text-white text-center sm:text-left truncate max-w-full">
              {match.team_b?.name || "TBD"}
            </span>
          </div>
        </div>

        {/* Player Stats Section - Only show for completed matches */}
        {match.status === "completed" && (
          <div className="mt-4 pt-4 border-t border-zinc-800">
            <h3 className="text-xs font-bold text-zinc-400 uppercase mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-[#ff4655] rounded-full"></span>
              Player Performance (All Maps)
            </h3>

            {!match.player_stats || match.player_stats.length === 0 ? (
              <div className="text-xs text-zinc-600 italic text-center py-4">
                No player statistics available for this match
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Team A Players */}
                  <div className="space-y-2">
                    <div className="text-[10px] font-bold text-zinc-500 uppercase mb-2 px-2">
                      {match.team_a?.name || "Team A"}
                    </div>
                    {(() => {
                      // Aggregate stats by player for Team A
                      const teamAStats = match
                        .player_stats!.filter(
                          (s) => s.player?.team_id === match.team_a_id,
                        )
                        .reduce(
                          (acc, stat) => {
                            const playerId = stat.player_id;
                            if (!acc[playerId]) {
                              acc[playerId] = {
                                player: stat.player,
                                kills: 0,
                                deaths: 0,
                                assists: 0,
                                fantasy_points: 0,
                                agents: new Set<string>(),
                              };
                            }
                            const entry = acc[playerId]!;
                            entry.kills += stat.kills;
                            entry.deaths += stat.death;
                            entry.assists += stat.assists;
                            entry.fantasy_points += stat.fantasy_points_earned;
                            if (stat.agent) entry.agents.add(stat.agent);
                            return acc;
                          },
                          {} as Record<number, AggregatedPlayerStat>,
                        );

                      const teamAPlayers = Object.values(teamAStats);

                      if (teamAPlayers.length === 0) {
                        return (
                          <div className="text-xs text-zinc-700 italic px-2">
                            No stats available
                          </div>
                        );
                      }

                      return teamAPlayers
                        .sort(
                          (a: AggregatedPlayerStat, b: AggregatedPlayerStat) =>
                            b.fantasy_points - a.fantasy_points,
                        )
                        .map((playerStat: AggregatedPlayerStat) => (
                          <div
                            key={playerStat.player?.id}
                            className="flex items-center justify-between p-2 rounded-xl bg-zinc-950/20 border border-zinc-800/50 transition-all hover:border-[#ff4655]/50 hover:shadow-lg group"
                          >
                            <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                              <span className="text-[9px] sm:text-[11px] font-bold text-zinc-500 w-14 sm:w-20 uppercase shrink-0 leading-tight">
                                {playerStat.agents.size === 1
                                  ? Array.from(playerStat.agents)[0]
                                  : `${playerStat.agents.size} agents`}
                              </span>
                              <span className="text-xs sm:text-sm font-semibold text-white truncate">
                                {playerStat.player?.name || "Unknown"}
                              </span>
                            </div>
                            <div className="flex flex-col items-end gap-0.5 shrink-0">
                              <span className="text-xs sm:text-sm font-black text-emerald-500 whitespace-nowrap">
                                {playerStat.fantasy_points.toFixed(1)} pts
                              </span>
                              <span className="text-[8px] sm:text-[9px] text-zinc-600">
                                {playerStat.kills}/{playerStat.deaths}/
                                {playerStat.assists}
                              </span>
                            </div>
                          </div>
                        ));
                    })()}
                  </div>

                  {/* Team B Players */}
                  <div className="space-y-2">
                    <div className="text-[10px] font-bold text-zinc-500 uppercase mb-2 px-2">
                      {match.team_b?.name || "Team B"}
                    </div>
                    {(() => {
                      // Aggregate stats by player for Team B
                      const teamBStats = match
                        .player_stats!.filter(
                          (s) => s.player?.team_id === match.team_b_id,
                        )
                        .reduce(
                          (acc, stat) => {
                            const playerId = stat.player_id;
                            if (!acc[playerId]) {
                              acc[playerId] = {
                                player: stat.player,
                                kills: 0,
                                deaths: 0,
                                assists: 0,
                                fantasy_points: 0,
                                agents: new Set<string>(),
                              };
                            }
                            const entry = acc[playerId]!;
                            entry.kills += stat.kills;
                            entry.deaths += stat.death;
                            entry.assists += stat.assists;
                            entry.fantasy_points += stat.fantasy_points_earned;
                            if (stat.agent) entry.agents.add(stat.agent);
                            return acc;
                          },
                          {} as Record<number, AggregatedPlayerStat>,
                        );

                      const teamBPlayers = Object.values(teamBStats);

                      if (teamBPlayers.length === 0) {
                        return (
                          <div className="text-xs text-zinc-700 italic px-2">
                            No stats available
                          </div>
                        );
                      }

                      return teamBPlayers
                        .sort(
                          (a: AggregatedPlayerStat, b: AggregatedPlayerStat) =>
                            b.fantasy_points - a.fantasy_points,
                        )
                        .map((playerStat: AggregatedPlayerStat) => (
                          <div
                            key={playerStat.player?.id}
                            className="flex items-center justify-between p-2 rounded-xl bg-zinc-950/20 border border-zinc-800/50 transition-all hover:border-[#ff4655]/50 hover:shadow-lg group"
                          >
                            <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
                              <span className="text-[9px] sm:text-[11px] font-bold text-zinc-500 w-14 sm:w-20 uppercase shrink-0 leading-tight">
                                {playerStat.agents.size === 1
                                  ? Array.from(playerStat.agents)[0]
                                  : `${playerStat.agents.size} agents`}
                              </span>
                              <span className="text-xs sm:text-sm font-semibold text-white truncate">
                                {playerStat.player?.name || "Unknown"}
                              </span>
                            </div>
                            <div className="flex flex-col items-end gap-0.5 shrink-0">
                              <span className="text-xs sm:text-sm font-black text-emerald-500 whitespace-nowrap">
                                {playerStat.fantasy_points.toFixed(1)} pts
                              </span>
                              <span className="text-[8px] sm:text-[9px] text-zinc-600">
                                {playerStat.kills}/{playerStat.deaths}/
                                {playerStat.assists}
                              </span>
                            </div>
                          </div>
                        ));
                    })()}
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {match.tournament_name && (
          <div className="mt-4 pt-4 border-t border-zinc-800 flex items-center gap-2 text-xs text-zinc-500">
            <Trophy className="size-3 text-amber-500" />
            {match.tournament_name} {match.stage && `- ${match.stage}`}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
