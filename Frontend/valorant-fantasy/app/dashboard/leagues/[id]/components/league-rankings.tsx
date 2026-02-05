"use client";

import { LeagueMember, Team } from "@/lib/types";
import { TrendingUp, Activity, Zap, Award, Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { PodiumCard } from "./podium-card";
import { StatCard } from "./stat-card";

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

  return (
    <div className="space-y-6">
      {/* Top 3 Podium - Olympic Style */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Reorder: 2nd, 1st, 3rd */}
        {[1, 0, 2].map((podiumIndex) => {
          const member = topThree[podiumIndex];
          if (!member) return null;

          const actualRank = podiumIndex + 1;
          const isFirstPlace = podiumIndex === 0;

          return (
            <PodiumCard
              key={member.id}
              member={member}
              rank={actualRank}
              podiumIndex={podiumIndex}
              proTeams={proTeams}
              currentUserId={currentUserId}
              isFirstPlace={isFirstPlace}
            />
          );
        })}
      </div>

      {/* Highlighted Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          icon={Award}
          iconColor="text-emerald-400"
          iconBg="bg-emerald-500/10"
          label="Top Scorer"
          teamName={highestPoints?.team_name || "N/A"}
          value={highestPoints?.total_points.toFixed(0) || "0"}
          valueColor="text-emerald-400"
        />

        <StatCard
          icon={TrendingUp}
          iconColor="text-amber-400"
          iconBg="bg-amber-500/10"
          label="Most Valuable"
          teamName={mostValuableTeam?.team_name || "N/A"}
          value={
            mostValuableTeam
              ? `€${(mostValuableTeam.team_value / 1000000).toFixed(1)}M`
              : "€0M"
          }
          valueColor="text-amber-400"
        />

        <StatCard
          icon={Zap}
          iconColor="text-blue-400"
          iconBg="bg-blue-500/10"
          label="Rising Star"
          teamName={biggestClimber?.team_name || "N/A"}
          value="+2"
          valueColor="text-blue-400"
        />

        <StatCard
          icon={Activity}
          iconColor="text-[#ff4655]"
          iconBg="bg-[#ff4655]/10"
          label="Cash Reserve"
          teamName={mostBudgetLeft?.team_name || "N/A"}
          value={`€${mostBudgetLeft?.budget.toFixed(1) || 0}M`}
          valueColor="text-[#ff4655]"
        />
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
