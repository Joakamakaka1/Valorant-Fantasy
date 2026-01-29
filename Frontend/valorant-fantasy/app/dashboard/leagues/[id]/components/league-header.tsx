"use client";

import { Trophy, Shield, Copy, Check, Users } from "lucide-react";
import { useState } from "react";
import { League, LeagueMember, Team } from "@/lib/types";
import { toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { leaguesApi } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

interface LeagueHeaderProps {
  league: League;
  memberCount: number;
  myMemberInfo?: LeagueMember | undefined;
  proTeams: Team[];
}

export function LeagueHeader({
  league,
  memberCount,
  myMemberInfo,
  proTeams,
}: LeagueHeaderProps) {
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const copyInvite = () => {
    navigator.clipboard.writeText(league.invite_code);
    setCopied(true);
    toast.success("Invite code copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSelectProTeam = async (teamId: number) => {
    if (!myMemberInfo) return;
    try {
      await leaguesApi.updateMember(myMemberInfo.id, {
        selected_team_id: teamId,
      });
      toast.success("Professional team selected!");
      queryClient.invalidateQueries({
        queryKey: ["league-rankings", league.id],
      });
      queryClient.invalidateQueries({ queryKey: ["my-leagues"] });
    } catch (error) {
      toast.error("Failed to select team");
    }
  };

  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-zinc-800 pb-8">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="bg-[#ff4655] p-2 rounded-lg shadow-[0_0_20px_rgba(255,70,85,0.3)]">
            <Trophy className="size-6 text-white" />
          </div>
          <h1 className="text-5xl font-black text-white uppercase tracking-tighter italic">
            {league.name}
          </h1>
        </div>
        <div className="flex items-center gap-4 text-sm text-zinc-400 mt-2">
          <span className="flex items-center gap-1 font-bold">
            <Users className="size-4 text-[#ff4655]" /> {memberCount}/
            {league.max_teams} Players
          </span>
          <button
            onClick={copyInvite}
            className="flex items-center gap-2 uppercase font-black text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded border border-zinc-700 hover:bg-zinc-700 hover:text-white transition-colors cursor-pointer"
          >
            INVITE CODE:{" "}
            <span className="text-white">{league.invite_code}</span>
            {copied ? (
              <Check className="size-3 text-green-500" />
            ) : (
              <Copy className="size-3" />
            )}
          </button>
        </div>
      </div>

      <div className="relative">
        <div className="flex flex-col sm:flex-row items-center gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-xl backdrop-blur-xl shadow-2xl">
          <div className="flex items-center gap-4 flex-1 w-full">
            <div className="size-16 rounded-xl bg-zinc-950 flex items-center justify-center border-2 border-zinc-800 shadow-2xl overflow-hidden relative group/logo">
              <div className="absolute inset-0 bg-gradient-to-br from-[#ff4655]/10 to-transparent opacity-0 group-hover/logo:opacity-100 transition-opacity"></div>
              {myMemberInfo?.selected_team_id ? (
                <img
                  src={
                    proTeams.find((t) => t.id === myMemberInfo.selected_team_id)
                      ?.logo_url || ""
                  }
                  alt="Team Logo"
                  className="size-12 object-contain relative z-10 transition-transform group-hover/logo:scale-110 "
                />
              ) : (
                <Shield className="size-8 text-zinc-800 relative z-10" />
              )}
            </div>
            <div className="flex flex-col flex-1">
              <span className="text-[10px] uppercase text-zinc-500 font-black tracking-[0.2em] mb-1">
                Representing Organization
              </span>
              <Select
                value={
                  myMemberInfo?.selected_team_id?.toString() || "placeholder"
                }
                disabled={!myMemberInfo}
                onValueChange={(val) =>
                  val !== "placeholder" && handleSelectProTeam(parseInt(val))
                }
              >
                <SelectTrigger className="w-full sm:w-[280px] h-10 bg-transparent border-none p-0 text-white text-sm font-black uppercase italic tracking-tighter hover:text-[#ff4655] transition-colors focus:ring-0 shadow-none pl-1">
                  <SelectValue placeholder="CLAIM YOUR ORG" />
                </SelectTrigger>
                <SelectContent
                  position="popper"
                  className="bg-zinc-950 border-zinc-800 text-white min-w-[280px] max-h-[300px]"
                  sideOffset={8}
                >
                  <SelectItem
                    value="placeholder"
                    disabled
                    className="text-zinc-600 font-bold py-3"
                  >
                    SELECT PROFESSIONAL TEAM
                  </SelectItem>
                  {proTeams.map((t) => (
                    <SelectItem
                      key={t.id}
                      value={t.id.toString()}
                      className="hover:bg-zinc-900 focus:bg-zinc-900 data-[state=checked]:text-[#ff4655] font-black uppercase italic tracking-tight p-4 transition-colors cursor-pointer border-b border-zinc-900/50 last:border-none"
                    >
                      <div className="flex items-center gap-4 pl-1">
                        <div className="size-8 rounded bg-black/40 flex items-center justify-center border border-zinc-800 group-hover:border-zinc-700">
                          {t.logo_url ? (
                            <img
                              src={t.logo_url}
                              className="size-5 object-contain"
                              alt=""
                            />
                          ) : (
                            <Shield className="size-4 text-zinc-800" />
                          )}
                        </div>
                        <span className="text-sm">{t.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="hidden sm:block w-px h-12 bg-zinc-800 mx-2"></div>
          <div className="flex flex-col items-center sm:items-end justify-center px-4">
            <span className="text-[10px] uppercase text-zinc-500 font-bold tracking-widest leading-none mb-1 text-center sm:text-right">
              Organization Status
            </span>
            <span
              className={`text-xs font-black uppercase tracking-tighter italic ${myMemberInfo?.selected_team_id ? "text-emerald-400" : "text-amber-500"}`}
            >
              {myMemberInfo?.selected_team_id
                ? "VERIFIED CONTRACT"
                : "UNASSIGNED AGENT"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
