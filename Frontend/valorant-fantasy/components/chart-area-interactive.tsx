"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const chartData = [
  { date: "2024-04-01", desktop: 222, mobile: 150 },
  { date: "2024-04-02", desktop: 97, mobile: 180 },
  { date: "2024-04-03", desktop: 167, mobile: 120 },
  { date: "2024-04-04", desktop: 242, mobile: 260 },
  { date: "2024-04-05", desktop: 373, mobile: 290 },
  { date: "2024-04-06", desktop: 301, mobile: 340 },
  { date: "2024-04-07", desktop: 245, mobile: 180 },
  { date: "2024-04-08", desktop: 409, mobile: 320 },
  { date: "2024-04-09", desktop: 59, mobile: 110 },
  { date: "2024-04-10", desktop: 261, mobile: 190 },
  { date: "2024-04-11", desktop: 327, mobile: 350 },
  { date: "2024-04-12", desktop: 292, mobile: 210 },
  { date: "2024-04-13", desktop: 342, mobile: 380 },
  { date: "2024-04-14", desktop: 137, mobile: 220 },
  { date: "2024-04-15", desktop: 120, mobile: 170 },
];

const chartConfig = {
  desktop: {
    label: "Points",
    color: "#ff4655",
  },
  mobile: {
    label: "N/A",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig;

interface ChartDataPoint {
  time: string;
  desktop: number;
  mobile: number;
}

export function ChartAreaInteractive({ data }: { data: ChartDataPoint[] }) {
  const [timeRange, setTimeRange] = React.useState("90d");

  // If no data, show message or empty chart
  if (!data || data.length === 0) {
    return (
      <Card className="px-4 md:px-6 h-[400px] flex items-center justify-center">
        <p className="text-zinc-500 italic text-sm text-center">
          No progression data available yet.
          <br />
          Join a league and wait for matches to be played!
        </p>
      </Card>
    );
  }

  const filteredData = chartData.filter((item) => {
    const date = new Date(item.date);
    const now = new Date();
    let daysToSubtract = 90;
    if (timeRange === "30d") {
      daysToSubtract = 30;
    } else if (timeRange === "7d") {
      daysToSubtract = 7;
    }
    now.setDate(now.getDate() - daysToSubtract);
    return date >= now;
  });

  return (
    <Card className="px-4 md:px-6">
      <CardHeader className="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
        <div className="grid flex-1 gap-1 text-center sm:text-left">
          <CardTitle>Points Progression</CardTitle>
          <CardDescription>
            Historical point gains over the season
          </CardDescription>
        </div>

        <div className="flex items-center gap-2 bg-muted/50 p-1 rounded-lg">
          <button
            onClick={() => setTimeRange("90d")}
            className={`px-3 py-1 text-xs rounded-md transition-all ${
              timeRange === "90d"
                ? "bg-background shadow-sm"
                : "hover:bg-background/50"
            }`}
          >
            Last 3 months
          </button>
          <button
            onClick={() => setTimeRange("30d")}
            className={`px-3 py-1 text-xs rounded-md transition-all ${
              timeRange === "30d"
                ? "bg-background shadow-sm"
                : "hover:bg-background/50"
            }`}
          >
            Last 30 days
          </button>
          <button
            onClick={() => setTimeRange("7d")}
            className={`px-3 py-1 text-xs rounded-md transition-all ${
              timeRange === "7d"
                ? "bg-background shadow-sm"
                : "hover:bg-background/50"
            }`}
          >
            Last 7 days
          </button>
        </div>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-[4/3] w-full sm:aspect-auto sm:h-[250px]"
        >
          <AreaChart data={data}>
            <defs>
              <linearGradient id="fillDesktop" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ff4655" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#ff4655" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              vertical={false}
              strokeDasharray="3 3"
              stroke="#ffffff10"
            />
            <XAxis
              dataKey="time"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tick={{ fill: "#71717a", fontSize: 10 }}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="dot" />}
            />
            <Area
              dataKey="desktop"
              type="monotone"
              fill="url(#fillDesktop)"
              stroke="#ff4655"
              strokeWidth={2}
              stackId="a"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
