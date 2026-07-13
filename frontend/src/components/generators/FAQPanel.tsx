import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useContentJob } from "@/hooks/useContentJob";
import { requestFAQ } from "@/lib/api-client";
import type { FAQItemResponse } from "@/types/api";

export function FAQPanel({ url }: { url: string }) {
  const job = useContentJob<FAQItemResponse[]>(() => requestFAQ({ url }));
  const items = job.result ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>FAQ</CardTitle>
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
            <Spinner /> Generating FAQ…
          </div>
        )}
        {job.jobError && <p className="text-sm text-red-500">{job.jobError}</p>}
        {items.length > 0 && (
          <div className="flex flex-col gap-3">
            {items.map((item) => (
              <div key={item.id}>
                <p className="text-sm font-semibold">{item.question}</p>
                <p className="text-sm text-muted-foreground">{item.answer}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
