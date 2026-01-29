import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { cookies } from "next/headers";
import { matchesApi } from "@/lib/api";
import { MatchesView } from "./components/matches-view";

export default async function MatchesPage() {
  const queryClient = new QueryClient();

  // Fetch cookies to forward auth token
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  const headers = token ? { Cookie: `token=${token}` } : {};

  // Prefetch data on the server
  // Note: We duplicate the sort logic here or rely on the API to sort,
  // but for hydration consistency the queryFn here must match the client queryKey.
  // The client side does extra sorting, but prefetching the raw data is enough.
  await queryClient.prefetchQuery({
    queryKey: ["matches"],
    queryFn: () => matchesApi.getAll({}, { headers }),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <MatchesView />
    </HydrationBoundary>
  );
}
