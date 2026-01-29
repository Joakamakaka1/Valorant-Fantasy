"use client";

import {
  BadgeCheck,
  Bell,
  ChevronsUpDown,
  LogOut,
  Mail,
  Zap,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/context/auth-context";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

export function NavUser({
  user,
}: {
  user: {
    name: string;
    email: string;
    avatar: string;
  };
}) {
  const { isMobile } = useSidebar();
  const { logout } = useAuth();
  const [openAccount, setOpenAccount] = useState(false);

  // Fetch latest user data when modal is opened
  const { data: currentUser } = useQuery({
    queryKey: ["auth-me-detailed"],
    queryFn: () => authApi.getMe(),
    enabled: openAccount,
  });

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton
                size="lg"
                className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              >
                <Avatar className="h-8 w-8 rounded-lg">
                  <AvatarImage src={user.avatar} alt={user.name} />
                  <AvatarFallback className="rounded-lg">CN</AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight gap-1">
                  <span className="truncate font-semibold">{user.name}</span>
                  <span className="truncate text-xs">{user.email}</span>
                </div>
                <ChevronsUpDown className="ml-auto size-4" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
              side={isMobile ? "bottom" : "right"}
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage src={user.avatar} alt={user.name} />
                    <AvatarFallback className="rounded-lg">CN</AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">{user.name}</span>
                    <span className="truncate text-xs">{user.email}</span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem onClick={() => setOpenAccount(true)}>
                  <BadgeCheck className="mr-2 size-4" />
                  Account
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Bell className="mr-2 size-4" />
                  Notifications
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 size-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>

        {/* Account Details Dialog */}
        <Dialog open={openAccount} onOpenChange={setOpenAccount}>
          <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-md p-0 overflow-hidden shadow-2xl">
            <div className="bg-gradient-to-r from-[#ff4655] to-red-900 p-8">
              <DialogHeader>
                <DialogTitle className="uppercase italic font-black text-3xl text-white tracking-tighter">
                  Protocol <span className="text-zinc-950">Identity</span>
                </DialogTitle>
              </DialogHeader>
            </div>
            <div className="p-8 space-y-6">
              <div className="flex flex-col items-center justify-center gap-4 pb-4 border-b border-zinc-800/50">
                <div className="size-24 rounded-2xl bg-zinc-900 border-2 border-zinc-800 p-1 shadow-inner relative">
                  <Avatar className="size-full rounded-xl">
                    <AvatarImage src={user.avatar} alt={user.name} />
                    <AvatarFallback className="text-2xl font-black bg-zinc-800">
                      {user.name[0]}
                    </AvatarFallback>
                  </Avatar>
                </div>
                <div className="text-center">
                  <h3 className="text-xl font-black uppercase italic tracking-tighter">
                    {currentUser?.username || user.name}
                  </h3>
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-widest">
                    Operational Agent #{currentUser?.id || "---"}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 flex items-center gap-2">
                    <Mail className="size-3" /> Registered Email
                  </label>
                  <div className="w-full bg-zinc-900/50 border border-zinc-800 p-3 rounded-lg text-sm font-bold text-zinc-300">
                    {currentUser?.email || user.email}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 flex items-center gap-2">
                    <Zap className="size-3" /> Authorization Level
                  </label>
                  <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                    <div className="size-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-black uppercase text-emerald-500">
                      {currentUser?.role || "Agent"} • Verified Operational
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </SidebarMenu>
    </>
  );
}
