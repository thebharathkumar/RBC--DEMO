/**
 * Shared types between the API and the web client.
 *
 * The Python source of truth lives in apps/api/src/models/. Keep this file in
 * sync until milestone 7, when types are generated from the OpenAPI schema.
 */

export type AgentName =
  | "supervisor"
  | "filings"
  | "earnings"
  | "market_data"
  | "news"
  | "comparables"
  | "critique"
  | "synthesizer";

export type AgentStatus = "pending" | "running" | "ok" | "partial" | "unavailable" | "error";

export interface RunRequest {
  ticker: string;
  config?: {
    enableHumanReview?: boolean;
  };
}

export interface SourceCitation {
  sourceId: string;
  hash: string;
  locator: string;
}

export interface AgentEvent {
  runId: string;
  agent: AgentName;
  status: AgentStatus;
  startedAt: string;
  finishedAt?: string;
  latencyMs?: number;
  retryCount: number;
  costUsd?: number;
  error?: { type: string; message: string };
}
