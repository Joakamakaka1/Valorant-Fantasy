"use client";

import { useEffect, useState } from "react";
import { SidebarInset } from "@/components/ui/sidebar";
import { SiteHeader } from "@/components/site-header";
import { SectionCards } from "@/components/section-cards";
import { ChartAreaInteractive } from "@/components/chart-area-interactive";
import { dashboardApi } from "@/lib/api";
import { DashboardOverview } from "@/lib/types";
import { LoadingState } from "@/components/shared/loading-state";

export default function DashboardPage() {
  // Estado para almacenar los datos generales del dashboard (puntos, ranking, ligas)
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  // Carga inicial de datos al montar el componente
  useEffect(() => {
    async function loadDashboardData() {
      try {
        const data = await dashboardApi.getOverview();
        setOverview(data);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardData();
  }, []);

  // Configuración de las tarjetas estadísticas mostradas en la parte superior
  const stats = [
    {
      title: "Total Points",
      value: overview?.total_points.toFixed(1) || "0.0",
      change: "+0.0%", // Todo: calcular cambio basado en historial
      trend: "up" as const,
      description: "Aggregate points from all leagues",
      footer: "Updated live",
    },
    {
      title: "Global Rank",
      value: overview?.global_rank || "N/A",
      change: "0",
      trend: "neutral" as const,
      description: "Your position in the world",
      footer: "Top 1% target",
    },
    {
      title: "Active Leagues",
      value: overview?.active_leagues.toString() || "0",
      change: "0",
      trend: "neutral" as const,
      description: "Leagues you are competing in",
      footer: "Join more to increase score",
    },
    {
      title: "Available Budget",
      value: overview?.available_budget || "€0M",
      change: "0",
      trend: "neutral" as const,
      description: "Budget in your primary team",
      footer: "Spend wisely",
    },
  ];

  // Transformar datos del historial para el gráfico interactivo
  const progressionData =
    overview?.points_history.map((item) => ({
      time: new Date(item.recorded_at).toLocaleDateString([], {
        month: "short",
        day: "numeric",
      }),
      desktop: item.total_points,
      mobile: 0, // Reservado para vista móvil si fuera necesario
    })) || [];

  return (
    <SidebarInset className="bg-[#0f1923]">
      <SiteHeader />
      <div className="flex flex-1 flex-col gap-6 py-4 overflow-y-auto">
        {loading ? (
          <LoadingState message="BOOTING SYSTEM OVERVIEW..." fullPage />
        ) : (
          <>
            {/* Tarjetas de estadísticas principales */}
            <SectionCards stats={stats} />

            {/* Gráfico de evolución de puntos */}
            <div className="px-4 md:px-6">
              <ChartAreaInteractive data={progressionData} />
            </div>
          </>
        )}
      </div>
    </SidebarInset>
  );
}
