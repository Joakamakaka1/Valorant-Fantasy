"use client";

import { useQuery } from "@tanstack/react-query";
import { leaguesApi, professionalApi } from "@/lib/api";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LeagueHeader } from "./league-header";
import { LeagueRankings } from "./league-rankings";
import { RosterView } from "./roster-view";
import { LeaguePageSkeleton } from "./league-skeleton";
import { useAuth } from "@/lib/context/auth-context";
import { Info, AlertCircle } from "lucide-react";

interface LeagueViewProps {
  leagueId: number;
}

export function LeagueView({ leagueId }: LeagueViewProps) {
  const { user } = useAuth();

  // 1. Fetch League Details (Prefetched)
  const {
    data: league,
    isLoading: leagueLoading,
    error: leagueError,
  } = useQuery({
    queryKey: ["league", leagueId],
    queryFn: () => leaguesApi.getById(leagueId),
  });

  // 2. Fetch Members & Rankings (Prefetched)
  const { data: rankings = [], isLoading: rankingsLoading } = useQuery({
    queryKey: ["league-rankings", leagueId],
    queryFn: () => leaguesApi.getRankings(leagueId),
    enabled: !!league,
  });

  // 3. Find Current User's Member Info (Derived)
  const myMemberInfo = rankings.find((m) => m.user_id === user?.id);

  // 4. Fetch My Roster (Client-side, or hydrated if user landed here)
  const { data: myRoster = [], isLoading: rosterLoading } = useQuery({
    queryKey: ["league-roster", myMemberInfo?.id],
    queryFn: () => leaguesApi.getMemberRoster(myMemberInfo!.id),
    enabled: !!myMemberInfo,
  });

  // 5. Fetch All Players (Prefetched)
  const { data: allPlayers = [], isLoading: playersLoading } = useQuery({
    queryKey: ["all-players"],
    queryFn: () => professionalApi.getPlayers({ limit: 500 }),
    staleTime: 1000 * 60 * 60, // 1 hour stale time for player database
  });

  // 6. Fetch Pro Teams (Prefetched)
  const { data: proTeams = [] } = useQuery({
    queryKey: ["pro-teams"],
    queryFn: () => professionalApi.getTeams(),
    staleTime: 1000 * 60 * 60 * 24, // 24 hours stale time
  });

  // Loading State
  if (leagueLoading || (user && !myMemberInfo && rankingsLoading)) {
    return (
      <SidebarInset className="bg-[#0f1923]">
        <SiteHeader />
        <div className="p-8">
          <LeaguePageSkeleton />
        </div>
      </SidebarInset>
    );
  }

  // Error State
  if (leagueError || !league) {
    return (
      <SidebarInset className="bg-[#0f1923]">
        <SiteHeader />
        <div className="flex flex-col items-center justify-center p-20 text-center">
          <div className="bg-red-500/10 p-4 rounded-full mb-4">
            <AlertCircle className="w-12 h-12 text-red-500" />
          </div>
          <h1 className="text-2xl font-black text-white uppercase italic mb-2 tracking-tighter">
            System Failure
          </h1>
          <p className="text-zinc-500 max-w-md">
            The league protocol could not be established. This frequency is
            currenly unavailable.
          </p>
        </div>
      </SidebarInset>
    );
  }

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-8 overflow-y-auto">
        <LeagueHeader
          league={league}
          memberCount={rankings.length}
          myMemberInfo={myMemberInfo}
          proTeams={proTeams}
        />

        <Tabs defaultValue="roster" className="w-full">
          <TabsList className="bg-zinc-900/40 border border-zinc-800 w-full justify-start p-1 h-12 rounded-xl mb-4">
            <TabsTrigger
              value="roster"
              disabled={!myMemberInfo}
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all"
            >
              My Team
            </TabsTrigger>
            <TabsTrigger
              value="ranking"
              className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white px-8 font-black uppercase italic tracking-tighter rounded-lg transition-all"
            >
              Rankings
            </TabsTrigger>
          </TabsList>

          <TabsContent
            value="roster"
            className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            {myMemberInfo ? (
              <RosterView
                member={myMemberInfo}
                roster={myRoster}
                allPlayers={allPlayers}
              />
            ) : (
              <div className="p-12 text-center border-2 border-dashed border-zinc-800 rounded-xl bg-zinc-900/20">
                <Info className="w-12 h-12 text-zinc-500 mx-auto mb-4" />
                <h3 className="text-xl font-black uppercase italic text-white mb-2 tracking-tight">
                  Spectator Mode
                </h3>
                <p className="text-zinc-500">
                  You are viewing this league as a guest.
                </p>
              </div>
            )}
          </TabsContent>

          <TabsContent
            value="ranking"
            className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            <LeagueRankings
              members={rankings}
              currentUserId={user?.id}
              proTeams={proTeams}
            />
          </TabsContent>
        </Tabs>
      </div>
    </SidebarInset>
  );
}
