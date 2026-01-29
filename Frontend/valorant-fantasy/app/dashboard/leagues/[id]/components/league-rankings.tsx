"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { LeagueMember } from "@/lib/types";

interface LeagueRankingsProps {
  members: LeagueMember[];
  currentUserId?: number | undefined;
}

export function LeagueRankings({
  members,
  currentUserId,
}: LeagueRankingsProps) {
  // Sort members by total points descending
  const sortedMembers = [...members].sort(
    (a, b) => b.total_points - a.total_points,
  );

  return (
    <Card className="bg-zinc-900/50 border-zinc-800 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="uppercase italic font-black">
          League Leaderboard
        </CardTitle>
        <CardDescription className="font-bold">
          Track the performance and budget of all participants.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="w-16 uppercase font-black text-xs">
                Pos
              </TableHead>
              <TableHead className="uppercase font-black text-xs text-zinc-500">
                Player Identity
              </TableHead>
              <TableHead className="text-right uppercase font-black text-xs">
                Total Points
              </TableHead>
              <TableHead className="text-right uppercase font-black text-xs">
                Team Value
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedMembers.map((member, index) => {
              const isCurrentUser = member.user_id === currentUserId;
              return (
                <TableRow
                  key={member.id}
                  className={`border-zinc-800 group/rank ${
                    isCurrentUser ? "bg-white/5" : ""
                  }`}
                >
                  <TableCell className="font-black text-2xl italic text-zinc-700 group-hover/rank:text-[#ff4655] transition-colors">
                    {(index + 1).toString().padStart(2, "0")}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-black text-white uppercase italic text-lg leading-tight pb-2">
                        {member.team_name}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[#ff4655] font-black uppercase tracking-wider bg-[#ff4655]/10 px-2 py-0.5 rounded">
                          @{member.user?.username || "SYNCING..."}
                        </span>
                        {member.is_admin && (
                          <span className="text-[10px] text-zinc-500 font-bold border border-zinc-800 px-1 rounded">
                            ADMIN
                          </span>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-emerald-400 font-black text-2xl italic tracking-tighter">
                    {member.total_points.toFixed(1)}
                  </TableCell>
                  <TableCell className="text-right text-zinc-100 font-black italic text-lg">
                    €
                    {member.team_value
                      ? (member.team_value / 1000000).toFixed(1)
                      : "0.0"}
                    M
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
