import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function MatchesSkeleton() {
  return (
    <div className="space-y-4">
      {Array(3)
        .fill(0)
        .map((_, i) => (
          <Card key={i} className="border-zinc-800 bg-zinc-900/50">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-center">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-20 rounded-full" />
                <Skeleton className="h-4 w-12" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between gap-8 mb-6">
                <div className="flex flex-1 justify-end gap-3">
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-10 w-10" />
                </div>
                <Skeleton className="h-12 w-32 rounded-xl" />
                <div className="flex flex-1 gap-3">
                  <Skeleton className="h-10 w-10" />
                  <Skeleton className="h-6 w-32" />
                </div>
              </div>
              <div className="border-t border-zinc-800 pt-4 mt-4">
                <Skeleton className="h-4 w-40 mb-3" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    {Array(3)
                      .fill(0)
                      .map((__, j) => (
                        <Skeleton key={j} className="h-12 w-full" />
                      ))}
                  </div>
                  <div className="space-y-2">
                    {Array(3)
                      .fill(0)
                      .map((__, j) => (
                        <Skeleton key={j} className="h-12 w-full" />
                      ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
    </div>
  );
}
