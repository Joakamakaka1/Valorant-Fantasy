import {
  dehydrate,
  HydrationBoundary,
  QueryClient,
} from "@tanstack/react-query";
import { cookies } from "next/headers";
import { tournamentsApi } from "@/lib/api";
import { TournamentsView } from "./components/tournaments-view";

export default async function TournamentsPage() {
  const queryClient = new QueryClient();

  // Fetch cookies to forward auth token
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  const headers = token ? { Cookie: `token=${token}` } : {};

  // Prefetch tournaments data on the server
  await queryClient.prefetchQuery({
    queryKey: ["tournaments"],
    queryFn: () => tournamentsApi.getAll({}, { headers }),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <TournamentsView />
    </HydrationBoundary>
  );
}
