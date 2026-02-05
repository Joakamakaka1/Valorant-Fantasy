"use client";

import { Card, CardContent } from "@/components/ui/card";
import { LeagueMember, Team } from "@/lib/types";
import { Users } from "lucide-react";

interface PodiumCardProps {
  member: LeagueMember;
  rank: number;
  podiumIndex: number;
  proTeams: Team[];
  currentUserId?: number | undefined;
  isFirstPlace: boolean;
}

const podiumGradients = [
  "from-yellow-500/20 via-amber-500/10 to-transparent", // 1st - Gold
  "from-cyan-500/20 via-blue-500/10 to-transparent", // 2nd - Cyan/Blue
  "from-orange-500/20 via-red-500/10 to-transparent", // 3rd - Orange/Red
];

export function PodiumCard({
  member,
  rank,
  podiumIndex,
  proTeams,
  currentUserId,
  isFirstPlace,
}: PodiumCardProps) {
  const proTeam = proTeams.find((t: Team) => t.id === member.selected_team_id);
  const isCurrentUser = member.user_id === currentUserId;

  return (
    <Card
      className={`bg-gradient-to-b ${podiumGradients[podiumIndex]} border-zinc-800 overflow-hidden relative group hover:border-[#ff4655]/30 transition-all ${
        isFirstPlace ? "md:mt-0" : "md:mt-8"
      }`}
    >
      <CardContent className="p-5">
        {/* Rank Badge */}
        <div className="flex justify-center mb-4">
          <div className="bg-zinc-900/80 backdrop-blur-sm text-white text-lg font-black uppercase px-4 py-1 rounded-lg shadow-lg border border-zinc-700">
            #{rank}
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
}
