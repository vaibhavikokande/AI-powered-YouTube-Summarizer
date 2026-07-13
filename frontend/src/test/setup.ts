import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

// Not using vitest's `globals: true` (avoids polluting every file with
// ambient test-global types), so cleanup must be wired up explicitly here
// rather than relying on @testing-library/react's auto-cleanup, which only
// registers itself when it detects a global `afterEach`.
afterEach(() => {
  cleanup();
});
