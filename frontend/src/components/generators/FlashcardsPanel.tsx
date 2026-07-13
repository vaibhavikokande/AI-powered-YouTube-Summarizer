import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useContentJob } from "@/hooks/useContentJob";
import { requestFlashcards } from "@/lib/api-client";
import type { FlashcardResponse } from "@/types/api";

function Flashcard({ card }: { card: FlashcardResponse }) {
  const [flipped, setFlipped] = useState(false);
  return (
    <button
      type="button"
      onClick={() => setFlipped((f) => !f)}
      className="rounded-lg border border-border p-4 text-left text-sm transition-colors hover:bg-muted"
    >
      <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">
        {flipped ? "Answer" : "Question"}
      </p>
      <p>{flipped ? card.answer : card.question}</p>
    </button>
  );
}

export function FlashcardsPanel({ url }: { url: string }) {
  const job = useContentJob<FlashcardResponse[]>(() => requestFlashcards({ url }));
  const cards = job.result ?? [];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Flashcards</CardTitle>
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
            <Spinner /> Generating flashcards…
          </div>
        )}
        {job.jobError && <p className="text-sm text-red-500">{job.jobError}</p>}
        {cards.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {cards.map((card) => (
              <Flashcard key={card.id} card={card} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
