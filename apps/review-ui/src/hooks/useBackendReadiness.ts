import { useCallback, useEffect, useRef, useState } from "react";
import {
  getReadiness,
  getReviewApiErrorMessage,
} from "../api/reviewApi";
import type { ReadinessResponse } from "../api/types";

export type BackendReadinessStatus =
  | "checking"
  | "ready"
  | "unavailable";

export type BackendReadinessState = {
  status: BackendReadinessStatus;
  response: ReadinessResponse | null;
  message: string;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
};

const DEFAULT_POLL_INTERVAL_MS = 30_000;

export function useBackendReadiness(
  pollIntervalMs = DEFAULT_POLL_INTERVAL_MS,
): BackendReadinessState {
  const mountedRef = useRef(true);
  const [status, setStatus] =
    useState<BackendReadinessStatus>("checking");
  const [response, setResponse] =
    useState<ReadinessResponse | null>(null);
  const [message, setMessage] =
    useState("Checking backend readiness...");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);

    try {
      const nextResponse = await getReadiness();

      if (!mountedRef.current) {
        return;
      }

      setResponse(nextResponse);

      if (nextResponse.status === "READY") {
        setStatus("ready");
        setMessage("Backend ready");
      } else {
        setStatus("unavailable");
        setMessage(buildUnavailableMessage(nextResponse));
      }
    } catch (error) {
      if (!mountedRef.current) {
        return;
      }

      setResponse(null);
      setStatus("unavailable");
      setMessage(
        getReviewApiErrorMessage(
          error,
          "Backend readiness could not be confirmed.",
        ),
      );
    } finally {
      if (mountedRef.current) {
        setIsRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    void refresh();

    const intervalId = window.setInterval(
      () => void refresh(),
      pollIntervalMs,
    );

    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
    };
  }, [pollIntervalMs, refresh]);

  return {
    status,
    response,
    message,
    isRefreshing,
    refresh,
  };
}

function buildUnavailableMessage(
  response: ReadinessResponse,
): string {
  const failedChecks = response.checks
    .filter((check) => check.status === "DOWN")
    .map((check) => check.detail);

  if (failedChecks.length === 0) {
    return "Backend unavailable";
  }

  return `Backend unavailable: ${failedChecks.join(" ")}`;
}
