import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { cookies } from "next/headers";
import { professionalApi } from "@/lib/api";
import { PlayersView } from "./components/players-view";

export default async function PlayerStatsPage() {
  const queryClient = new QueryClient();

  // Fetch cookies to forward auth token
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  const headers = token ? { Cookie: `token=${token}` } : {};

  // Prefetch data on the server
  await queryClient.prefetchQuery({
    queryKey: ["all-players-db"],
    queryFn: () => professionalApi.getPlayers({ limit: 500 }, { headers }),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PlayersView />
    </HydrationBoundary>
  );
}
