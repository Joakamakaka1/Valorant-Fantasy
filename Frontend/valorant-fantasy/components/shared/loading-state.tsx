"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  message?: string;
  className?: string;
  fullPage?: boolean;
}

export function LoadingState({
  message = "ACCESSING ENCRYPTED DATA...",
  className,
  fullPage = false,
}: LoadingStateProps) {
  const content = (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4",
        className,
      )}
    >
      <div className="text-[#ff4655] font-black italic animate-pulse tracking-tighter text-2xl md:text-3xl uppercase">
        {message}
      </div>
      <div className="flex gap-1">
        <div className="w-1 h-1 bg-[#ff4655] animate-bounce [animation-delay:-0.3s]" />
        <div className="w-1 h-1 bg-[#ff4655] animate-bounce [animation-delay:-0.15s]" />
        <div className="w-1 h-1 bg-[#ff4655] animate-bounce" />
      </div>
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[60vh]">
        {content}
      </div>
    );
  }

  return content;
}
