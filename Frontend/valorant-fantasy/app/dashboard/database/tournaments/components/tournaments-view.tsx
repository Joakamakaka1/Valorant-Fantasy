"use client";

import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { tournamentsApi } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Calendar, Trophy, AlertCircle } from "lucide-react";
import { Tournament } from "@/lib/types";

export function TournamentsView() {
  const {
    data: tournaments = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["tournaments"],
    queryFn: () => tournamentsApi.getAll(),
    staleTime: 1000 * 60 * 10, // 10 minutes cache
  });

  const getStatusBadge = (status: string) => {
    const styles = {
      ONGOING: "bg-green-600/20 text-green-400 border-green-600/30",
      UPCOMING: "bg-blue-600/20 text-blue-400 border-blue-600/30",
      COMPLETED: "bg-gray-600/20 text-gray-400 border-gray-600/30",
    };
    return styles[status as keyof typeof styles] || styles.COMPLETED;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 p-4 md:p-6 overflow-y-auto">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white uppercase tracking-tighter italic">
            VCT <span className="text-[#ff4655]">Tournaments</span>
          </h1>
          <p className="text-sm sm:text-base text-zinc-400">
            Official VCT tournaments for the 2026 season.
          </p>
        </div>

        {isLoading ? (
          <div className="grid gap-4">
            {[1, 2, 3].map((i) => (
              <Card
                key={i}
                className="bg-zinc-900/40 border-zinc-800 p-6 animate-pulse"
              >
                <div className="h-6 bg-zinc-800 rounded w-1/3 mb-4"></div>
                <div className="h-4 bg-zinc-800 rounded w-1/2"></div>
              </Card>
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center p-12 text-center text-red-500">
            <AlertCircle className="size-12 mb-4" />
            <h3 className="text-xl font-bold uppercase">System Error</h3>
            <p className="text-zinc-400 max-w-md">
              Could not retrieve tournaments. Please check your connection and
              try again.
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {tournaments.map((tournament) => (
              <Card
                key={tournament.id}
                className="bg-zinc-900/40 border-zinc-800"
              >
                <div className="p-6">
                  {/* Header with status */}
                  <div className="flex items-start justify-between gap-4 mb-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Trophy className="size-5 text-[#ff4655]" />
                        <h2 className="text-xl md:text-2xl font-black text-white uppercase italic tracking-tight">
                          {tournament.name}
                        </h2>
                      </div>
                      <span
                        className={`inline-flex px-3 py-1 rounded-lg text-xs font-black uppercase tracking-wide border ${getStatusBadge(tournament.status)}`}
                      >
                        {tournament.status}
                      </span>
                    </div>
                  </div>

                  {/* Tournament Details Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Start Date */}
                    <div className="flex items-center gap-3 bg-zinc-900/50 rounded-lg p-3 border border-zinc-800/50">
                      <Calendar className="size-4 text-zinc-500" />
                      <div>
                        <p className="text-[10px] text-zinc-500 font-black uppercase tracking-wide">
                          Start Date
                        </p>
                        <p className="text-sm text-white font-bold">
                          {formatDate(tournament.start_date)}
                        </p>
                      </div>
                    </div>

                    {/* End Date */}
                    {tournament.end_date && (
                      <div className="flex items-center gap-3 bg-zinc-900/50 rounded-lg p-3 border border-zinc-800/50">
                        <Calendar className="size-4 text-zinc-500" />
                        <div>
                          <p className="text-[10px] text-zinc-500 font-black uppercase tracking-wide">
                            End Date
                          </p>
                          <p className="text-sm text-white font-bold">
                            {formatDate(tournament.end_date)}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* VLR Event ID */}
                    <div className="flex items-center gap-3 bg-zinc-900/50 rounded-lg p-3 border border-zinc-800/50">
                      <div className="size-4 flex items-center justify-center">
                        <span className="text-xs text-zinc-500 font-black">
                          #
                        </span>
                      </div>
                      <div>
                        <p className="text-[10px] text-zinc-500 font-black uppercase tracking-wide">
                          VLR Event ID
                        </p>
                        <p className="text-sm text-white font-bold">
                          {tournament.vlr_event_id}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* VLR Link */}
                  {tournament.vlr_event_path && (
                    <div className="mt-4 pt-4 border-t border-zinc-800/50">
                      <a
                        href={`https://www.vlr.gg${tournament.vlr_event_path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-[#ff4655] hover:text-[#ff4655]/80 font-bold uppercase tracking-wide transition-colors"
                      >
                        View on VLR.gg →
                      </a>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </SidebarInset>
  );
}
