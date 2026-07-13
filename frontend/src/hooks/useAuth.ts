import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import { getMe } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

/** Fetches the current user on app load if a token is already stored,
 * and logs out if that token turns out to be invalid/expired. */
export function useBootstrapAuth() {
  const setUser = useAuthStore((s) => s.setUser);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const logout = useAuthStore((s) => s.logout);

  const { data, isError } = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    enabled: isAuthenticated,
    retry: false,
  });

  useEffect(() => {
    if (data) setUser(data);
  }, [data, setUser]);

  useEffect(() => {
    if (isError) logout();
  }, [isError, logout]);
}
