import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Spinner } from "@/components/ui/spinner";
import { VideoCard } from "@/components/video/VideoCard";
import { getHistory } from "@/lib/api-client";

export function HistoryPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["history"],
    queryFn: () => getHistory(),
    retry: false,
  });

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">History</h1>
      {isLoading && <Spinner />}
      {isError && <p className="text-sm text-red-500">Log in to see your history.</p>}
      {data?.items.map((video) => (
        <Link key={video.id} to={`/?url=${encodeURIComponent(video.url)}`}>
          <VideoCard video={video} />
        </Link>
      ))}
      {data && data.items.length === 0 && (
        <p className="text-sm text-muted-foreground">No videos summarized yet.</p>
      )}
    </div>
  );
}
