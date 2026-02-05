"use client";

import { LeagueMember, Team } from "@/lib/types";
import { Users, TrendingUp, Activity, Zap, Award } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface LeagueRankingsProps {
  members: LeagueMember[];
  currentUserId?: number | undefined;
  proTeams: Team[];
}

export function LeagueRankings({
  members,
  currentUserId,
  proTeams,
}: LeagueRankingsProps) {
  // Sort members by total points descending
  const sortedMembers = [...members].sort(
    (a, b) => b.total_points - a.total_points,
  );

  // Get top 3 for podium
  const topThree = sortedMembers.slice(0, 3);
  const restOfRankings = sortedMembers.slice(3);

  // Calculate statistics for highlighted metrics
  const highestPoints = sortedMembers[0];
  const mostValuableTeam = [...sortedMembers].sort(
    (a, b) => b.team_value - a.team_value,
  )[0];
  const mostBudgetLeft = [...sortedMembers].sort(
    (a, b) => b.budget - a.budget,
  )[0];

  // Calculate biggest rank climber (simulated, could be based on history)
  const biggestClimber = sortedMembers[Math.min(3, sortedMembers.length - 1)];

  // Podium gradient classes for each position
  const podiumGradients = [
    "from-yellow-500/20 via-amber-500/10 to-transparent", // 1st - Gold
    "from-cyan-500/20 via-blue-500/10 to-transparent", // 2nd - Cyan/Blue
    "from-orange-500/20 via-red-500/10 to-transparent", // 3rd - Orange/Red
  ];

  return (
    <div className="space-y-6">
      {/* Top 3 Podium - Olympic Style */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Reorder: 2nd, 1st, 3rd */}
        {[1, 0, 2].map((podiumIndex) => {
          const member = topThree[podiumIndex];
          if (!member) return null;

          const actualRank = podiumIndex + 1;
          const proTeam = proTeams.find(
            (t: Team) => t.id === member.selected_team_id,
          );
          const isCurrentUser = member.user_id === currentUserId;
          const isFirstPlace = podiumIndex === 0;

          return (
            <Card
              key={member.id}
              className={`bg-gradient-to-b ${podiumGradients[podiumIndex]} border-zinc-800 overflow-hidden relative group hover:border-[#ff4655]/30 transition-all ${
                isFirstPlace ? "md:mt-0" : "md:mt-8"
              }`}
            >
              <CardContent className="p-5">
                {/* Rank Badge */}
                <div className="flex justify-center mb-4">
                  <div className="bg-zinc-900/80 backdrop-blur-sm text-white text-lg font-black uppercase px-4 py-1 rounded-lg shadow-lg border border-zinc-700">
                    #{actualRank}
                  </div>
                </div>

                {/* Avatar/Logo */}
                <div className="flex flex-col items-center mb-4">
                  <div className="size-20 rounded-full bg-zinc-900 border-2 border-zinc-700 flex items-center justify-center mb-3 shadow-lg overflow-hidden relative">
                    {proTeam?.logo_url ? (
                      <img
                        src={proTeam.logo_url}
                        alt={proTeam.name}
                        className="size-12 object-contain opacity-80"
                      />
                    ) : (
                      <Users className="size-10 text-zinc-600" />
                    )}
                  </div>

                  {/* Name */}
                  <div className="text-center">
                    <h4 className="font-black text-white text-lg uppercase italic leading-tight mb-1">
                      {member.team_name}
                    </h4>
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
                      @{member.user?.username || "Loading..."}
                    </p>
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center">
                    <p className="text-[8px] text-zinc-500 uppercase font-black mb-0.5">
                      Points
                    </p>
                    <p className="text-sm font-black text-emerald-400 italic">
                      {member.total_points.toFixed(0)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-[8px] text-zinc-500 uppercase font-black mb-0.5">
                      Value
                    </p>
                    <p className="text-sm font-black text-white italic">
                      €
                      {member.team_value
                        ? (member.team_value / 1000000).toFixed(1)
                        : "0.0"}
                      M
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-[8px] text-zinc-500 uppercase font-black mb-0.5">
                      Score
                    </p>
                    <p className="text-sm font-black text-zinc-400 italic">
                      {Math.round(
                        (member.total_points / 100 +
                          (member.team_value || 0) / 1000000) *
                          10,
                      )}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Highlighted Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Highest Scorer */}
        <Card className="bg-zinc-900/40 border-zinc-800 hover:border-[#ff4655]/30 transition-all">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="size-8 rounded-full bg-emerald-500/10 flex items-center justify-center">
                <Award className="size-4 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[8px] text-zinc-500 uppercase font-black tracking-wider">
                  Top Scorer
                </p>
                <p className="text-xs font-black text-white uppercase italic truncate">
                  {highestPoints?.team_name || "N/A"}
                </p>
              </div>
              <span className="text-lg font-black text-emerald-400 italic">
                {highestPoints?.total_points.toFixed(0) || 0}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Most Valuable */}
        <Card className="bg-zinc-900/40 border-zinc-800 hover:border-[#ff4655]/30 transition-all">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="size-8 rounded-full bg-amber-500/10 flex items-center justify-center">
                <TrendingUp className="size-4 text-amber-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[8px] text-zinc-500 uppercase font-black tracking-wider">
                  Most Valuable
                </p>
                <p className="text-xs font-black text-white uppercase italic truncate">
                  {mostValuableTeam?.team_name || "N/A"}
                </p>
              </div>
              <span className="text-lg font-black text-amber-400 italic">
                {mostValuableTeam
                  ? `€${(mostValuableTeam.team_value / 1000000).toFixed(1)}M`
                  : "€0M"}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Biggest Climber */}
        <Card className="bg-zinc-900/40 border-zinc-800 hover:border-[#ff4655]/30 transition-all">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="size-8 rounded-full bg-blue-500/10 flex items-center justify-center">
                <Zap className="size-4 text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[8px] text-zinc-500 uppercase font-black tracking-wider">
                  Rising Star
                </p>
                <p className="text-xs font-black text-white uppercase italic truncate">
                  {biggestClimber?.team_name || "N/A"}
                </p>
              </div>
              <span className="text-lg font-black text-blue-400 italic">
                +2
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Most Budget Left */}
        <Card className="bg-zinc-900/40 border-zinc-800 hover:border-[#ff4655]/30 transition-all">
          <CardContent className="p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="size-8 rounded-full bg-[#ff4655]/10 flex items-center justify-center">
                <Activity className="size-4 text-[#ff4655]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[8px] text-zinc-500 uppercase font-black tracking-wider">
                  Cash Reserve
                </p>
                <p className="text-xs font-black text-white uppercase italic truncate">
                  {mostBudgetLeft?.team_name || "N/A"}
                </p>
              </div>
              <span className="text-lg font-black text-[#ff4655] italic">
                €{mostBudgetLeft?.budget.toFixed(1) || 0}M
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Full Rankings Table */}
      <div>
        <h4 className="text-lg font-black text-white uppercase italic tracking-tighter mb-3">
          Full <span className="text-[#ff4655]">Leaderboard</span>
        </h4>

        {/* Table Header */}
        <div className="hidden md:flex md:items-center md:justify-between gap-3 px-4 py-2 mb-2 border-b border-zinc-800">
          <div className="flex items-center gap-24 flex-1">
            <div className="w-12 text-[10px] text-zinc-500 uppercase font-black">
              Rank
            </div>
            <div className="flex-1 text-[10px] text-zinc-500 uppercase font-black">
              Name
            </div>
          </div>
          <div className="flex items-center gap-32">
            <div className="text-[10px] text-zinc-500 uppercase font-black text-right">
              Points
            </div>
            <div className="text-[10px] text-zinc-500 uppercase font-black text-right">
              Score
            </div>
          </div>
        </div>

        {/* Table Rows */}
        <div className="space-y-2">
          {sortedMembers.map((member, index) => {
            const isCurrentUser = member.user_id === currentUserId;
            const proTeam = proTeams.find(
              (t: Team) => t.id === member.selected_team_id,
            );

            // Calculate a simple score metric
            const score = Math.round(
              (member.total_points / 100 + (member.team_value || 0) / 1000000) *
                10,
            );

            return (
              <Card
                key={member.id}
                className={`border transition-all hover:border-[#ff4655]/50 hover:shadow-lg ${
                  isCurrentUser
                    ? "bg-[#ff4655]/5 border-[#ff4655]/30"
                    : "bg-zinc-900/20 border-zinc-800/50"
                }`}
              >
                <CardContent className="p-3 md:p-4">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                    {/* Left Side: Rank + Name */}
                    <div className="flex items-center gap-24 flex-1">
                      {/* Rank */}
                      <div
                        className={`size-8 md:size-10 rounded-lg flex items-center justify-center font-black text-sm shrink-0 ${
                          index < 3
                            ? "bg-gradient-to-br from-[#ff4655] to-[#ff4655]/70 text-white shadow-lg"
                            : "bg-zinc-800 text-zinc-400"
                        }`}
                      >
                        {index + 1}
                      </div>

                      {/* Name & Team */}
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="size-10 rounded-lg bg-zinc-900 border border-zinc-800 overflow-hidden flex items-center justify-center shrink-0">
                          {proTeam?.logo_url ? (
                            <img
                              src={proTeam.logo_url}
                              alt={proTeam.name}
                              className="size-6 object-contain opacity-80"
                            />
                          ) : (
                            <Users className="size-5 text-zinc-700" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-black text-white text-sm uppercase italic leading-tight">
                              {member.team_name}
                            </span>
                            {member.is_admin && (
                              <span className="text-[8px] text-zinc-500 font-bold border border-zinc-800 px-1.5 rounded uppercase">
                                Admin
                              </span>
                            )}
                          </div>
                          <p className="text-[10px] text-[#ff4655] font-black uppercase tracking-wider">
                            @{member.user?.username || "Loading..."}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Right Side: Points + Score */}
                    <div className="flex items-center gap-26 justify-between md:justify-end">
                      {/* Points */}
                      <div className="flex items-center gap-2">
                        <span className="md:hidden text-[10px] text-zinc-500 uppercase font-black">
                          Points
                        </span>
                        <span className="text-emerald-400 text-lg md:text-xl font-black italic">
                          {member.total_points.toFixed(1)}
                        </span>
                      </div>

                      {/* Score Badge */}
                      <div className="flex items-center gap-2">
                        <span className="md:hidden text-[10px] text-zinc-500 uppercase font-black">
                          Score
                        </span>
                        <div className="bg-zinc-950 text-white text-xs md:text-sm font-black px-2 md:px-3 py-1 rounded shadow-sm border border-zinc-700">
                          {score}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
}
