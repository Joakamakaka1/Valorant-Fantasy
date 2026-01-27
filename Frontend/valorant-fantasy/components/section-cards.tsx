import { TrendingUp, TrendingDown } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface Stat {
  title: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
  description: string;
  footer: string;
}

export function SectionCards({ stats }: { stats: Stat[] }) {
  if (!stats) return null;
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 px-4 md:px-6">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
            <div
              className={`flex items-center text-xs ${
                stat.trend === "up"
                  ? "text-emerald-500"
                  : stat.trend === "down"
                    ? "text-rose-500"
                    : "text-zinc-500"
              }`}
            >
              {stat.change}
              {stat.trend === "up" && <TrendingUp className="ml-1 size-3" />}
              {stat.trend === "down" && (
                <TrendingDown className="ml-1 size-3" />
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stat.description}
            </p>
            <p className="text-[10px] text-muted-foreground mt-2 border-t pt-2 opacity-50">
              {stat.footer}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
