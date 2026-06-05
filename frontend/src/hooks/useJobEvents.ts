"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getEventsUrl } from "@/lib/api-client";

export type JobEvent = {
  id: string;
  type: string;
  data: Record<string, unknown>;
  receivedAt: number;
};

export type UseJobEventsOptions = {
  enabled?: boolean;
  onEvent?: (event: JobEvent) => void;
};

export function useJobEvents(
  jobId: string | null | undefined,
  options: UseJobEventsOptions = {},
) {
  const { enabled = true, onEvent } = options;
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<JobEvent | null>(null);
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const clearEvents = useCallback(() => setEvents([]), []);

  useEffect(() => {
    if (!jobId || !enabled) {
      setConnected(false);
      return;
    }

    const url = getEventsUrl(jobId);
    const source = new EventSource(url);
    let closed = false;

    source.onopen = () => {
      if (!closed) {
        setConnected(true);
        setError(null);
      }
    };

    source.onerror = () => {
      if (!closed) {
        setConnected(false);
        setError("Connection lost — retrying…");
      }
    };

    const handleMessage = (e: MessageEvent<string>) => {
      const type = e.type === "message" ? "message" : e.type;
      let parsed: Record<string, unknown> = {};
      try {
        parsed = JSON.parse(e.data) as Record<string, unknown>;
      } catch {
        parsed = { raw: e.data };
      }

      const event: JobEvent = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        type,
        data: parsed,
        receivedAt: Date.now(),
      };

      setLastEvent(event);
      setEvents((prev) => [...prev.slice(-99), event]);
      onEventRef.current?.(event);
    };

    const knownTypes = [
      "job.status",
      "job.progress",
      "dag.node.started",
      "dag.node.completed",
      "artifact.created",
      "evaluation.updated",
    ];

    knownTypes.forEach((eventType) => {
      source.addEventListener(eventType, handleMessage as EventListener);
    });
    source.onmessage = handleMessage;

    return () => {
      closed = true;
      source.close();
      setConnected(false);
    };
  }, [jobId, enabled]);

  return { connected, lastEvent, events, error, clearEvents };
}
