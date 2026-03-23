import { AnimatePresence, motion } from 'framer-motion';
import { Send } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useStream } from '../../hooks/useStream';
import type { Citation } from '../../store/ragStore';
import { useActiveSession, useRagStore } from '../../store/ragStore';
import { StreamingIndicator } from '../ui/StreamingIndicator';
import { CitationPreviewModal } from './CitationPreviewModal';
import { EmptyState } from './EmptyState';
import { EvidencePanel } from './EvidencePanel';
import { ReasoningTrace } from './ReasoningTrace';
import { StreamingText } from './StreamingText';
import { VerificationStatusBar } from './VerificationStatusBar';

const modes = ['Adaptive', 'Multi-hop', 'Strict cite', 'Graph', 'HyDE', 'Claims-only'] as const;

function getStageLabel(stage: string): string {
  if (!stage) return 'Preparing answer';
  if (/retriev|context|search/i.test(stage)) return 'Retrieving evidence';
  if (/reason|synth|draft|compose/i.test(stage)) return 'Reasoning over sources';
  if (/verif|check|faithful|ground/i.test(stage)) return 'Verifying claims';
  if (/cit|source|attribut/i.test(stage)) return 'Linking citations';
  if (/final|complete|done/i.test(stage)) return 'Finalizing response';
  return stage;
}

function getStageProgress(stage: string): number {
  const normalized = stage.toLowerCase();
  if (!normalized) return 10;
  if (/retriev|context|search/.test(normalized)) return 25;
  if (/reason|synth|draft|compose/.test(normalized)) return 55;
  if (/verif|check|faithful|ground/.test(normalized)) return 75;
  if (/cit|source|attribut/.test(normalized)) return 90;
  if (/final|complete|done/.test(normalized)) return 100;
  return 40;
}

export function ChatInterface() {
  const session = useActiveSession();
  const renameSession = useRagStore((s) => s.renameSession);
  const settings = useRagStore((s) => s.settings);
  const updateSettings = useRagStore((s) => s.updateSettings);
  const [draftName, setDraftName] = useState(session?.name ?? 'Session');
  const [query, setQuery] = useState('');
  const [enabledModes, setEnabledModes] = useState<string[]>(['Adaptive']);
  const [searchParams] = useSearchParams();
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const { sendQuery, cancelStream, isStreaming, streamText, currentStage, stages } = useStream();

  const messages = session?.messages ?? [];
  const stageLabel = getStageLabel(currentStage);
  const stageProgress = getStageProgress(currentStage);
  const stageTrail = stages.slice(-3);

  const tokenEstimate = useMemo(() => Math.ceil(query.length / 4), [query]);

  useEffect(() => {
    const mode = (searchParams.get('mode') ?? '').toLowerCase();
    if (mode === 'multihop') {
      setEnabledModes((prev) => {
        if (prev.length === 1 && prev[0] === 'Multi-hop') return prev;
        return ['Multi-hop'];
      });
    }
  }, [searchParams]);

  const onSend = async () => {
    const clean = query.trim();
    if (!clean) return;
    await sendQuery(clean, {
      mode: enabledModes.includes('Multi-hop') ? 'multi_hop' : 'auto',
      body: {
        filters: enabledModes.includes('Claims-only') ? { content_type: 'claim' } : undefined,
      },
    });
    setQuery('');
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-11 items-center justify-between border-b border-slate-300 bg-surface-primary px-4">
        <input
          value={draftName}
          onChange={(event) => setDraftName(event.target.value)}
          onBlur={() => session && renameSession(session.id, draftName)}
          className="rounded-md border border-transparent bg-transparent px-2 py-1 text-sm font-semibold hover:border-slate-300 focus:border-slate-400 focus:outline-none"
        />
        <div className="text-xs text-text-secondary">Scope: {session?.paperScope.length ? `${session.paperScope.length} papers` : 'All papers'}</div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <EmptyState onPickPrompt={setQuery} />
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`max-w-[75%] rounded-lg border p-3 ${
                  message.role === 'user'
                    ? 'ml-auto border-slate-300 bg-surface-secondary'
                    : 'border-slate-300 bg-surface-primary'
                }`}
              >
                {message.streamText ? <StreamingText text={message.streamText} /> : <p className="whitespace-pre-wrap text-sm">{message.content}</p>}
                {message.claims?.length ? <EvidencePanel claims={message.claims} onCitationClick={setActiveCitation} /> : null}
                {message.verification ? <VerificationStatusBar verification={message.verification} /> : null}
                {message.reasoningSteps?.length ? <ReasoningTrace steps={message.reasoningSteps} /> : null}
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-slate-300 bg-surface-primary p-3">
        <div className="rounded-lg border border-slate-300 p-2">
          <textarea
            id="global-query-input"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="h-24 w-full resize-none border-none bg-transparent text-sm outline-none"
            placeholder="Ask about your papers... (/ to focus, Cmd+K for commands)"
          />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {modes.map((mode) => {
              const active = enabledModes.includes(mode);
              return (
                <button
                  key={mode}
                  onClick={() =>
                    setEnabledModes((prev) => (active ? prev.filter((x) => x !== mode) : [...prev, mode]))
                  }
                  className={`rounded-full border px-2 py-1 text-xs ${
                    active ? 'border-blue-400 bg-blue-50 text-blue-700' : 'border-slate-300 text-text-secondary'
                  }`}
                >
                  {mode}
                </button>
              );
            })}
            <span className="ml-auto text-xs text-text-secondary">{query.length} chars ~ {tokenEstimate} tokens</span>
            <button
              onClick={() => updateSettings({ primaryModel: settings.primaryModel === 'gpt-4o' ? 'claude-3.7-sonnet' : 'gpt-4o' })}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs"
            >
              {settings.primaryModel}
            </button>
            <button
              onClick={isStreaming ? cancelStream : onSend}
              className="inline-flex items-center gap-1 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white"
            >
              <Send size={12} />
              {isStreaming ? 'Cancel' : 'Send'}
            </button>
          </div>
          <AnimatePresence>
            {isStreaming && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3"
              >
                <StreamingIndicator stage={stageLabel} />
                <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-200">
                  <motion.div
                    className="h-full rounded-full bg-blue-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${stageProgress}%` }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                  />
                </div>
                {stageTrail.length ? (
                  <div className="mt-2 flex flex-wrap gap-1 text-[11px] text-text-secondary">
                    {stageTrail.map((stage, idx) => (
                      <span key={`${stage}-${idx}`} className="rounded-full border border-slate-300 px-2 py-0.5">
                        {getStageLabel(stage)}
                      </span>
                    ))}
                  </div>
                ) : null}
                {streamText ? <div className="mt-2 text-xs text-text-secondary">{streamText.slice(-80)}</div> : null}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {activeCitation ? <CitationPreviewModal citation={activeCitation} onClose={() => setActiveCitation(null)} /> : null}
    </div>
  );
}
