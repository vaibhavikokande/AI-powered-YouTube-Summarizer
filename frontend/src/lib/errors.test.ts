import { AxiosError } from "axios";
import { describe, expect, it } from "vitest";

import { getApiErrorMessage } from "./errors";

function axiosErrorWithResponse(status: number, data: unknown): AxiosError {
  const err = new AxiosError("Request failed");
  // @ts-expect-error -- test fixture only needs `.data`; the rest of
  // AxiosResponse's shape is irrelevant to getApiErrorMessage.
  err.response = { status, statusText: "Error", headers: {}, config: {}, data };
  return err;
}

describe("getApiErrorMessage", () => {
  it("surfaces the backend's real error message when the server responded", () => {
    const err = axiosErrorWithResponse(401, {
      error: { code: "unauthorized", message: "Incorrect email or password." },
    });

    expect(getApiErrorMessage(err, "fallback")).toBe("Incorrect email or password.");
  });

  it("falls back to the caller's message for a 4xx response that doesn't match the expected shape", () => {
    const err = axiosErrorWithResponse(404, { detail: "something else entirely" });

    expect(getApiErrorMessage(err, "fallback message")).toBe("fallback message");
  });

  it("reports a generic server problem for a 5xx response without the expected shape", () => {
    // This is the actual shape "no backend running" takes behind Vite's dev
    // proxy: a real HTTP 500 response, not a network-level failure — so it
    // must NOT fall through to the caller's specific (e.g. credentials)
    // fallback message.
    const err = axiosErrorWithResponse(500, "<html>Internal Server Error</html>");

    expect(getApiErrorMessage(err, "Incorrect email or password.")).toBe(
      "The server ran into a problem. Please try again in a moment."
    );
  });

  it("reports a connectivity problem when there was no response at all", () => {
    const err = new AxiosError("Network Error", "ERR_NETWORK");

    expect(getApiErrorMessage(err, "fallback")).toBe(
      "Could not reach the server. Please check your connection and try again."
    );
  });

  it("falls back to the provided message for non-axios errors", () => {
    expect(getApiErrorMessage(new Error("boom"), "fallback")).toBe("fallback");
    expect(getApiErrorMessage("a plain string", "fallback")).toBe("fallback");
    expect(getApiErrorMessage(undefined, "fallback")).toBe("fallback");
  });
});
