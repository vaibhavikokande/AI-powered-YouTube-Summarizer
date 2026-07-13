import { beforeEach, describe, expect, it } from "vitest";

import { useAuthStore } from "./auth-store";
import type { Token, UserResponse } from "@/types/api";

const fakeUser: UserResponse = {
  id: "user-1",
  email: "user@example.com",
  full_name: "Test User",
  avatar_url: null,
  is_active: true,
  created_at: "2024-01-15T00:00:00Z",
};

const fakeTokens: Token = {
  access_token: "access-123",
  refresh_token: "refresh-456",
  token_type: "bearer",
};

beforeEach(() => {
  localStorage.clear();
  useAuthStore.setState({ user: null, isAuthenticated: false });
});

describe("useAuthStore", () => {
  it("setSession stores tokens in localStorage and marks the user authenticated", () => {
    useAuthStore.getState().setSession(fakeTokens, fakeUser);

    expect(localStorage.getItem("access_token")).toBe("access-123");
    expect(localStorage.getItem("refresh_token")).toBe("refresh-456");
    expect(useAuthStore.getState().user).toEqual(fakeUser);
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it("logout clears localStorage and resets state", () => {
    useAuthStore.getState().setSession(fakeTokens, fakeUser);

    useAuthStore.getState().logout();

    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it("setUser(null) marks the user as unauthenticated", () => {
    useAuthStore.getState().setSession(fakeTokens, fakeUser);

    useAuthStore.getState().setUser(null);

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().user).toBeNull();
  });
});
