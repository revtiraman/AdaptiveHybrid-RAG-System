import type { Paper, QueryResult, SystemStats, UploadResult } from '../types';

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {
      // ignore parse error
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: (): Promise<{ status: string; service: string }> =>
    fetch(`${API_BASE}/health/live`).then((r) => r.json()),

  stats: (): Promise<SystemStats> =>
    request<SystemStats>('/stats'),

  papers: (): Promise<Paper[]> =>
    request<{ papers: Paper[] }>('/papers').then((d) => d.papers ?? []),

  query: (body: { question: string; paper_ids?: string[] }): Promise<QueryResult> =>
    request<QueryResult>('/query', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  upload: (
    file: File,
    title: string | undefined,
    onProgress: (pct: number) => void,
  ): Promise<UploadResult> => {
    const form = new FormData();
    form.append('file', file);
    if (title) form.append('title', title);

    return new Promise<UploadResult>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE}/upload`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText) as UploadResult);
          } catch {
            reject(new Error('Invalid response from server'));
          }
        } else {
          let msg = `Upload failed (${xhr.status})`;
          try {
            const body = JSON.parse(xhr.responseText);
            msg = body.detail ?? msg;
          } catch {
            // ignore
          }
          reject(new Error(msg));
        }
      };

      xhr.onerror = () => reject(new Error('Network error during upload'));
      xhr.send(form);
    });
  },

  chunkSample: (paper_id: string) =>
    request<{ paper_id: string; title: string; sample_count: number; chunks: unknown[] }>(
      '/debug/chunk-sample',
      {
        method: 'POST',
        body: JSON.stringify({ paper_id, limit: 5 }),
      },
    ),
};
