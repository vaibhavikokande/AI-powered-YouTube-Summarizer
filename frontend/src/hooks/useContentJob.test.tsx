import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", () => ({
  getJobStatus: vi.fn(),
}));

import { getJobStatus } from "@/lib/api-client";

import { useContentJob } from "./useContentJob";

const mockedGetJobStatus = vi.mocked(getJobStatus);

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  mockedGetJobStatus.mockReset();
});

describe("useContentJob", () => {
  it("starts idle with no job triggered", () => {
    const { result } = renderHook(
      () => useContentJob(async () => ({ task_id: "t1", status: "queued" })),
      { wrapper }
    );

    expect(result.current.hasStarted).toBe(false);
    expect(result.current.isPolling).toBe(false);
    expect(result.current.result).toBeNull();
  });

  it("transitions through polling to a successful result", async () => {
    const requestFn = vi.fn().mockResolvedValue({ task_id: "task-1", status: "queued" });
    mockedGetJobStatus.mockResolvedValue({
      task_id: "task-1",
      status: "SUCCESS",
      result: { content: "done" },
      error: null,
    });

    const { result } = renderHook(() => useContentJob(requestFn), { wrapper });

    await act(async () => {
      await result.current.trigger();
    });

    expect(result.current.hasStarted).toBe(true);

    await waitFor(() => {
      expect(result.current.result).toEqual({ content: "done" });
    });
    expect(result.current.isPolling).toBe(false);
  });

  it("surfaces a request error without ever starting to poll", async () => {
    const requestFn = vi.fn().mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useContentJob(requestFn), { wrapper });

    await act(async () => {
      await result.current.trigger();
    });

    expect(result.current.requestError).toBe("network down");
    expect(result.current.hasStarted).toBe(false);
  });

  it("surfaces a job failure", async () => {
    const requestFn = vi.fn().mockResolvedValue({ task_id: "task-2", status: "queued" });
    mockedGetJobStatus.mockResolvedValue({
      task_id: "task-2",
      status: "FAILURE",
      result: null,
      error: "boom",
    });

    const { result } = renderHook(() => useContentJob(requestFn), { wrapper });

    await act(async () => {
      await result.current.trigger();
    });

    await waitFor(() => {
      expect(result.current.jobError).toBe("boom");
    });
  });
});
