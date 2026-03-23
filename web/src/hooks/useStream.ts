import { useCallback, useRef, useState } from 'react';
import { useActiveSession, useRagStore } from '../store/ragStore';

type QueryOptions = {
  mode?: string;
  filters?: Record<string, string>;
  body?: Record<string, unknown>;
};

type StreamEvent = {
  type: 'status' | 'chunk' | 'citation' | 'reasoning' | 'verification' | 'complete' | 'error';
  data: Record<string, unknown>;
};

export function useStream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [currentStage, setCurrentStage] = useState('');
  const [stages, setStages] = useState<string[]>([]);

  const eventSourceRef = useRef<EventSource | null>(null);

  const addMessage = useRagStore((s) => s.addMessage);
  const updateMessage = useRagStore((s) => s.updateMessage);
  const activeSession = useActiveSession();

  const connectWebSocket = useCallback(
    (query: string, options: QueryOptions, messageId: string) => {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${protocol}://${window.location.host}/ws/query`);
      ws.onopen = () => ws.send(JSON.stringify({ query, options }));
      ws.onmessage = (event) => {
        const ev = JSON.parse(event.data) as StreamEvent;
        if (ev.type === 'chunk') {
          setStreamText((prev) => {
            const next = prev + String(ev.data.text ?? '');
            updateMessage(messageId, { streamText: next });
            return next;
          });
        }
        if (ev.type === 'complete') {
          setIsStreaming(false);
          ws.close();
          updateMessage(messageId, {
            status: 'complete',
            content: String(ev.data.answer ?? ''),
            streamText: undefined,
          });
        }
      };
      ws.onerror = () => {
        setIsStreaming(false);
        updateMessage(messageId, { status: 'error', error: 'Streaming failed on SSE and WebSocket fallback.' });
      };
    },
    [updateMessage],
  );

  const sendQuery = useCallback(
    async (query: string, options: QueryOptions = {}) => {
      if (!activeSession) return;

      setIsStreaming(true);
      setStreamText('');
      setStages([]);
      setCurrentStage('Retrieving context...');

      addMessage(activeSession.id, {
        role: 'user',
        content: query,
        timestamp: new Date(),
      });

      const messageId = addMessage(activeSession.id, {
        role: 'assistant',
        content: '',
        streamText: '',
        status: 'streaming',
        stage: 'Retrieving context...',
        timestamp: new Date(),
      });

      const params = new URLSearchParams({ query, mode: options.mode ?? 'auto', ...(options.filters ?? {}) });
      const es = new EventSource(`/api/query/stream?${params.toString()}`);
      eventSourceRef.current = es;

      let buffer = '';

      es.onmessage = (event) => {
        const ev = JSON.parse(event.data) as StreamEvent;
        switch (ev.type) {
          case 'status': {
            const msg = String(ev.data.message ?? 'Processing...');
            setCurrentStage(msg);
            setStages((prev) => [...prev, msg]);
            updateMessage(messageId, { stage: msg });
            break;
          }
          case 'chunk': {
            buffer += String(ev.data.text ?? '');
            setStreamText(buffer);
            updateMessage(messageId, { streamText: buffer });
            break;
          }
          case 'citation': {
            updateMessage(messageId, (prev) => ({ citations: [...(prev.citations ?? []), ev.data as unknown as never] }));
            break;
          }
          case 'reasoning': {
            updateMessage(messageId, (prev) => ({
              reasoningSteps: [...(prev.reasoningSteps ?? []), { step: String(ev.data.step ?? '...') }],
            }));
            break;
          }
          case 'verification': {
            updateMessage(messageId, { verification: ev.data as never });
            break;
          }
          case 'complete': {
            setIsStreaming(false);
            es.close();
            updateMessage(messageId, {
              status: 'complete',
              content: String(ev.data.answer ?? buffer),
              streamText: undefined,
            });
            break;
          }
          case 'error': {
            setIsStreaming(false);
            es.close();
            updateMessage(messageId, { status: 'error', error: String(ev.data.message ?? 'Unknown stream error') });
            break;
          }
        }
      };

      es.onerror = async () => {
        es.close();
        try {
          connectWebSocket(query, options, messageId);
        } catch {
          setIsStreaming(false);
          updateMessage(messageId, { status: 'error', error: 'Stream failed and fallback unavailable.' });
        }
      };

      const base = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';
      const res = await fetch(`${base}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, ...(options.body ?? {}) }),
      });
      const payload = (await res.json()) as Record<string, unknown>;
      setIsStreaming(false);
      es.close();
      updateMessage(messageId, {
        status: res.ok ? 'complete' : 'error',
        content: String(payload.answer ?? ''),
        claims: (payload.claims as never[]) ?? [],
        citations: (payload.citations as never[]) ?? [],
        verification: (payload.diagnostic as { verification?: unknown })?.verification as never,
      });
    },
    [activeSession, addMessage, connectWebSocket, updateMessage],
  );

  const cancelStream = useCallback(() => {
    eventSourceRef.current?.close();
    setIsStreaming(false);
  }, []);

  return { sendQuery, cancelStream, isStreaming, streamText, currentStage, stages };
}
