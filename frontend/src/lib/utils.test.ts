import { describe, expect, it } from "vitest";

import { cn } from "./utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("resolves conflicting tailwind classes, keeping the last one", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });

  it("drops falsy values", () => {
    const isEnabled: boolean = false;
    expect(cn("a", isEnabled && "b", undefined, null, "c")).toBe("a c");
  });
});
