import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useContentJob } from "@/hooks/useContentJob";
import { requestQuiz } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { QuizResponse } from "@/types/api";

function QuizQuestionCard({ question }: { question: QuizResponse["questions"][number] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const revealed = selected !== null;

  const choices =
    question.options ?? (question.question_type === "true_false" ? ["True", "False"] : null);

  return (
    <div className="rounded-lg border border-border p-4">
      <p className="mb-3 text-sm font-medium">{question.question_text}</p>
      {choices ? (
        <div className="flex flex-col gap-2">
          {choices.map((choice) => {
            const isCorrect = choice === question.correct_answer;
            return (
              <button
                key={choice}
                type="button"
                onClick={() => setSelected(choice)}
                disabled={revealed}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-left text-sm transition-colors",
                  revealed && isCorrect && "border-green-500 bg-green-500/10",
                  revealed && !isCorrect && choice === selected && "border-red-500 bg-red-500/10",
                  !revealed && "border-border hover:bg-muted"
                )}
              >
                {choice}
              </button>
            );
          })}
        </div>
      ) : (
        <div>
          <Button size="sm" variant="outline" onClick={() => setSelected("shown")} disabled={revealed}>
            Reveal answer
          </Button>
          {revealed && <p className="mt-2 text-sm text-green-600">{question.correct_answer}</p>}
        </div>
      )}
      {revealed && question.explanation && (
        <p className="mt-2 text-xs text-muted-foreground">{question.explanation}</p>
      )}
    </div>
  );
}

export function QuizPanel({ url }: { url: string }) {
  const job = useContentJob<QuizResponse>(() => requestQuiz({ url }));
  const quiz = job.result;

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>Quiz</CardTitle>
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
            <Spinner /> Generating quiz…
          </div>
        )}
        {job.jobError && <p className="text-sm text-red-500">{job.jobError}</p>}
        {quiz && (
          <div className="flex flex-col gap-3">
            <h4 className="text-sm font-semibold">{quiz.title}</h4>
            {quiz.questions.map((q) => (
              <QuizQuestionCard key={q.id} question={q} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
