"use client";

import { Database, LayoutDashboard, Trophy, Zap } from "lucide-react";
import * as React from "react";
import { useEffect, useState } from "react";

import { NavMain } from "@/components/nav-main";
import { NavUser } from "@/components/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { leaguesApi } from "@/lib/api";
import { useAuth } from "@/lib/context/auth-context";
import { LeagueMember } from "@/lib/types";

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user } = useAuth();
  const [myLeagues, setMyLeagues] = useState<LeagueMember[]>([]);

  useEffect(() => {
    async function loadLeagues() {
      try {
        const leagues = await leaguesApi.getMyLeagues();
        setMyLeagues(leagues);
      } catch (error) {
        console.error("Failed to load leagues:", error);
      }
    }
    loadLeagues();
  }, []);

  const data = {
    user: {
      name: user?.username || "Guest",
      email: user?.email || "Connect your account",
      avatar: "/Icono.webp",
    },
    navMain: [
      {
        title: "Fantasy Hub",
        url: "/dashboard",
        icon: LayoutDashboard,
        isActive: true,
        items: [
          {
            title: "Overview",
            url: "/dashboard",
          },
        ],
      },
      {
        title: "My Leagues",
        url: "#",
        icon: Trophy,
        items: [
          ...myLeagues.map((lm) => ({
            title: lm.members_league?.name || lm.team_name,
            url: `/dashboard/leagues/${lm.league_id}`,
            items: [
              {
                title: "Dashboard",
                url: `/dashboard/leagues/${lm.league_id}`,
              },
              {
                title: "My Team",
                url: `/dashboard/leagues/${lm.league_id}?tab=team`,
              },
              {
                title: "Ranking",
                url: `/dashboard/leagues/${lm.league_id}?tab=ranking`,
              },
            ],
          })),
          {
            title: "Join/Create League",
            url: "/dashboard/leagues/join",
            items: [],
          },
        ],
      },
      {
        title: "Global Database",
        url: "#",
        icon: Database,
        items: [
          {
            title: "Player Stats",
            url: "/dashboard/database/players",
          },
          {
            title: "Match Results",
            url: "/dashboard/database/matches",
          },
          {
            title: "Tournaments",
            url: "/dashboard/database/tournaments",
          },
        ],
      },
    ],
  };

  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="#">
                <div className="flex aspect-square size-9 items-center justify-center rounded-lg bg-[#ff4655] text-white">
                  <Zap className="size-4 fill-current" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-black uppercase tracking-tighter italic text-base">
                    Valorant Fantasy
                  </span>
                  <span className="truncate text-xs opacity-50">
                    VCT Edition
                  </span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  );
}
