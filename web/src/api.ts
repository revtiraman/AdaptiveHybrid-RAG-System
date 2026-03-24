import type { Paper, QueryResult, SystemStats, UploadResult } from './types';

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? body.message ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function fetchPapers(): Promise<Paper[]> {
  const data = await request<{ papers: Paper[] }>('/papers');
  return data.papers ?? [];
}

export async function fetchStats(): Promise<SystemStats> {
  return request<SystemStats>('/stats');
}

export async function queryRAG(
  question: string,
  paperIds?: string[],
  filters?: Record<string, unknown>,
): Promise<QueryResult> {
  return request<QueryResult>('/query', {
    method: 'POST',
    body: JSON.stringify({
      question,
      paper_ids: paperIds && paperIds.length > 0 ? paperIds : undefined,
      filters: filters ?? undefined,
    }),
  });
}

export async function uploadPdf(
  file: File,
  title?: string,
  onProgress?: (pct: number) => void,
): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  if (title) form.append('title', title);

  return new Promise<UploadResult>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE}/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
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
        } catch {}
        reject(new Error(msg));
      }
    };

    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.send(form);
  });
}

export async function fetchPaperStructure(paperId: string) {
  return request<Record<string, unknown>>('/debug/paper-structure', {
    method: 'POST',
    body: JSON.stringify({ paper_id: paperId }),
  });
}

export async function checkHealth(): Promise<boolean> {
  try {
    const data = await request<{ status: string }>('/health/live');
    return data.status === 'ok';
  } catch {
    return false;
  }
}
