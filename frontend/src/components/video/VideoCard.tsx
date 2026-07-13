import { Card, CardContent } from "@/components/ui/card";
import type { VideoResponse } from "@/types/api";

function formatDuration(seconds: number | null): string {
  if (!seconds) return "";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  if (hours > 0) return `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

function formatViews(count: number | null): string {
  if (!count) return "";
  if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1)}M views`;
  if (count >= 1_000) return `${(count / 1_000).toFixed(1)}K views`;
  return `${count} views`;
}

export function VideoCard({ video }: { video: VideoResponse }) {
  return (
    <Card>
      <CardContent className="flex gap-4 p-4">
        {video.thumbnail_url && (
          <img
            src={video.thumbnail_url}
            alt={video.title ?? "Video thumbnail"}
            className="h-24 w-40 shrink-0 rounded-md object-cover"
          />
        )}
        <div className="flex flex-col justify-center gap-1 min-w-0">
          <h2 className="font-semibold leading-snug line-clamp-2">{video.title}</h2>
          <p className="text-sm text-muted-foreground">
            {video.channel_name}
            {video.duration_seconds ? ` · ${formatDuration(video.duration_seconds)}` : ""}
            {video.view_count ? ` · ${formatViews(video.view_count)}` : ""}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
