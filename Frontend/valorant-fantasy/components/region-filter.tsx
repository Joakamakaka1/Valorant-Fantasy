"use client";

interface RegionFilterProps {
  regions: string[];
  currentRegion: string;
  onRegionChange: (region: string) => void;
}

export function RegionFilter({
  regions,
  currentRegion,
  onRegionChange,
}: RegionFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {regions.map((region) => (
        <button
          key={region}
          onClick={() => onRegionChange(region)}
          className={`px-4 py-2 rounded-lg text-xs font-black uppercase italic transition-all border ${
            currentRegion === region
              ? "bg-[#ff4655] text-white border-[#ff4655] shadow-lg"
              : "bg-zinc-900/40 text-zinc-500 border-zinc-800 hover:border-zinc-700 hover:text-white"
          }`}
        >
          {region}
        </button>
      ))}
    </div>
  );
}
