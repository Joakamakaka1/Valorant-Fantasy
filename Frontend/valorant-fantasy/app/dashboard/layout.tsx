"use client";

import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <div className="flex flex-1 flex-col overflow-hidden">{children}</div>
    </SidebarProvider>
  );
}
