import axios from "axios";

/**
 * Extracts a user-facing message from an API error, distinguishing three
 * cases a blanket catch conflates:
 *  1. The backend actually processed the request and rejected it — surface
 *     its real message (`{"error": {"code", "message"}}`, see
 *     app/core/exceptions.py).
 *  2. *Something* responded with a server error but not our backend's JSON
 *     shape — e.g. Vite's dev proxy returns a bare HTTP 500 (not a network
 *     failure axios can detect) when the backend it's proxying to is
 *     unreachable. Confirmed by hand: this is the actual shape "no backend
 *     running" takes in local dev, not case 3 below.
 *  3. No response was received at all (DNS failure, CORS block, connection
 *     refused with no proxy in front of it).
 * Only case 1 uses the caller's specific fallback message (e.g. "Incorrect
 * email or password") — cases 2 and 3 are infrastructure problems, and
 * showing a credentials-specific message for those sends the user chasing
 * the wrong fix.
 */
export function getApiErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    if (err.response) {
      const backendMessage = err.response.data?.error?.message;
      if (typeof backendMessage === "string") return backendMessage;
      if (err.response.status >= 500) {
        return "The server ran into a problem. Please try again in a moment.";
      }
      return fallback;
    }
    return "Could not reach the server. Please check your connection and try again.";
  }
  return fallback;
}
