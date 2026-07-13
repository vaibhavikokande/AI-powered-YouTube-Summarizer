import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/services/api";

interface HealthResponse {
  status: string;
  app: string;
  environment: string;
}

function useDarkMode() {
  const [isDark, setIsDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  return { isDark, toggle: () => setIsDark((prev) => !prev) };
}

export default function App() {
  const { isDark, toggle } = useDarkMode();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<HealthResponse>("/health")).data,
  });

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-8">
      <div className="flex items-center justify-between w-full max-w-xl">
        <h1 className="text-2xl font-semibold">AI YouTube Summarizer</h1>
        <button
          onClick={toggle}
          className="rounded-md border border-border px-3 py-1.5 text-sm"
        >
          {isDark ? "Light mode" : "Dark mode"}
        </button>
      </div>

      <div className="w-full max-w-xl rounded-lg border border-border p-6">
        <p className="text-muted-foreground text-sm mb-2">Backend status</p>
        {isLoading && <p>Checking backend connection…</p>}
        {isError && (
          <p className="text-red-500">
            Could not reach the backend at /api/v1/health. Is the FastAPI
            server running?
          </p>
        )}
        {data && (
          <p className="font-mono text-sm">
            {data.status.toUpperCase()} — {data.app} ({data.environment})
          </p>
        )}
      </div>
    </div>
  );
}
