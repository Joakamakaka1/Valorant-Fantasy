"use client";

import { useState } from "react";
import { leaguesApi } from "@/lib/api";
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
import { Plus, LogIn } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset } from "@/components/ui/sidebar";

export default function JoinLeaguePage() {
  const [newLeagueName, setNewLeagueName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [joinTeamName, setJoinTeamName] = useState("");
  const router = useRouter();
  const queryClient = useQueryClient();

  // Mutation for creating a league
  const createLeagueMutation = useMutation({
    mutationFn: (name: string) => leaguesApi.create(name, 10),
    onSuccess: (newLeague) => {
      toast.success(`League "${newLeague.name}" created!`);
      // Invalidate queries to update sidebar/dashboard immediately
      queryClient.invalidateQueries({ queryKey: ["my-leagues"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      router.push(`/dashboard/leagues/${newLeague.id}`);
    },
    onError: (error) => {
      toast.error("Failed to create league");
      console.error(error);
    },
  });

  // Mutation for joining a league
  const joinLeagueMutation = useMutation({
    mutationFn: async ({
      code,
      teamName,
    }: {
      code: string;
      teamName: string;
    }) => {
      // 1. Resolve code to league
      const league = await leaguesApi.getByInviteCode(code.toUpperCase());
      // 2. Join
      await leaguesApi.join(league.id, teamName);
      return league;
    },
    onSuccess: (league) => {
      toast.success(`Joined league: ${league.name}`);
      queryClient.invalidateQueries({ queryKey: ["my-leagues"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-overview"] });
      router.push(`/dashboard/leagues/${league.id}`);
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.error?.message ||
          "Invalid invite code or already joined",
      );
    },
  });

  const handleCreateLeague = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLeagueName) {
      toast.error("Please enter a league name");
      return;
    }
    createLeagueMutation.mutate(newLeagueName);
  };

  const handleJoinByCode = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteCode || !joinTeamName) {
      toast.error("Please enter both invite code and your team name");
      return;
    }
    joinLeagueMutation.mutate({ code: inviteCode, teamName: joinTeamName });
  };

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6 overflow-y-auto">
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
            <form
              onSubmit={handleCreateLeague}
              className="flex flex-col flex-1"
            >
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
                  disabled={createLeagueMutation.isPending}
                >
                  {createLeagueMutation.isPending
                    ? "Creating..."
                    : "Create League"}
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
                  disabled={joinLeagueMutation.isPending}
                >
                  {joinLeagueMutation.isPending
                    ? "Joining..."
                    : "Join Private League"}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </SidebarInset>
  );
}
