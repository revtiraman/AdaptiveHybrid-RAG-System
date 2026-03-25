import type { QueryHistoryEntry } from '../types';

const MAX_HISTORY = 100;
const HISTORY_KEY = 'rag_query_history';
const ACTIVITY_KEY = 'rag_activity_log';
const MAX_ACTIVITY = 200;

export function saveQueryToHistory(entry: QueryHistoryEntry): void {
  try {
    const existing = getQueryHistory();
    const updated = [entry, ...existing].slice(0, MAX_HISTORY);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  } catch {
    // ignore storage errors
  }
}

export function getQueryHistory(): QueryHistoryEntry[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as QueryHistoryEntry[];
  } catch {
    return [];
  }
}

export function clearQueryHistory(): void {
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch {
    // ignore
  }
}

export interface ActivityEntry {
  type: 'ingest' | 'query' | 'eval';
  description: string;
  timestamp: string;
}

export function logActivity(
  type: 'ingest' | 'query' | 'eval',
  description: string,
): void {
  try {
    const existing = getActivity();
    const entry: ActivityEntry = {
      type,
      description,
      timestamp: new Date().toISOString(),
    };
    const updated = [entry, ...existing].slice(0, MAX_ACTIVITY);
    localStorage.setItem(ACTIVITY_KEY, JSON.stringify(updated));
  } catch {
    // ignore storage errors
  }
}

export function getActivity(): ActivityEntry[] {
  try {
    const raw = localStorage.getItem(ACTIVITY_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as ActivityEntry[];
  } catch {
    return [];
  }
}
