"use client";

import { Button } from "@/components/ui/button";
import {
  Table as ShadcnTable,
  TableBody as ShadcnTableBody,
  TableCell as ShadcnTableCell,
  TableHead as ShadcnTableHead,
  TableHeader as ShadcnTableHeader,
  TableRow as ShadcnTableRow,
} from "@/components/ui/table";
import { ArrowUpDown, ChevronDown, ChevronUp } from "lucide-react";
import { useMemo, useState } from "react";

interface PlayerData {
  id: string;
  name: string;
  org: string;
  role: string;
  points: number;
  price: string;
  rawPrice: number; // Added for numeric sorting
}

interface DataTableProps {
  data: PlayerData[];
  onRowClick?: (id: string) => void;
  currentRegion: string;
  onRegionChange: (region: string) => void;
}

export function DataTable({
  data,
  onRowClick,
  currentRegion,
  onRegionChange,
}: DataTableProps) {
  const regions = ["ALL", "AMERICAS", "EMEA", "PACIFIC", "CN"];
  const [sortConfig, setSortConfig] = useState<{
    key: "points" | "rawPrice" | null;
    direction: "asc" | "desc";
  }>({ key: null, direction: "desc" });

  const handleSort = (key: "points" | "rawPrice") => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc",
    }));
  };

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key!];
      const bValue = b[sortConfig.key!];

      if (sortConfig.direction === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }, [data, sortConfig]);

  const SortIcon = ({ column }: { column: "points" | "rawPrice" }) => {
    if (sortConfig.key !== column)
      return <ArrowUpDown className="ml-2 size-3 opacity-30" />;
    return sortConfig.direction === "asc" ? (
      <ChevronUp className="ml-2 size-3 text-[#ff4655]" />
    ) : (
      <ChevronDown className="ml-2 size-3 text-[#ff4655]" />
    );
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center gap-2 pb-4">
        {regions.map((region) => (
          <Button
            key={region}
            variant={currentRegion === region ? "outline" : "ghost"}
            size="sm"
            className={`h-8 font-black uppercase tracking-tighter italic transition-all ${
              currentRegion === region
                ? "border-[#ff4655] bg-[#ff4655]/10 text-white"
                : "text-zinc-500 hover:text-white"
            }`}
            onClick={() => onRegionChange(region)}
          >
            {region}
          </Button>
        ))}
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 backdrop-blur-md overflow-hidden shadow-2xl">
        <ShadcnTable>
          <ShadcnTableHeader>
            <ShadcnTableRow className="hover:bg-transparent border-zinc-800/50 bg-zinc-950/20">
              <ShadcnTableHead className="text-[10px] uppercase text-zinc-500 font-black italic tracking-widest pl-6">
                Player Identitiy
              </ShadcnTableHead>
              <ShadcnTableHead className="text-[10px] uppercase text-zinc-500 font-black italic tracking-widest text-center">
                Organization
              </ShadcnTableHead>
              <ShadcnTableHead className="text-[10px] uppercase text-zinc-500 font-black italic tracking-widest text-center">
                Protocol Role
              </ShadcnTableHead>
              <ShadcnTableHead
                className="text-[10px] uppercase text-zinc-500 font-black italic tracking-widest text-center cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("points")}
              >
                <div className="flex items-center justify-center">
                  Fantasy Points <SortIcon column="points" />
                </div>
              </ShadcnTableHead>
              <ShadcnTableHead
                className="text-[10px] uppercase text-zinc-500 font-black italic tracking-widest text-right pr-6 cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort("rawPrice")}
              >
                <div className="flex items-center justify-end">
                  Market Valuation <SortIcon column="rawPrice" />
                </div>
              </ShadcnTableHead>
            </ShadcnTableRow>
          </ShadcnTableHeader>
          <ShadcnTableBody>
            {sortedData.length > 0 ? (
              sortedData.map((row) => (
                <ShadcnTableRow
                  key={row.id}
                  className="hover:bg-white/5 cursor-pointer transition-colors border-zinc-800/20 group h-16"
                  onClick={() => onRowClick?.(row.id)}
                >
                  <ShadcnTableCell className="font-black text-white uppercase italic text-lg tracking-tighter pl-6 group-hover:text-[#ff4655] transition-colors">
                    {row.name}
                  </ShadcnTableCell>
                  <ShadcnTableCell className="text-xs text-zinc-400 font-bold text-center">
                    {row.org}
                  </ShadcnTableCell>
                  <ShadcnTableCell className="text-center">
                    <span className="inline-flex items-center rounded bg-zinc-800 px-2 py-0.5 text-[9px] font-black uppercase tracking-widest text-zinc-400 border border-zinc-700/50">
                      {row.role}
                    </span>
                  </ShadcnTableCell>
                  <ShadcnTableCell className="text-center text-emerald-400 font-black text-xl italic tracking-tighter">
                    {row.points.toFixed(1)}
                  </ShadcnTableCell>
                  <ShadcnTableCell className="text-right pr-6 font-mono font-bold text-zinc-300">
                    {row.price}
                  </ShadcnTableCell>
                </ShadcnTableRow>
              ))
            ) : (
              <ShadcnTableRow>
                <ShadcnTableCell
                  colSpan={5}
                  className="h-32 text-center text-zinc-500 italic font-bold"
                >
                  No operational records found for this sector.
                </ShadcnTableCell>
              </ShadcnTableRow>
            )}
          </ShadcnTableBody>
        </ShadcnTable>
      </div>
    </div>
  );
}
