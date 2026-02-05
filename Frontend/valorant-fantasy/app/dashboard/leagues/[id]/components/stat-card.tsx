"use client";

import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
  label: string;
  teamName: string;
  value: string;
  valueColor?: string;
}

export function StatCard({
  icon: Icon,
  iconColor,
  iconBg,
  label,
  teamName,
  value,
  valueColor = "text-white",
}: StatCardProps) {
  return (
    <Card className="bg-zinc-900/40 border-zinc-800 hover:border-[#ff4655]/30 transition-all">
      <CardContent className="p-3">
        <div className="flex items-center gap-2 mb-2">
          <div
            className={`size-8 rounded-full ${iconBg} flex items-center justify-center`}
          >
            <Icon className={`size-4 ${iconColor}`} />
          </div>
          <p className="text-[9px] uppercase text-zinc-500 font-black tracking-wider">
            {label}
          </p>
        </div>
        <p className="text-xs text-zinc-400 font-bold mb-1 truncate">
          {teamName}
        </p>
        <p className={`text-lg font-black ${valueColor} italic`}>{value}</p>
      </CardContent>
    </Card>
  );
}
