"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Plus,
  Trash2,
  Search,
  User as UserIcon,
  AlertTriangle,
  ArrowUpDown,
  ChevronDown,
  ChevronUp,
  X,
} from "lucide-react";
import { LeagueMember, RosterEntry, Player } from "@/lib/types";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { leaguesApi } from "@/lib/api";

// Role colors matching the trading card aesthetic
const ROLE_STYLES = {
  Duelist: {
    gradient: "from-red-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-red-500/50",
    text: "text-red-400",
  },
  Controller: {
    gradient: "from-purple-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-purple-500/50",
    text: "text-purple-400",
  },
  Initiator: {
    gradient: "from-amber-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-amber-500/50",
    text: "text-amber-400",
  },
  Sentinel: {
    gradient: "from-blue-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-blue-500/50",
    text: "text-blue-400",
  },
  Flex: {
    gradient: "from-emerald-500/30 via-zinc-900/50 to-zinc-900",
    border: "border-t-emerald-500/50",
    text: "text-emerald-400",
  },
};

interface RosterViewProps {
  member: LeagueMember;
  roster: RosterEntry[];
  allPlayers: Player[];
}

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

export function RosterView({ member, roster, allPlayers }: RosterViewProps) {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  // State for Scout Dialog
  const [openDialogSlot, setOpenDialogSlot] = useState<string | null>(null);
  const [scoutSort, setScoutSort] = useState<{
    key: "points" | "current_price";
    direction: "asc" | "desc";
  }>({ key: "current_price", direction: "desc" });

  const toggleScoutSort = (key: "points" | "current_price") => {
    setScoutSort((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc",
    }));
  };

  // State for Release Confirmation Dialog
  const [playerToRelease, setPlayerToRelease] = useState<{
    id: number;
    name: string;
  } | null>(null);

  const getPlayerInSlot = (slotLabel: string) => {
    const entry = roster.find((r) => r.role_position === slotLabel);
    if (!entry) return null;
    return {
      entry,
      player: allPlayers.find((p) => p.id === entry.player_id),
    };
  };

  const handleBuyPlayer = async (slot: RosterSlot, player: Player) => {
    if (member.budget < player.current_price) {
      toast.error("Insufficient funds for this transaction");
      return;
    }

    setIsProcessing(true);
    try {
      await leaguesApi.addPlayerToRoster(member.id, {
        league_member_id: member.id,
        player_id: player.id,
        is_starter: slot.isStarter,
        role_position: slot.label,
      });

      toast.success(`Signed ${player.name} to roster`);
      setOpenDialogSlot(null);

      queryClient.invalidateQueries({ queryKey: ["league-roster", member.id] });
      queryClient.invalidateQueries({
        queryKey: ["league-rankings", member.league_id],
      });
      queryClient.invalidateQueries({ queryKey: ["my-leagues"] });
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Failed to sign player");
    } finally {
      setIsProcessing(false);
    }
  };

  const confirmReleasePlayer = (rosterId: number, playerName: string) => {
    setPlayerToRelease({ id: rosterId, name: playerName });
  };

  const handleSellPlayer = async () => {
    if (!playerToRelease) return;

    setIsProcessing(true);
    try {
      await leaguesApi.removePlayerFromRoster(playerToRelease.id);
      toast.success(`Released ${playerToRelease.name} from contract`);

      queryClient.invalidateQueries({ queryKey: ["league-roster", member.id] });
      queryClient.invalidateQueries({
        queryKey: ["league-rankings", member.league_id],
      });
      queryClient.invalidateQueries({ queryKey: ["my-leagues"] });
      setPlayerToRelease(null);
    } catch (error: any) {
      toast.error("Failed to release player");
    } finally {
      setIsProcessing(false);
    }
  };

  const rosterValue = roster.reduce((sum, entry) => {
    const p = allPlayers.find((p) => p.id === entry.player_id);
    return sum + (p?.current_price || 0);
  }, 0);

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
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
              €{member.budget.toFixed(1)}M
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
              €{rosterValue.toFixed(1)}M
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Roster Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {ROSTER_SLOTS.map((slot) => {
          const slotData = getPlayerInSlot(slot.label);
          const isOpen = openDialogSlot === slot.id;

          return (
            <Card
              key={slot.id}
              className="bg-zinc-900/40 border-zinc-800 relative overflow-hidden group min-h-[160px] hover:border-[#ff4655]/30 transition-all backdrop-blur-sm flex flex-col p-0 h-full"
            >
              {slotData ? (
                // FILLED SLOT - Trading Card Design
                (() => {
                  const roleStyle =
                    ROLE_STYLES[
                      slotData.player?.role as keyof typeof ROLE_STYLES
                    ] || ROLE_STYLES.Flex;
                  return (
                    <div className="p-0 flex flex-1 flex-col h-full">
                      {/* Role Badge - Top with corner decorations */}
                      <div className="relative border-b-2 border-zinc-800/50">
                        <div
                          className={`absolute inset-0 bg-gradient-to-b ${roleStyle.gradient} opacity-60`}
                        />
                        <div className="relative px-3 py-2 flex items-center justify-between">
                          {/* Left corner decoration */}
                          <div
                            className={`w-3 h-0.5 ${roleStyle.border.replace("border-t-", "bg-")}`}
                          />

                          <p
                            className={`text-[12px] font-black uppercase tracking-widest ${roleStyle.text}`}
                          >
                            {slotData.player?.role}
                          </p>

                          {/* Right corner decoration */}
                          <div
                            className={`w-3 h-0.5 ${roleStyle.border.replace("border-t-", "bg-")}`}
                          />
                        </div>
                        {/* Trash button in top-right corner */}
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute top-1 right-1 size-6 text-zinc-600 hover:text-red-500 hover:bg-red-500/10 rounded-full z-10"
                          onClick={() =>
                            confirmReleasePlayer(
                              slotData.entry.id,
                              slotData.player?.name || "Player",
                            )
                          }
                          disabled={isProcessing}
                        >
                          <X className="size-4.5" />
                        </Button>
                      </div>

                      {/* Player Image Section */}
                      <div
                        className={`relative h-60 bg-gradient-to-b ${roleStyle.gradient} flex items-center justify-center overflow-hidden`}
                      >
                        {/* Player Image */}
                        <img
                          src={
                            slotData.player?.photo_url
                              ? `/api/proxy/image?url=${encodeURIComponent(slotData.player.photo_url)}`
                              : "/fondo_overview.jpg"
                          }
                          alt={slotData.player?.name}
                          className="absolute inset-0 w-full h-full object-cover z-0"
                        />

                        {/* Team Logo Watermark */}
                        {slotData.player?.team?.logo_url && (
                          <div className="absolute bottom-2 right-2 size-7 rounded bg-zinc-900/80 border border-zinc-800 p-1 backdrop-blur-sm z-20">
                            <img
                              src={slotData.player.team.logo_url}
                              alt={slotData.player.team.name}
                              className="size-full object-contain opacity-60"
                            />
                          </div>
                        )}

                        {/* Price Badge */}
                        <div className="absolute bottom-0 left-0 right-0 bg-zinc-950/90 backdrop-blur-sm border-t border-zinc-800 py-1.5">
                          <p className="text-xs font-black text-white italic text-center">
                            €{slotData.player?.current_price.toFixed(1)}M
                          </p>
                        </div>
                      </div>

                      {/* Player Info Section */}
                      <div className="p-3 bg-zinc-950 flex-1 flex flex-col justify-end">
                        {/* Player Name */}
                        <h3 className="text-[16px] font-black text-white uppercase italic leading-tight mb-1 truncate">
                          {slotData.player?.name}
                        </h3>

                        {/* Team Name */}
                        <div className="flex items-center gap-1 mb-2">
                          <p className="text-[10px] text-zinc-500 font-bold uppercase truncate flex-1">
                            {slotData.player?.team?.name || "Independent"}
                          </p>
                        </div>

                        {/* Stats */}
                        <div className="flex items-center justify-between text-[10px]">
                          <div className="flex flex-col">
                            <span className="text-zinc-500 font-black uppercase mb-0.5">
                              Points
                            </span>
                            <span className="text-[14px] text-emerald-400 font-black italic">
                              {slotData.player?.points.toFixed(1)}
                            </span>
                          </div>
                          <div className="flex flex-col items-end">
                            <span className="text-zinc-500 font-black uppercase mb-0.5">
                              Matches
                            </span>
                            <span className="text-[14px] text-white font-black italic">
                              {slotData.player?.matches_played}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()
              ) : (
                // EMPTY SLOT - SCOUT BUTTON
                <Dialog
                  open={isOpen}
                  onOpenChange={(open) =>
                    setOpenDialogSlot(open ? slot.id : null)
                  }
                >
                  <DialogTrigger asChild>
                    <div className="flex-1 flex items-center justify-center p-4 cursor-pointer">
                      <button className="aspect-square w-full max-w-[120px] flex flex-col items-center justify-center gap-2 hover:bg-[#ff4655]/5 transition-all text-zinc-700 hover:text-[#ff4655] group/btn border-2 border-dashed border-zinc-800/50 rounded-xl">
                        <Plus className="size-8 group-hover/btn:scale-110 transition-transform" />
                        <span className="text-[10px] uppercase font-black text-zinc-500 tracking-widest text-center px-1">
                          {slot.label}
                        </span>
                        <span className="text-[8px] text-zinc-700 font-black uppercase text-center px-2">
                          Click to Scout
                        </span>
                      </button>
                    </div>
                  </DialogTrigger>
                  <DialogContent className="bg-zinc-950 border-zinc-800 text-white w-[92vw] sm:w-[95vw] max-w-[600px] max-h-[90vh] p-0 overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] rounded-2xl sm:rounded-lg">
                    <div className="bg-[#ff4655] p-5 sm:p-6 pt-10 sm:pt-6">
                      <DialogHeader>
                        <DialogTitle className="uppercase italic font-black text-xl sm:text-2xl md:text-3xl text-white tracking-tighter">
                          Scout{" "}
                          <span className="text-zinc-900">{slot.role}</span>
                        </DialogTitle>
                      </DialogHeader>
                    </div>
                    <div className="flex flex-col gap-4 p-4 sm:p-6">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-zinc-500" />
                        <Input
                          placeholder="Search VCT database..."
                          className="pl-10 bg-zinc-900 border-zinc-800 text-white font-bold h-10 sm:h-11"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                      </div>
                      <div className="max-h-[50vh] overflow-y-auto pr-1 custom-scrollbar">
                        <div className="space-y-3">
                          {allPlayers
                            .filter((p) => p.role === slot.role)
                            .filter((p) =>
                              p.name
                                .toLowerCase()
                                .includes(searchQuery.toLowerCase()),
                            )
                            .filter(
                              (p) => !roster.some((r) => r.player_id === p.id),
                            )
                            .sort((a, b) => {
                              const aValue = a[scoutSort.key];
                              const bValue = b[scoutSort.key];
                              return scoutSort.direction === "asc"
                                ? aValue - bValue
                                : bValue - aValue;
                            })
                            .map((player) => (
                              <div
                                key={player.id}
                                className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 sm:p-3.5 hover:border-[#ff4655]/30 transition-all"
                              >
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-3">
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-0.5 sm:mb-1">
                                      <div className="w-full font-black text-lg sm:text-base uppercase italic text-white leading-tight sm:truncate">
                                        {player.name}
                                      </div>
                                    </div>
                                    <div className="text-[10px] sm:text-xs text-zinc-500 font-bold uppercase tracking-wider mb-3 sm:mb-2">
                                      {player.team?.name} • {player.region}
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <div className="flex items-center gap-1.5 py-0.5 rounded">
                                        <span className="text-sm sm:text-xs font-black text-emerald-400">
                                          {player.points.toFixed(1)}
                                        </span>
                                        <span className="text-[8px] text-emerald-400 uppercase font-black mt-0.5">
                                          PTS
                                        </span>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="flex items-center justify-between sm:justify-end gap-3 pt-3 sm:pt-0 border-t sm:border-t-0 border-zinc-800/50">
                                    {/* Mobile Price Display */}
                                    <div className="flex flex-col sm:hidden">
                                      <span className="text-[8px] text-zinc-500 uppercase font-black leading-none mb-1">
                                        Current Price
                                      </span>
                                      <span className="text-sm text-emerald-400 font-black italic">
                                        €{player.current_price}M
                                      </span>
                                    </div>

                                    <Button
                                      size="sm"
                                      disabled={
                                        isProcessing ||
                                        member.budget < player.current_price
                                      }
                                      className="bg-zinc-800 sm:bg-zinc-700 hover:bg-emerald-700 text-white h-10 sm:h-9 px-6 sm:px-4 text-xs sm:text-sm uppercase font-black italic transition-all group-hover:scale-105 disabled:bg-zinc-900 disabled:opacity-50 whitespace-nowrap border border-zinc-700 sm:border-none"
                                      onClick={() =>
                                        handleBuyPlayer(slot, player)
                                      }
                                    >
                                      <span className="sm:hidden">
                                        BUY PLAYER
                                      </span>
                                      <span className="hidden sm:inline">
                                        €{player.current_price}M
                                      </span>
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                      <div className="flex items-center justify-start pt-3 border-t border-zinc-800/50">
                        <div className="flex gap-2 w-full overflow-x-auto no-scrollbar pb-1">
                          <button
                            onClick={() => toggleScoutSort("points")}
                            className={`text-[9px] sm:text-[10px] uppercase font-black px-3 py-2 rounded-lg transition-all shrink-0 border ${
                              scoutSort.key === "points"
                                ? "bg-[#ff4655] text-white border-[#ff4655]"
                                : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-700 hover:text-white"
                            }`}
                          >
                            Sort by Points{" "}
                            {scoutSort.key === "points" &&
                              (scoutSort.direction === "asc" ? "↑" : "↓")}
                          </button>
                          <button
                            onClick={() => toggleScoutSort("current_price")}
                            className={`text-[9px] sm:text-[10px] uppercase font-black px-3 py-2 rounded-lg transition-all shrink-0 border ${
                              scoutSort.key === "current_price"
                                ? "bg-[#ff4655] text-white border-[#ff4655]"
                                : "bg-zinc-900 text-zinc-500 border-zinc-800 hover:border-zinc-700 hover:text-white"
                            }`}
                          >
                            Sort by Price{" "}
                            {scoutSort.key === "current_price" &&
                              (scoutSort.direction === "asc" ? "↑" : "↓")}
                          </button>
                        </div>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </Card>
          );
        })}
      </div>

      {/* Release Confirmation Dialog */}
      <Dialog
        open={!!playerToRelease}
        onOpenChange={(open) => !open && setPlayerToRelease(null)}
      >
        <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-[#ff4655]">
              <AlertTriangle className="size-5" />
              CONFIRM RELEASE
            </DialogTitle>
            <DialogDescription className="text-zinc-400 pt-2">
              Are you sure you want to release{" "}
              <span className="text-white font-bold">
                {playerToRelease?.name}
              </span>
              ?
              <br />
              You will receive their full current value back to your budget.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setPlayerToRelease(null)}
              className="border-zinc-700 hover:bg-zinc-900 text-white"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSellPlayer}
              disabled={isProcessing}
              className="bg-[#ff4655] hover:bg-[#ff4655]/90 text-white font-bold"
            >
              {isProcessing ? "Processing..." : "Confirm Release"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
