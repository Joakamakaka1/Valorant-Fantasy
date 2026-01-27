"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import {
  Trophy,
  Users,
  LayoutDashboard,
  ShoppingCart,
  Database,
  Search,
  History,
  Settings,
  LifeBuoy,
  Send,
  Zap,
} from "lucide-react";

import { NavMain } from "@/components/nav-main";
import { NavDocuments } from "@/components/nav-documents";
import { NavSecondary } from "@/components/nav-secondary";
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
import { useAuth } from "@/lib/context/auth-context";
import { leaguesApi } from "@/lib/api";
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
      avatar: "/avatars/user.jpg",
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
        ],
      },
    ],
    navSecondary: [
      {
        title: "Support",
        url: "#",
        icon: LifeBuoy,
      },
      {
        title: "Feedback",
        url: "#",
        icon: Send,
      },
    ],
    documents: [
      {
        name: "Search Players",
        url: "#",
        icon: Search,
      },
      {
        name: "App Settings",
        url: "/dashboard/settings",
        icon: Settings,
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
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-[#ff4655] text-white">
                  <Zap className="size-4 fill-current" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-black uppercase tracking-tighter">
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
        <NavDocuments documents={data.documents} />
        <NavSecondary items={data.navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
    </Sidebar>
  );
}
