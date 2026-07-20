import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { FAQPanel } from "@/components/generators/FAQPanel";
import { FlashcardsPanel } from "@/components/generators/FlashcardsPanel";
import { NotesPanel } from "@/components/generators/NotesPanel";
import { QuizPanel } from "@/components/generators/QuizPanel";
import { SummaryPanel } from "@/components/summary/SummaryPanel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { VideoCard } from "@/components/video/VideoCard";
import { getVideo } from "@/lib/api-client";
import { getApiErrorMessage } from "@/lib/errors";

export function HomePage() {
  const [searchParams] = useSearchParams();
  const [urlInput, setUrlInput] = useState(searchParams.get("url") ?? "");
  const [submittedUrl, setSubmittedUrl] = useState<string | null>(searchParams.get("url"));

  const videoQuery = useQuery({
    queryKey: ["video", submittedUrl],
    queryFn: () => getVideo(submittedUrl as string),
    enabled: submittedUrl !== null,
    retry: false,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (urlInput.trim()) setSubmittedUrl(urlInput.trim());
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 p-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          placeholder="Paste a YouTube URL..."
        />
        <Button type="submit" disabled={videoQuery.isFetching}>
          {videoQuery.isFetching ? <Spinner /> : "Analyze"}
        </Button>
      </form>

      {videoQuery.isError && (
        <p className="text-sm text-red-500">
          {getApiErrorMessage(
            videoQuery.error,
            "Couldn't resolve that URL — check it's a valid YouTube video link."
          )}
        </p>
      )}

      {videoQuery.data && (
        // Keyed by video URL: each generator panel owns its own job state
        // (useContentJob's taskId/hasStarted/result), which isn't tied to
        // the `url` prop React sees. Without this key, switching to a new
        // video reuses the same panel instances and leaves them stuck
        // showing the *previous* video's stale result, error, or "already
        // started" state instead of resetting to a fresh "Generate" button.
        <div key={videoQuery.data.url} className="contents">
          <VideoCard video={videoQuery.data} />
          <SummaryPanel url={videoQuery.data.url} />
          <ChatPanel videoUrl={videoQuery.data.url} />
          <QuizPanel url={videoQuery.data.url} />
          <FlashcardsPanel url={videoQuery.data.url} />
          <FAQPanel url={videoQuery.data.url} />
          <NotesPanel url={videoQuery.data.url} />
        </div>
      )}
    </div>
  );
}
