"use client";

import { LeagueMember, Team } from "@/lib/types";
import { Users } from "lucide-react";

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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter">
            League <span className="text-[#ff4655]">Leaderboard</span>
          </h3>
          <p className="text-zinc-500 text-sm font-bold uppercase tracking-wider">
            Track performance and team values.
          </p>
        </div>
      </div>

      <div className="grid gap-3">
        {sortedMembers.map((member, index) => {
          const isCurrentUser = member.user_id === currentUserId;
          const proTeam = proTeams.find(
            (t: Team) => t.id === member.selected_team_id,
          );

          return (
            <div
              key={member.id}
              className={`flex items-start justify-between p-3 sm:p-4 rounded-xl border transition-all hover:shadow-lg group ${
                isCurrentUser
                  ? "bg-zinc-950/20 border-zinc-800/50 hover:border-[#ff4655]/50"
                  : "bg-zinc-950/20 border-zinc-800/50 hover:border-[#ff4655]/50"
              }`}
            >
              <div className="flex items-start sm:items-center gap-3 sm:gap-4 min-w-0 flex-1">
                {/* Visual Identity (Logo + Rank) */}
                <div className="size-11 sm:size-14 rounded-xl bg-zinc-950 border border-zinc-800 overflow-hidden relative flex items-center justify-center shadow-inner shrink-0 transition-colors">
                  {proTeam?.logo_url ? (
                    <img
                      src={proTeam.logo_url}
                      alt={proTeam.name}
                      className="size-7 sm:size-10 object-contain opacity-80 group-hover:opacity-100 transition-opacity"
                    />
                  ) : (
                    <Users className="size-5 sm:size-6 text-zinc-700" />
                  )}
                  <div className="absolute top-0 left-0 bg-[#ff4655] text-white text-[8px] sm:text-[10px] font-black px-1.5 py-0.5 rounded-br shadow-sm">
                    #{index + 1}
                  </div>
                </div>

                {/* Identity Info */}
                <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-black text-white text-base sm:text-xl uppercase italic leading-tight transition-colors break-words">
                      {member.team_name}
                    </span>
                    {member.is_admin && (
                      <span className="text-[8px] sm:text-[10px] text-zinc-500 font-bold border border-zinc-800 px-1.5 rounded uppercase tracking-tighter shrink-0">
                        Admin
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 sm:mt-1">
                    <span className="text-[9px] sm:text-xs text-[#ff4655] font-black uppercase tracking-wider bg-[#ff4655]/10 px-1.5 sm:px-2 py-0.5 rounded break-all">
                      @{member.user?.username || "SYNCING..."}
                    </span>
                  </div>
                </div>
              </div>

              {/* Stats Section */}
              <div className="flex flex-col items-end gap-0.5 sm:gap-1 pl-3 shrink-0">
                <span className="text-emerald-400 text-lg sm:text-2xl font-black italic tracking-tighter">
                  {member.total_points.toFixed(1)}{" "}
                  <span className="text-[8px] sm:text-xs text-emerald-500/50 not-italic uppercase font-bold tracking-widest ml-0.5 sm:ml-1">
                    pts
                  </span>
                </span>
                <span className="text-[9px] sm:text-sm text-zinc-500 font-black italic uppercase">
                  €
                  {member.team_value
                    ? (member.team_value / 1000000).toFixed(1)
                    : "0.0"}
                  M Value
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
