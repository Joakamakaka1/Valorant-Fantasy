import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { cookies } from "next/headers";
import { professionalApi } from "@/lib/api";
import { DashboardView } from "./components/dashboard-view";

export default async function DashboardPage() {
  const queryClient = new QueryClient();

  // Fetch cookies to forward auth token
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  const headers = token ? { Cookie: `token=${token}` } : {};

  // Prefetch players for the "Market Movers" (Top Players) section
  await queryClient.prefetchQuery({
    queryKey: ["all-players-db"], // Using same key as players page for cache consistency
    queryFn: () => professionalApi.getPlayers({ limit: 500 }, { headers }),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DashboardView />
    </HydrationBoundary>
  );
}
