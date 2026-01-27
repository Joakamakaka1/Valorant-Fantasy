"use client";

import { useEffect, useState, use } from "react";
import {
  League,
  LeagueMember,
  RosterEntry,
  Player,
  Team,
  Match,
} from "@/lib/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";
import { matchesApi, leaguesApi, professionalApi } from "@/lib/api";
import { LoadingState } from "@/components/shared/loading-state";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  Users,
  Plus,
  Trash2,
  Search,
  Shield,
  User as UserIcon,
  Calendar,
  ExternalLink,
} from "lucide-react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { toast } from "sonner";
import { useAuth } from "@/lib/context/auth-context";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface RosterSlot {
  id: string;
  role: string;
  label: string;
  isStarter: boolean;
}

const ROSTER_SLOTS: RosterSlot[] = [
  { id: "d1", role: "Duelist", label: "Duelist 1", isStarter: true },
  { id: "d2", role: "Duelist", label: "Duelist 2", isStarter: true },
  { id: "c1", role: "Controller", label: "Controller 1", isStarter: true },
  { id: "c2", role: "Controller", label: "Controller 2", isStarter: true },
  { id: "i1", role: "Initiator", label: "Initiator 1", isStarter: true },
  { id: "i2", role: "Initiator", label: "Initiator 2", isStarter: true },
  { id: "s1", role: "Sentinel", label: "Sentinel 1", isStarter: true },
  { id: "s2", role: "Sentinel", label: "Sentinel 2", isStarter: true },
  { id: "b1", role: "Flex", label: "Bench 1", isStarter: false },
  { id: "b2", role: "Flex", label: "Bench 2", isStarter: false },
  { id: "b3", role: "Flex", label: "Bench 3", isStarter: false },
];

