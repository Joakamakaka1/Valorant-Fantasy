"use client";

import { useEffect, useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { matchesApi } from "@/lib/api";
import { type Match } from "@/lib/types";
import { type PlayerBasic } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, Trophy, ExternalLink } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LoadingState } from "@/components/shared/loading-state";

// Interface for aggregated player stats
interface AggregatedPlayerStat {
  player: PlayerBasic | undefined;
  kills: number;
  deaths: number;
  assists: number;
  fantasy_points: number;
  agents: Set<string>;
}

export default function MatchesPage() {
  const [allMatches, setAllMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    async function loadMatches() {
      setLoading(true);
      try {
        // Fetch ALL matches once
        const matchesData = await matchesApi.getAll({});
        const sortedMatches = [...matchesData].sort((a, b) => {
          const dateA = a.date ? new Date(a.date).getTime() : 0;
          const dateB = b.date ? new Date(b.date).getTime() : 0;
          return dateB - dateA;
        });
        setAllMatches(sortedMatches);

        // Debug: log first completed match with stats
        const completedMatch = sortedMatches.find(
          (m) => m.status === "completed",
        );
        if (completedMatch) {
          console.log("First completed match:", {
            id: completedMatch.id,
            team_a_id: completedMatch.team_a_id,
            team_b_id: completedMatch.team_b_id,
            player_stats_count: completedMatch.player_stats?.length || 0,
            first_stat: completedMatch.player_stats?.[0],
          });
        }
      } catch (error) {
        console.error("Failed to load matches:", error);
      } finally {
        setLoading(false);
      }
    }
    loadMatches();
  }, []);

  // Filter client-side
  const filteredMatches = allMatches.filter((match) => {
    if (statusFilter === "all") return true;
    if (statusFilter === "upcoming")
      return match.status === "upcoming" || match.status === "live";
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
          defaultValue="all"
          value={statusFilter}
          onValueChange={setStatusFilter}
          className="w-full"
        >
          <TabsList className="bg-zinc-950 border border-zinc-800 w-full justify-start p-1 h-12 rounded-xl">
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

        {loading ? (
          <LoadingState
            message="INTERCEPTING MATCH DATA..."
            className="py-20"
          />
        ) : filteredMatches.length === 0 ? (
          <p className="text-zinc-500 italic">No matches found.</p>
        ) : (
          <div
            key={statusFilter}
            className="grid gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            {filteredMatches.map((match) => (
              <Card key={match.id} className="border-zinc-800 bg-zinc-900/50">
                <CardHeader className="pb-2">
                  <div className="relative flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-zinc-500">
                      <Calendar className="size-3" />
                      {match.date
                        ? new Date(match.date).toLocaleDateString()
                        : "TBD"}
                    </div>

                    {/* Centered Status Badge */}
                    <div className="absolute left-1/2 -translate-x-1/2">
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
                        <ExternalLink className="size-3" />
                      </a>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between gap-8 mb-6">
                    <div className="flex flex-1 items-center justify-end gap-3">
                      <span className="font-bold text-white text-right">
                        {match.team_a?.name || "TBD"}
                      </span>
                      {match.team_a?.logo_url && (
                        <img
                          src={match.team_a.logo_url}
                          alt=""
                          className="size-10 object-contain"
                        />
                      )}
                    </div>

                    <div className="flex items-center gap-4 px-6 py-3 bg-black/40 rounded-xl min-w-[120px] justify-center border border-zinc-800/50">
                      <span
                        className={`text-3xl font-black ${match.score_team_a > match.score_team_b ? "text-[#ff4655]" : "text-white"}`}
                      >
                        {match.score_team_a}
                      </span>
                      <span className="text-zinc-600 font-bold text-xl">:</span>
                      <span
                        className={`text-3xl font-black ${match.score_team_b > match.score_team_a ? "text-[#ff4655]" : "text-white"}`}
                      >
                        {match.score_team_b}
                      </span>
                    </div>

                    <div className="flex flex-1 items-center gap-3">
                      {match.team_b?.logo_url && (
                        <img
                          src={match.team_b.logo_url}
                          alt=""
                          className="size-10 object-contain"
                        />
                      )}
                      <span className="font-bold text-white text-left">
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

                      {!match.player_stats ||
                      match.player_stats.length === 0 ? (
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
                                const teamAStats = match.player_stats
                                  .filter(
                                    (s) =>
                                      s.player?.team_id === match.team_a_id,
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
                                      acc[playerId].kills += stat.kills;
                                      acc[playerId].deaths += stat.death;
                                      acc[playerId].assists += stat.assists;
                                      acc[playerId].fantasy_points +=
                                        stat.fantasy_points_earned;
                                      if (stat.agent)
                                        acc[playerId].agents.add(stat.agent);
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
                                    (
                                      a: AggregatedPlayerStat,
                                      b: AggregatedPlayerStat,
                                    ) => b.fantasy_points - a.fantasy_points,
                                  )
                                  .map((playerStat: AggregatedPlayerStat) => (
                                    <div
                                      key={playerStat.player?.id}
                                      className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/50 hover:bg-zinc-900/70 transition-all border border-zinc-800/30"
                                    >
                                      <div className="flex items-center gap-3 flex-1 min-w-0">
                                        <span className="text-[10px] font-bold text-zinc-500 w-20 uppercase shrink-0">
                                          {playerStat.agents.size === 1
                                            ? Array.from(playerStat.agents)[0]
                                            : `${playerStat.agents.size} agents`}
                                        </span>
                                        <span className="text-sm font-semibold text-white truncate">
                                          {playerStat.player?.name || "Unknown"}
                                        </span>
                                      </div>
                                      <div className="flex flex-col items-end gap-0.5 shrink-0">
                                        <span className="text-sm font-black text-[#ff4655]">
                                          {playerStat.fantasy_points.toFixed(1)}{" "}
                                          pts
                                        </span>
                                        <span className="text-[9px] text-zinc-600">
                                          {playerStat.kills}/{playerStat.deaths}
                                          /{playerStat.assists}
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
                                const teamBStats = match.player_stats
                                  .filter(
                                    (s) =>
                                      s.player?.team_id === match.team_b_id,
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
                                      acc[playerId].kills += stat.kills;
                                      acc[playerId].deaths += stat.death;
                                      acc[playerId].assists += stat.assists;
                                      acc[playerId].fantasy_points +=
                                        stat.fantasy_points_earned;
                                      if (stat.agent)
                                        acc[playerId].agents.add(stat.agent);
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
                                    (a: any, b: any) =>
                                      b.fantasy_points - a.fantasy_points,
                                  )
                                  .map((playerStat: any) => (
                                    <div
                                      key={playerStat.player.id}
                                      className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/50 hover:bg-zinc-900/70 transition-all border border-zinc-800/30"
                                    >
                                      <div className="flex items-center gap-3 flex-1 min-w-0">
                                        <span className="text-[10px] font-bold text-zinc-500 w-20 uppercase shrink-0">
                                          {playerStat.agents.size === 1
                                            ? Array.from(playerStat.agents)[0]
                                            : `${playerStat.agents.size} agents`}
                                        </span>
                                        <span className="text-sm font-semibold text-white truncate">
                                          {playerStat.player?.name || "Unknown"}
                                        </span>
                                      </div>
                                      <div className="flex flex-col items-end gap-0.5 shrink-0">
                                        <span className="text-sm font-black text-[#ff4655]">
                                          {playerStat.fantasy_points.toFixed(1)}{" "}
                                          pts
                                        </span>
                                        <span className="text-[9px] text-zinc-600">
                                          {playerStat.kills}/{playerStat.deaths}
                                          /{playerStat.assists}
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
                      {match.tournament_name}{" "}
                      {match.stage && `- ${match.stage}`}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </SidebarInset>
  );
}
