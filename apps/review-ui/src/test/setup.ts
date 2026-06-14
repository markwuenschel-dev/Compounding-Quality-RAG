import "@testing-library/jest-dom/vitest";
import { beforeEach, vi } from "vitest";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url.endsWith("/ready")) {
        return new Response(
          JSON.stringify({
            status: "READY",
            checks: [
              {
                name: "spring",
                status: "UP",
                detail: "The Spring Boot API is running.",
              },
            ],
            timestamp: "2026-06-14T12:00:00Z",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
            },
          },
        );
      }

      throw new Error(`Unexpected unmocked fetch request: ${url}`);
    }),
  );
});