export default function LeagueDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const leagueId = parseInt(id);
  const { user } = useAuth();

  const [league, setLeague] = useState<League | null>(null);
  const [members, setMembers] = useState<LeagueMember[]>([]);
  const [myMemberInfo, setMyMemberInfo] = useState<LeagueMember | null>(null);
  const [myRoster, setMyRoster] = useState<RosterEntry[]>([]);
  const [allPlayers, setAllPlayers] = useState<Player[]>([]);
  const [proTeams, setProTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isBuying, setIsBuying] = useState(false);
  const [matches, setMatches] = useState<Match[]>([]);
  const [matchesLoading, setMatchesLoading] = useState(false);
  const [matchStatusFilter, setMatchStatusFilter] = useState("all");

  useEffect(() => {
    // If we have an ID but no user yet, we can still fetch most data
    // but we'll wait for the user to identify "myMemberInfo"
    async function loadData() {
      try {
        console.log(
          "LeagueDetailPage: Initializing data fetch for league",
          leagueId,
        );

        // Fetch data with individual error handling to avoid "all or nothing" failures
        const fetchLeague = leaguesApi.getById(leagueId).catch((err) => {
          console.error("Failed to fetch league:", err);
          return null;
        });
        const fetchRankings = leaguesApi.getRankings(leagueId).catch(() => []);
        const fetchPlayers = professionalApi
          .getPlayers({ limit: 500 })
          .catch(() => []);
        const fetchTeams = professionalApi.getTeams().catch(() => []);
        const fetchMyLeagues = leaguesApi.getMyLeagues().catch(() => []);

        const [leagueData, rankings, playersList, teams, myLeagues] =
          await Promise.all([
            fetchLeague,
            fetchRankings,
            fetchPlayers,
            fetchTeams,
            fetchMyLeagues,
          ]);

        if (!leagueData) {
          console.error("LeagueDetailPage: League object is null after fetch.");
          setLeague(null);
          setLoading(false);
          return;
        }

        setLeague(leagueData);
        setMembers(rankings);
        setAllPlayers(playersList);
        setProTeams(teams);

        // More robust identification using the specific "my leagues" endpoint
        if (user) {
          console.log("LeagueDetailPage: Current User ID", user.id);
          console.log(
            "LeagueDetailPage: My Leagues returned",
            myLeagues.length,
            "entries",
            myLeagues,
          );

          // Try to find member info in several ways to be extremely robust
          let mine = myLeagues.find((m) => m.league_id === leagueId);

          if (!mine) {
            console.log(
              "LeagueDetailPage: Not found in MyLeagues, trying rankings...",
            );
            mine = rankings.find((m) => m.user_id === user.id);
          }

          console.log("LeagueDetailPage: Final Identification Result", mine);

          if (mine) {
            setMyMemberInfo(mine);
            try {
              const roster = await leaguesApi.getMemberRoster(mine.id);
              setMyRoster(roster);
              console.log(
                "LeagueDetailPage: Roster loaded",
                roster.length,
                "players",
              );
            } catch (rErr) {
              console.error("Failed to load roster", rErr);
            }
          } else {
            console.warn(
              "LeagueDetailPage: User is NOT identified as a member of this league.",
            );
          }
        } else {
          console.log(
            "LeagueDetailPage: User object not yet available from AuthContext",
          );
        }
      } catch (error) {
        console.error("LeagueDetailPage: Load error", error);
        // We don't toast here yet to avoid spamming if it's just a transient auth lag
      } finally {
        // ALWAYS set loading to false if we have league data or a definite error
        setLoading(false);
      }
    }

    loadData();
  }, [leagueId, user?.id]); // Depend on user.id to be stable

  useEffect(() => {
    async function loadLeagueMatches() {
      setMatchesLoading(true);
      try {
        // Fetch ALL matches once
        const data = await matchesApi.getAll({});
        setMatches(data);
      } catch (error) {
        console.error("Failed to load league matches:", error);
      } finally {
        setMatchesLoading(false);
      }
    }
    loadLeagueMatches();
  }, []);

  const filteredMatches = matches.filter((match) => {
    if (matchStatusFilter === "all") return true;
    if (matchStatusFilter === "upcoming")
      return match.status === "upcoming" || match.status === "live";
    if (matchStatusFilter === "completed") return match.status === "completed";
    return true;
  });

  const handleBuyPlayer = async (slot: RosterSlot, player: Player) => {
    if (!myMemberInfo) return;

    if (player.current_price > myMemberInfo.budget) {
      toast.error("Insufficient budget!");
      return;
    }

    setIsBuying(true);
    try {
      const entry = await leaguesApi.addPlayerToRoster(myMemberInfo.id, {
        league_member_id: myMemberInfo.id,
        player_id: player.id,
        is_starter: slot.isStarter,
        is_bench: !slot.isStarter,
        role_position: slot.label,
      });

      const newBudget = myMemberInfo.budget - player.current_price;

      setMyRoster([...myRoster, entry]);
      setMyMemberInfo({
        ...myMemberInfo,
        budget: newBudget,
      });

      // Synchronize budget in calculations/rankings list
      setMembers((prev) =>
        prev.map((m) =>
          m.user_id === user?.id ? { ...m, budget: newBudget } : m,
        ),
      );

      toast.success(`Recruited ${player.name}!`);
    } catch (error: any) {
      toast.error(
        error.response?.data?.error?.message || "Failed to recruit player",
      );
    } finally {
      setIsBuying(false);
    }
  };

  const handleSellPlayer = async (rosterId: number) => {
    if (!myMemberInfo) return;

    const entry = myRoster.find((r) => r.id === rosterId);
    if (!entry) return;
    const player = allPlayers.find((p) => p.id === entry.player_id);

    try {
      await leaguesApi.removePlayerFromRoster(rosterId);
      const newRoster = myRoster.filter((r) => r.id !== rosterId);
      setMyRoster(newRoster);

      if (player) {
        const newBudget = myMemberInfo.budget + player.current_price;
        setMyMemberInfo({
          ...myMemberInfo,
          budget: newBudget,
        });

        // Synchronize budget in calculations/rankings list
        setMembers((prev) =>
          prev.map((m) =>
            m.user_id === user?.id ? { ...m, budget: newBudget } : m,
          ),
        );
      }
      toast.success("Player sold. Funds returned to budget.");
    } catch (error) {
      toast.error("Failed to sell player");
    }
  };

  const handleSelectProTeam = async (teamId: number) => {
    if (!myMemberInfo) return;
    try {
      await leaguesApi.updateMember(myMemberInfo.id, {
        selected_team_id: teamId,
      });
      setMyMemberInfo({ ...myMemberInfo, selected_team_id: teamId });
      toast.success("Professional team selected!");
    } catch (error) {
      toast.error("Failed to select team");
    }
  };

  if (loading)
    return (
      <SidebarInset className="bg-[#0f1923]">
        <SiteHeader />
        <LoadingState
          message="SYNCHRONIZING VCT PROTOCOLS..."
          fullPage
          className="bg-[#0f1923]"
        />
      </SidebarInset>
    );
  if (!league)
    return (
      <SidebarInset className="bg-[#0f1923]">
        <SiteHeader />
        <div className="p-8 text-white flex flex-col items-center justify-center min-h-[60vh] gap-4">
          <Trophy className="size-16 text-zinc-800 mb-4" />
          <h1 className="text-5xl font-black text-white uppercase tracking-tighter italic">
            League <span className="text-[#ff4655]">Not Found</span>
          </h1>
          <p className="text-zinc-400 max-w-md text-center">
            The league with ID{" "}
            <span className="text-white font-mono">{leagueId}</span> could not
            be retrieved. This might be due to a synchronization delay or an
            incorrect ID.
          </p>
          <div className="flex gap-4 mt-4">
            <Button
              onClick={() => window.location.reload()}
              className="bg-zinc-800 hover:bg-zinc-700"
            >
              Retry Synchronization
            </Button>
            <Link href="/dashboard/leagues/join">
              <Button variant="outline" className="border-zinc-800">
                Back to League Hub
              </Button>
            </Link>
          </div>
        </div>
      </SidebarInset>
    );

  const getPlayerInSlot = (slotLabel: string) => {
    const entry = myRoster.find((r) => r.role_position === slotLabel);
    if (!entry) return null;
    return {
      entry,
      player: allPlayers.find((p) => p.id === entry.player_id),
    };
  };

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-8 p-8 overflow-y-auto">
        {/* League Header */}
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
                <Users className="size-4 text-[#ff4655]" /> {members.length}/
                {league.max_teams} Players
              </span>
              <span className="flex items-center gap-1 uppercase font-black text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded border border-zinc-700">
                INVITE CODE: {league.invite_code}
              </span>
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
                        proTeams.find(
                          (t) => t.id === myMemberInfo.selected_team_id,
                        )?.logo_url || ""
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
                      myMemberInfo?.selected_team_id?.toString() ||
                      "placeholder"
                    }
                    onValueChange={(val) =>
                      val !== "placeholder" &&
                      handleSelectProTeam(parseInt(val))
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
                          className="hover:bg-zinc-900 focus:bg-zinc-900 data-[state=checked] data-[state=checked]:text-[#ff4655] font-black uppercase italic tracking-tight p-4 transition-colors cursor-pointer border-b border-zinc-900/50 last:border-none"
                        >
                          <div className="flex items-center gap-4 pl-1">
                            <div className="size-8 rounded bg-black/40 flex items-center justify-center border border-zinc-800 group-hover:border-zinc-700">
                              {t.logo_url ? (
                                <img
                                  src={t.logo_url}
                                  className="size-5 object-contain "
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

        <Tabs defaultValue="roster" className="w-full">
          <TabsList className="bg-zinc-950 border border-zinc-800 w-full justify-start p-1 h-12 rounded-xl mb-4">
            <TabsTrigger
              value="roster"
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

          {/* Roster Management View */}
          <TabsContent
            value="roster"
            className="mt-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
            <div className="grid gap-6 md:grid-cols-2">
              <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden relative group">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-25 transition-opacity">
                  <h2 className="text-8xl font-black italic">BUDGET</h2>
                </div>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs uppercase font-black tracking-[0.2em] text-zinc-500">
                    Available Capital
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <span className="text-5xl font-black text-[#ff4655] tracking-tighter italic">
                    €
                    {myMemberInfo?.budget !== undefined
                      ? myMemberInfo.budget.toFixed(1)
                      : "---"}
                    M
                  </span>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-zinc-900 to-zinc-950 border-zinc-800 overflow-hidden relative group">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-25 transition-opacity">
                  <h2 className="text-8xl font-black italic">VALUE</h2>
                </div>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs uppercase font-black tracking-[0.2em] text-zinc-500">
                    Roster Net Worth
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <span className="text-5xl font-black text-white tracking-tighter italic">
                    €
                    {myRoster
                      .reduce((sum, entry) => {
                        const p = allPlayers.find(
                          (p) => p.id === entry.player_id,
                        );
                        return sum + (p?.current_price || 0);
                      }, 0)
                      .toFixed(1)}
                    M
                  </span>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {ROSTER_SLOTS.map((slot) => {
                const slotData = getPlayerInSlot(slot.label);
                return (
                  <Card
                    key={slot.id}
                    className="bg-zinc-900/40 border-zinc-800 relative overflow-hidden group min-h-[160px] hover:border-[#ff4655]/30 transition-all backdrop-blur-sm flex flex-col p-0 h-full"
                  >
                    {slotData ? (
                      <div className="p-4 flex flex-1 flex-col bg-gradient-to-t from-zinc-950/50 to-transparent h-full">
                        <div className="flex justify-between items-start">
                          <div className="bg-[#ff4655] text-white text-[8px] font-black uppercase px-2 py-0.5 rounded shadow-[0_2px_10px_rgba(255,70,85,0.4)]">
                            {slot.label}
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-6 text-zinc-600 hover:text-red-500 hover:bg-red-500/10 rounded-full"
                            onClick={() => handleSellPlayer(slotData.entry.id)}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                        <div className="flex flex-1 flex-col items-center justify-center min-h-0 py-4">
                          <div className="size-16 rounded-full bg-zinc-800 flex items-center justify-center mb-2 border-2 border-zinc-700 group-hover:border-[#ff4655]/50 transition-colors shadow-inner overflow-hidden relative">
                            {slotData.player?.team?.logo_url ? (
                              <img
                                src={slotData.player.team.logo_url}
                                alt={slotData.player.team.name}
                                className="size-full object-cover opacity-40 absolute inset-0"
                              />
                            ) : null}
                            <UserIcon className="size-8 text-zinc-500 relative z-10" />
                          </div>
                          <span className="font-black text-white uppercase italic text-center leading-tight tracking-tight text-sm">
                            {slotData.player?.name}
                          </span>
                          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
                            {slotData.player?.team?.name || "Independent"} •{" "}
                            {slotData.player?.region}
                          </span>
                        </div>
                        <div className="mt-auto flex justify-between w-full border-t border-zinc-800/50 pt-2 bg-zinc-950/30 p-2 rounded-lg">
                          <div className="flex flex-col">
                            <span className="text-[7px] text-zinc-500 uppercase font-black">
                              FPts ({slotData.player?.matches_played} GP)
                            </span>
                            <span className="text-xs font-black text-emerald-400 italic">
                              {slotData.player?.points}
                            </span>
                          </div>
                          <div className="flex flex-col items-end">
                            <span className="text-[7px] text-zinc-500 uppercase font-black">
                              Contract
                            </span>
                            <span className="text-xs font-black text-white italic">
                              €{slotData.player?.current_price}M
                            </span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <Dialog>
                        <DialogTrigger asChild>
                          <div className="flex-1 flex items-center justify-center p-4">
                            <button className="aspect-square w-full max-w-[120px] flex flex-col items-center justify-center gap-2 hover:bg-[#ff4655]/5 transition-all text-zinc-700 hover:text-[#ff4655] group/btn border-2 border-dashed border-zinc-800/50 rounded-xl">
                              <Plus className="size-8 group-hover/btn:scale-110 transition-transform" />
                              <span className="text-[10px] uppercase font-black tracking-widest text-center px-1">
                                {slot.label}
                              </span>
                              <span className="text-[8px] text-zinc-800 font-black uppercase text-center px-2">
                                Click to Scout
                              </span>
                            </button>
                          </div>
                        </DialogTrigger>
                        <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-[480px] p-0 overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                          <div className="bg-[#ff4655] p-6">
                            <DialogHeader>
                              <DialogTitle className="uppercase italic font-black text-3xl text-white tracking-tighter">
                                Scout{" "}
                                <span className="text-zinc-900">
                                  {slot.role}
                                </span>
                              </DialogTitle>
                            </DialogHeader>
                          </div>
                          <div className="flex flex-col gap-4 p-6">
                            <div className="relative">
                              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
                              <Input
                                placeholder="Search VCT database..."
                                className="pl-10 bg-zinc-900 border-zinc-800 text-white font-bold"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                              />
                            </div>
                            <div className="max-h-[350px] overflow-y-auto pr-1 custom-scrollbar">
                              <Table>
                                <TableBody>
                                  {allPlayers
                                    .filter((p) => p.role === slot.role)
                                    .filter((p) =>
                                      p.name
                                        .toLowerCase()
                                        .includes(searchQuery.toLowerCase()),
                                    )
                                    .filter(
                                      (p) =>
                                        !myRoster.some(
                                          (r) => r.player_id === p.id,
                                        ),
                                    )
                                    .map((player) => (
                                      <TableRow
                                        key={player.id}
                                        className="border-zinc-800 hover:bg-zinc-900 group/row"
                                      >
                                        <TableCell className="py-3">
                                          <div className="flex flex-col">
                                            <span className="font-black text-sm uppercase italic">
                                              {player.name}
                                            </span>
                                            <span className="text-[10px] text-zinc-500 font-bold uppercase">
                                              {player.team?.name} •{" "}
                                              {player.region}
                                            </span>
                                          </div>
                                        </TableCell>
                                        <TableCell className="text-right py-3">
                                          <Button
                                            size="sm"
                                            className="bg-zinc-800 hover:bg-[#ff4655] h-8 text-[11px] uppercase font-black italic transition-all group-hover/row:scale-105"
                                            onClick={() =>
                                              handleBuyPlayer(slot, player)
                                            }
                                            disabled={isBuying}
                                          >
                                            €{player.current_price}M
                                          </Button>
                                        </TableCell>
                                      </TableRow>
                                    ))}
                                </TableBody>
                              </Table>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                    )}
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {/* Ranking View */}
          <TabsContent
            value="ranking"
            className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500"
          >
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
                    {members.map((member, index) => (
                      <TableRow
                        key={member.id}
                        className="border-zinc-800 group/rank"
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
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-emerald-400 font-black text-2xl italic tracking-tighter">
                          {member.total_points.toFixed(1)}
                        </TableCell>
                        <TableCell className="text-right text-zinc-100 font-black italic text-lg">
                          €
                          {member.team_value
                            ? member.team_value.toFixed(1)
                            : "0.0"}
                          M
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Matches View */}
        </Tabs>
      </div>
    </SidebarInset>
  );
}
