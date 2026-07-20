import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getJobStatus } from "@/lib/api-client";
import { getApiErrorMessage } from "@/lib/errors";
import type { JobEnqueuedResponse } from "@/types/api";

/**
 * Drives the request -> enqueue -> poll -> result lifecycle shared by
 * /summarize, /quiz, /flashcards, /faq, and /notes (all job-based since
 * Step 11). Each caller only supplies the request function and gets back
 * a uniform trigger/status/result shape.
 */
export function useContentJob<T>(requestFn: () => Promise<JobEnqueuedResponse>) {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isRequesting, setIsRequesting] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  const jobQuery = useQuery({
    queryKey: ["job", taskId],
    queryFn: () => getJobStatus<T>(taskId as string),
    enabled: taskId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "SUCCESS" || status === "FAILURE" ? false : 1500;
    },
  });

  async function trigger() {
    setIsRequesting(true);
    setRequestError(null);
    try {
      const { task_id } = await requestFn();
      setTaskId(task_id);
    } catch (err) {
      setRequestError(getApiErrorMessage(err, "Something went wrong. Please try again."));
    } finally {
      setIsRequesting(false);
    }
  }

  const status = jobQuery.data?.status;
  const isPolling = taskId !== null && status !== "SUCCESS" && status !== "FAILURE";

  return {
    trigger,
    isRequesting,
    isPolling,
    requestError,
    result: status === "SUCCESS" ? (jobQuery.data?.result ?? null) : null,
    jobError: status === "FAILURE" ? (jobQuery.data?.error ?? "The job failed.") : null,
    hasStarted: taskId !== null,
  };
}
