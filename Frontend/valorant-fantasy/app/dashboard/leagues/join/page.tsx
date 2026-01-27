"use client";

import { useEffect, useState } from "react";
import { leaguesApi } from "@/lib/api";
import { League, LeagueMember } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Trophy, Plus, LogIn, Users } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function JoinLeaguePage() {
  const [availableLeagues, setAvailableLeagues] = useState<League[]>([]);
  const [myLeagues, setMyLeagues] = useState<LeagueMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [newLeagueName, setNewLeagueName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [joinTeamName, setJoinTeamName] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const router = useRouter();

  const handleCreateLeague = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeagueName) {
      toast.error("Please enter a league name");
      return;
    }
    try {
      const newLeague = await leaguesApi.create(newLeagueName, 10);
      toast.success(`League "${newLeagueName}" created!`);
      router.push(`/dashboard/leagues/${newLeague.id}`);
    } catch (error) {
      toast.error("Failed to create league");
      console.error(error);
    }
  };

  const handleJoinByCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteCode || !joinTeamName) {
      toast.error("Please enter both invite code and your team name");
      return;
    }
    setIsJoining(true);
    try {
      // 1. Resolve code to league
      const league = await leaguesApi.getByInviteCode(inviteCode.toUpperCase());
      // 2. Join
      await leaguesApi.join(league.id, joinTeamName);
      toast.success(`Joined league: ${league.name}`);
      router.push(`/dashboard/leagues/${league.id}`);
    } catch (error: any) {
      toast.error(
        error.response?.data?.error?.message ||
          "Invalid invite code or already joined",
      );
    } finally {
      setIsJoining(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-8 p-8 overflow-y-auto bg-[#0f1923]">
      <div className="flex flex-col gap-2">
        <h1 className="text-5xl font-black text-white uppercase tracking-tighter italic">
          League <span className="text-[#ff4655]">Hub</span>
        </h1>
        <p className="text-zinc-400">
          Create your own competition or join a friend's league to start your
          journey.
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Create League */}
        <Card className="border-zinc-800 bg-zinc-900/50 flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="size-5 text-[#ff4655]" />
              Create a New League
            </CardTitle>
            <CardDescription>
              Start your own competition and invite your friends.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleCreateLeague} className="flex flex-col flex-1">
            <CardContent className="space-y-4 flex-1">
              <div className="space-y-2">
                <Label htmlFor="league-name">League Name</Label>
                <Input
                  id="league-name"
                  placeholder="The Champions League"
                  value={newLeagueName}
                  onChange={(e) => setNewLeagueName(e.target.value)}
                  className="bg-zinc-950 border-zinc-800"
                />
              </div>
            </CardContent>
            <CardFooter className="mt-auto pt-4">
              <Button
                type="submit"
                className="w-full bg-[#ff4655] hover:bg-[#ff4655]/90"
              >
                Create League
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* Join League by Code */}
        <Card className="border-zinc-800 bg-zinc-900/50 flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LogIn className="size-5 text-[#ff4655]" />
              Join with Invite Code
            </CardTitle>
            <CardDescription>
              Enter a code provided by a league administrator.
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleJoinByCode} className="flex flex-col flex-1">
            <CardContent className="space-y-4 flex-1">
              <div className="space-y-2">
                <Label htmlFor="invite-code">Invite Code</Label>
                <Input
                  id="invite-code"
                  placeholder="ABC123XY"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 uppercase"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="join-team-name">Your Team Name</Label>
                <Input
                  id="join-team-name"
                  placeholder="My Fantasy Team"
                  value={joinTeamName}
                  onChange={(e) => setJoinTeamName(e.target.value)}
                  className="bg-zinc-950 border-zinc-800"
                />
              </div>
            </CardContent>
            <CardFooter className="mt-auto pt-4">
              <Button
                type="submit"
                variant="outline"
                className="w-full border-[#ff4655]/50 text-white hover:bg-[#ff4655]/10"
                disabled={isJoining}
              >
                {isJoining ? "Joining..." : "Join Private League"}
              </Button>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
