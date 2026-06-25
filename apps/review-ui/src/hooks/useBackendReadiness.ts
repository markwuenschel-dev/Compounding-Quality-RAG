import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  getReadiness,
  getReviewApiErrorMessage,
} from "../api/reviewApi";
import type { AsyncState, ReadinessResponse } from "../api/types";

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

  const [requestState, setRequestState] =
    useState<AsyncState<ReadinessResponse>>({ status: "loading" });

  const [isRefreshing, setIsRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);

    try {
      const nextResponse = await getReadiness();

      if (!mountedRef.current) {
        return;
      }

      setRequestState({
        status: "success",
        data: nextResponse,
      });
    } catch (error) {
      if (!mountedRef.current) {
        return;
      }

      setRequestState({
        status: "error",
        message: getReviewApiErrorMessage(
          error,
          "Backend readiness could not be confirmed.",
        ),
        error,
      });
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

  return useMemo(
    () => toBackendReadinessState(requestState, isRefreshing, refresh),
    [requestState, isRefreshing, refresh],
  );
}

function toBackendReadinessState(
  requestState: AsyncState<ReadinessResponse>,
  isRefreshing: boolean,
  refresh: () => Promise<void>,
): BackendReadinessState {
  switch (requestState.status) {
    case "idle":
    case "loading":
      return {
        status: "checking",
        response: null,
        message: "Checking backend readiness...",
        isRefreshing,
        refresh,
      };

    case "success":
      return {
        status: requestState.data.status === "READY"
          ? "ready"
          : "unavailable",
        response: requestState.data,
        message: requestState.data.status === "READY"
          ? "Backend ready"
          : buildUnavailableMessage(requestState.data),
        isRefreshing,
        refresh,
      };

    case "error":
      return {
        status: "unavailable",
        response: null,
        message: requestState.message,
        isRefreshing,
        refresh,
      };
  }
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