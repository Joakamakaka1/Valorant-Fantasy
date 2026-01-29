"use client";

import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { SidebarInset } from "@/components/ui/sidebar";
import { professionalApi } from "@/lib/api";
import { useAuth } from "@/lib/context/auth-context";
import { useQuery } from "@tanstack/react-query";
import {
  Play,
  ShieldAlert,
  Swords,
  TrendingUp,
  Trophy,
  Users,
} from "lucide-react";
import Link from "next/link";

export function DashboardView() {
  const { user } = useAuth();

  // Fetch players (should be prefetched on server)
  const { data: allPlayers = [] } = useQuery({
    queryKey: ["all-players-db"],
    queryFn: () => professionalApi.getPlayers({ limit: 500 }),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Sort by points descending and take top 3
  const topPlayers = [...allPlayers]
    .sort((a, b) => b.points - a.points)
    .slice(0, 3);

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col p-4 md:p-8 overflow-y-auto gap-8">
        {/* HERO SECTION */}
        <div className="relative w-full min-h-[350px] md:min-h-[450px] rounded-2xl md:rounded-3xl overflow-hidden group shadow-xl border border-zinc-800 flex items-center transition-all hover:shadow-2xl hover:border-zinc-700">
          {/* Background Gradient/Image */}
          <div className="absolute inset-0 bg-[url('/fondo_overview.webp')] bg-cover bg-center md:bg-[center_top_25%] transition-transform duration-700 group-hover:scale-105 opacity-80" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0f1923] via-[#0f1923]/95 md:via-[#0f1923]/90 to-transparent" />
          <div className="relative h-full flex flex-col justify-center p-6 sm:p-8 md:p-16 max-w-3xl gap-4 md:gap-6">
            <div className="flex items-center gap-2 md:gap-3 flex-wrap">
              <span className="bg-[#ff4655] text-white px-2.5 md:px-3 py-1 text-[9px] md:text-[10px] font-black uppercase tracking-widest rounded-sm shadow-[0_0_10px_rgba(255,70,85,0.4)]">
                New Season
              </span>
              <span className="text-zinc-300 text-[10px] md:text-xs font-bold uppercase tracking-[0.15em] md:tracking-[0.2em]">
                Episode 1: DEFIANCE
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-black text-white italic uppercase tracking-tighter leading-[0.9] drop-shadow-xl">
              Build Your <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#ff4655] to-white pr-2">
                Dream Team
              </span>
            </h1>
            <p className="text-zinc-300 text-sm sm:text-base md:text-lg font-medium max-w-lg leading-relaxed drop-shadow-md">
              Compete against friends in the ultimate Valorant fantasy league.
              Scout players, manage your budget, and dominate the leaderboard.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 md:gap-4 pt-2 md:pt-4">
              <Link href="/dashboard/leagues/join" className="w-full sm:w-auto">
                <Button
                  size="lg"
                  className="w-full sm:w-auto bg-[#ff4655] hover:bg-[#ff4655]/90 text-white font-black italic uppercase tracking-wider px-6 md:px-8 py-5 md:py-6 text-base md:text-lg rounded-xl shadow-[0_4px_20px_rgba(255,70,85,0.4)] transition-all hover:-translate-y-0.5"
                >
                  <Play className="fill-current size-3.5" />
                  Play Now
                </Button>
              </Link>
              <Link href="/dashboard/leagues/join" className="w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full sm:w-auto border-white/20 text-white hover:bg-white/10 font-bold uppercase tracking-wider px-6 md:px-8 py-5 md:py-6 text-xs md:text-sm rounded-xl backdrop-blur-sm transition-all hover:-translate-y-0.5"
                >
                  How to Play
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* NAVIGATION GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* CARD 1: LEAGUES */}
          <Link
            href="/dashboard/leagues/join"
            className="group relative h-[240px] rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-900/40 hover:border-[#ff4655]/50 transition-all shadow-lg hover:shadow-[#ff4655]/10"
          >
            <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(68,68,68,.2)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] bg-[position:-100%_0,0_0] bg-no-repeat transition-[background-position_0s_ease] hover:bg-[position:200%_0,0_0] hover:duration-[1500ms]" />
            <div className="absolute top-0 right-0 p-6 opacity-20 group-hover:opacity-40 transition-opacity">
              <Trophy className="size-32 text-zinc-500 group-hover:text-[#ff4655] rotate-12 transition-colors" />
            </div>
            <div className="relative h-full flex flex-col justify-end p-6">
              <div className="size-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-[#ff4655] transition-colors shadow-lg">
                <Trophy className="size-6 text-white" />
              </div>
              <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter mb-1">
                My Leagues
              </h3>
              <p className="text-zinc-400 text-sm font-medium">
                Manage your teams and check standings.
              </p>
            </div>
          </Link>

          {/* CARD 2: PLAYERS/DATABASE */}
          <Link
            href="/dashboard/database/players"
            className="group relative h-[240px] rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-900/40 hover:border-purple-500/50 transition-all shadow-lg hover:shadow-purple-500/10"
          >
            <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(68,68,68,.2)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] bg-[position:-100%_0,0_0] bg-no-repeat transition-[background-position_0s_ease] hover:bg-[position:200%_0,0_0] hover:duration-[1500ms]" />
            <div className="absolute top-0 right-0 p-6 opacity-20 group-hover:opacity-40 transition-opacity">
              <Users className="size-32 text-zinc-500 group-hover:text-purple-500 -rotate-12 transition-colors" />
            </div>
            <div className="relative h-full flex flex-col justify-end p-6">
              <div className="size-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-purple-500 transition-colors shadow-lg">
                <Users className="size-6 text-white" />
              </div>
              <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter mb-1">
                Player Database
              </h3>
              <p className="text-zinc-400 text-sm font-medium">
                Scout active pros and market values.
              </p>
            </div>
          </Link>

          {/* CARD 3: MATCHES */}
          <Link
            href="/dashboard/database/matches"
            className="group relative h-[240px] rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-900/40 hover:border-emerald-500/50 transition-all shadow-lg hover:shadow-emerald-500/10"
          >
            <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(68,68,68,.2)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] bg-[position:-100%_0,0_0] bg-no-repeat transition-[background-position_0s_ease] hover:bg-[position:200%_0,0_0] hover:duration-[1500ms]" />
            <div className="absolute top-0 right-0 p-6 opacity-20 group-hover:opacity-40 transition-opacity">
              <Swords className="size-32 text-zinc-500 group-hover:text-emerald-500 rotate-6 transition-colors" />
            </div>
            <div className="relative h-full flex flex-col justify-end p-6">
              <div className="size-12 bg-zinc-800 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-500 transition-colors shadow-lg">
                <Swords className="size-6 text-white" />
              </div>
              <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter mb-1">
                Match Center
              </h3>
              <p className="text-zinc-400 text-sm font-medium">
                Live scores and upcoming VCT schedule.
              </p>
            </div>
          </Link>
        </div>

        {/* BOTTOM SECTION - FEATURED or NEWS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-8">
          <div className="lg:col-span-2 bg-zinc-900/40 border border-zinc-800/50 rounded-2xl p-8 flex flex-col gap-6  transition-colors">
            <div className="flex items-center gap-3 text-[#ff4655]">
              <div className="p-2 rounded-lg">
                <TrendingUp className="size-6" />
              </div>
              <span className="text-lg font-black uppercase tracking-wide">
                Top Players
              </span>
            </div>
            <div className="space-y-4">
              {topPlayers.length > 0 ? (
                topPlayers.map((player, i) => (
                  <div
                    key={player.id}
                    className="flex items-center justify-between bg-zinc-950/20 p-4 rounded-xl border border-zinc-800/50 transition-all hover:border-[#ff4655]/50 hover:shadow-lg group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="size-12 rounded-xl bg-zinc-950 border border-zinc-700 overflow-hidden relative flex items-center justify-center shadow-inner group-hover:border-[#ff4655]/30 transition-colors ">
                        {player.team?.logo_url ? (
                          <img
                            src={player.team.logo_url}
                            alt={player.team.name}
                            className="size-8 object-contain opacity-80 group-hover:opacity-100 transition-opacity"
                          />
                        ) : (
                          <Users className="size-6 text-zinc-500" />
                        )}
                        <div className="absolute top-0 right-0 bg-[#ff4655] text-white text-[10px] font-black px-1.5 py-0.5 rounded-bl shadow-sm">
                          #{i + 1}
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="font-black text-white text-lg uppercase italic leading-none group-hover:text-[#ff4655] transition-colors">
                          {player.name}
                        </span>

                        {/* Contenedor del Equipo y el Rol */}
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-zinc-400 uppercase font-bold tracking-wide">
                            {player.team?.name || "Free Agent"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className="text-emerald-400 text-xl font-black italic tracking-tight">
                        {player.points}
                        <span className="text-sm text-emerald-500/70 not-italic">
                          pts
                        </span>
                      </span>
                      <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">
                        €{player.current_price}M
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center py-12 text-zinc-500 text-sm uppercase font-bold bg-zinc-950/30 rounded-xl border border-dashed border-zinc-800">
                  Syncing Market Data...
                </div>
              )}
            </div>
          </div>

          <div className="bg-zinc-900/40 border border-zinc-800/50 rounded-2xl p-8 flex flex-col gap-6 transition-colors">
            <div className="flex items-center gap-3 text-zinc-400">
              <div className="p-2 bg-zinc-800/50 rounded-lg">
                <ShieldAlert className="size-6" />
              </div>
              <span className="text-lg font-black uppercase tracking-wide text-zinc-300">
                System Status
              </span>
            </div>
            <div className="h-full flex flex-col justify-center items-center text-center gap-4 rounded-xl p-6">
              <div className="relative">
                <div className="size-4 bg-emerald-500 rounded-full animate-ping absolute inset-0 opacity-75" />
                <div className="size-4 bg-emerald-500 rounded-full relative shadow-[0_0_20px_#10b981]" />
              </div>
              <div className="space-y-1">
                <span className="text-white font-black text-xl italic tracking-tight block">
                  All Systems Operational
                </span>
                <p className="text-sm text-zinc-500 font-medium">
                  Live VLR.gg Data Sync
                </p>
              </div>
              <div className="flex gap-8 text-xs text-zinc-500 font-mono pt-2">
                <div className="flex flex-col items-center">
                  <span className="text-zinc-600 font-bold uppercase">
                    Latency
                  </span>
                  <span className="text-emerald-500">24ms</span>
                </div>
                <div className="flex flex-col items-center">
                  <span className="text-zinc-600 font-bold uppercase">
                    Region
                  </span>
                  <span className="text-white">EU-West</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SidebarInset>
  );
}
