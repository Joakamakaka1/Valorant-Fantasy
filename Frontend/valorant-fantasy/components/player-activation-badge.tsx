"use client";

import { CheckCircle2, XCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PlayerActivationBadgeProps {
  isActive: boolean;
  variant?: "badge" | "icon";
  size?: "sm" | "md" | "lg";
}

export function PlayerActivationBadge({
  isActive,
  variant = "badge",
  size = "md",
}: PlayerActivationBadgeProps) {
  const sizeClasses = {
    sm: "text-[9px] px-1.5 py-0.5",
    md: "text-[10px] px-2 py-1",
    lg: "text-xs px-3 py-1.5",
  };

  const iconSizes = {
    sm: "size-3",
    md: "size-4",
    lg: "size-5",
  };

  if (variant === "icon") {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="cursor-help">
              {isActive ? (
                <CheckCircle2 className={`${iconSizes[size]} text-green-500`} />
              ) : (
                <XCircle className={`${iconSizes[size]} text-red-500`} />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent className="bg-zinc-900 border-zinc-800">
            <p className="text-xs text-white">
              {isActive
                ? "🟢 Active in current tournament"
                : "🔴 Inactive - Not in ongoing tournament"}
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={`${sizeClasses[size]} rounded font-black uppercase tracking-wide cursor-help ${
              isActive
                ? "bg-green-600/20 text-green-400 border border-green-600/30"
                : "bg-red-600/20 text-red-400 border border-red-600/30"
            }`}
          >
            {isActive ? "ACTIVE" : "INACTIVE"}
          </span>
        </TooltipTrigger>
        <TooltipContent className="bg-zinc-900 border-zinc-800">
          <p className="text-xs text-white">
            {isActive
              ? "🟢 Active in current tournament"
              : "🔴 Inactive - Not in ongoing tournament"}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
