import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useContentJob } from "@/hooks/useContentJob";
import { requestNotes } from "@/lib/api-client";
import type { NoteResponse } from "@/types/api";

export function NotesPanel({ url }: { url: string }) {
  const job = useContentJob<NoteResponse>(() => requestNotes({ url }));
  const note = job.result;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Notes</CardTitle>
        {!job.hasStarted && (
          <Button onClick={job.trigger} disabled={job.isRequesting} size="sm">
            {job.isRequesting ? <Spinner /> : "Generate"}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {job.requestError && <p className="text-sm text-red-500">{job.requestError}</p>}
        {job.isPolling && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner /> Writing notes…
          </div>
        )}
        {job.jobError && <p className="text-sm text-red-500">{job.jobError}</p>}
        {note && <pre className="whitespace-pre-wrap font-sans text-sm">{note.content_markdown}</pre>}
      </CardContent>
    </Card>
  );
}
