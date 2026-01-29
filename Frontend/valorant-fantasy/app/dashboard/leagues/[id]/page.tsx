import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { cookies } from "next/headers";
import { leaguesApi, professionalApi } from "@/lib/api";
import { LeagueView } from "./components/league-view";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function LeagueDetailPage({ params }: PageProps) {
  const { id } = await params;
  const leagueId = parseInt(id);
  const queryClient = new QueryClient();

  // Fetch cookies to forward auth token
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  const headers = token ? { Cookie: `token=${token}` } : {};

  // Prefetch data on the server
  // 1. League Details
  await queryClient.prefetchQuery({
    queryKey: ["league", leagueId],
    queryFn: () => leaguesApi.getById(leagueId, { headers }),
  });

  // 2. Rankings (needed for member list and deriving current user's member info)
  await queryClient.prefetchQuery({
    queryKey: ["league-rankings", leagueId],
    queryFn: () => leaguesApi.getRankings(leagueId, { headers }),
  });

  // 3. All Players (heavy request, good to prefetch)
  await queryClient.prefetchQuery({
    queryKey: ["all-players"],
    queryFn: () => professionalApi.getPlayers({ limit: 500 }, { headers }),
  });

  // 4. Pro Teams (light request, but confirms cache)
  await queryClient.prefetchQuery({
    queryKey: ["pro-teams"],
    queryFn: () => professionalApi.getTeams({}, { headers }),
  });

  // Note: We cannot easily prefetch the 'roster' here because we don't know the 'memberId'
  // without first parsing the rankings on the server. Given the complexity vs benefit,
  // we let the client component handle the roster fetch (which will happen immediately after hydration).
  // The heavy lifting (players DB + rankings) is done.

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <LeagueView leagueId={leagueId} />
    </HydrationBoundary>
  );
}
