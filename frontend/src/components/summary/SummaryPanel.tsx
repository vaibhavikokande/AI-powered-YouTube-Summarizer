import { useState } from "react";
import { Download, Share2, Volume2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useContentJob } from "@/hooks/useContentJob";
import { createShareLink, downloadUrl, requestSummary, ttsUrl } from "@/lib/api-client";
import type { SummaryResponse, SummaryType } from "@/types/api";

const SUMMARY_TYPES: { value: SummaryType; label: string }[] = [
  { value: "short", label: "Short" },
  { value: "medium", label: "Medium" },
  { value: "detailed", label: "Detailed" },
  { value: "bullet", label: "Bullet" },
];

export function SummaryPanel({ url }: { url: string }) {
  const [selectedType, setSelectedType] = useState<SummaryType>("medium");
  const [includeMindmap, setIncludeMindmap] = useState(false);
  const [shareToken, setShareToken] = useState<string | null>(null);

  // All four summary types are requested in a single job — the backend's
  // map step (chunking + per-chunk summarization) is shared across them, so
  // there's no cost benefit to requesting them one at a time.
  const job = useContentJob<SummaryResponse[]>(() =>
    requestSummary({
      url,
      summary_types: ["short", "medium", "detailed", "bullet"],
      include_mindmap: includeMindmap,
    })
  );

  const summaries = job.result ?? [];
  const active = summaries.find((s) => s.summary_type === selectedType);

  async function handleShare() {
    if (!active) return;
    const { token } = await createShareLink(active.id);
    setShareToken(token);
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Summary</CardTitle>
        {!job.hasStarted && (
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={includeMindmap}
                onChange={(e) => setIncludeMindmap(e.target.checked)}
              />
              Include mind map
            </label>
            <Button onClick={job.trigger} disabled={job.isRequesting}>
              {job.isRequesting ? <Spinner /> : "Generate summary"}
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {job.requestError && <p className="text-sm text-red-500">{job.requestError}</p>}
        {job.isPolling && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Spinner /> Summarizing — this can take a minute for longer videos…
          </div>
        )}
        {job.jobError && <p className="text-sm text-red-500">{job.jobError}</p>}

        {summaries.length > 0 && (
          <Tabs value={selectedType} onValueChange={(v) => setSelectedType(v as SummaryType)}>
            <TabsList>
              {SUMMARY_TYPES.map((t) => (
                <TabsTrigger key={t.value} value={t.value}>
                  {t.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {active && (
              <TabsContent value={selectedType} className="flex flex-col gap-4">
                <p className="whitespace-pre-line text-sm leading-relaxed">{active.content}</p>

                {active.topics.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {active.topics.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                {active.key_takeaways.important_concepts.length > 0 && (
                  <div>
                    <h4 className="mb-1 text-sm font-semibold">Key Concepts</h4>
                    <ul className="list-disc space-y-0.5 pl-5 text-sm">
                      {active.key_takeaways.important_concepts.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {active.key_takeaways.action_items.length > 0 && (
                  <div>
                    <h4 className="mb-1 text-sm font-semibold">Action Items</h4>
                    <ul className="list-disc space-y-0.5 pl-5 text-sm">
                      {active.key_takeaways.action_items.map((a) => (
                        <li key={a}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {active.timestamped_sections.length > 0 && (
                  <div>
                    <h4 className="mb-1 text-sm font-semibold">Timestamped Sections</h4>
                    <ul className="space-y-1 text-sm">
                      {active.timestamped_sections.map((s) => (
                        <li key={s.timestamp_seconds}>
                          <span className="mr-2 font-mono text-muted-foreground">
                            {Math.floor(s.timestamp_seconds / 60)}:
                            {String(s.timestamp_seconds % 60).padStart(2, "0")}
                          </span>
                          <strong>{s.title}</strong> — {s.summary}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {active.mindmap_markdown && (
                  <div>
                    <h4 className="mb-1 text-sm font-semibold">Mind Map</h4>
                    <pre className="whitespace-pre-wrap rounded-md bg-muted p-3 text-xs overflow-x-auto">
                      {active.mindmap_markdown}
                    </pre>
                  </div>
                )}

                <div className="flex flex-wrap gap-2 pt-2">
                  {(["pdf", "docx", "markdown", "txt"] as const).map((format) => (
                    <a key={format} href={downloadUrl(active.id, format)} target="_blank" rel="noreferrer">
                      <Button variant="outline" size="sm">
                        <Download className="h-3.5 w-3.5" />
                        {format.toUpperCase()}
                      </Button>
                    </a>
                  ))}
                  <Button variant="outline" size="sm" onClick={handleShare}>
                    <Share2 className="h-3.5 w-3.5" />
                    Share
                  </Button>
                  <a href={ttsUrl(active.id)} target="_blank" rel="noreferrer">
                    <Button variant="outline" size="sm">
                      <Volume2 className="h-3.5 w-3.5" />
                      Listen
                    </Button>
                  </a>
                </div>

                {shareToken && (
                  <p className="text-xs text-muted-foreground">
                    Share link:{" "}
                    <code className="rounded bg-muted px-1 py-0.5">
                      {window.location.origin}/share/{shareToken}
                    </code>
                  </p>
                )}
              </TabsContent>
            )}
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
