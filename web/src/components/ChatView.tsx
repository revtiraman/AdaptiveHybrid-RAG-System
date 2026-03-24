import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { Message, Paper } from '../types';
import AnswerCard from './AnswerCard';

interface Props {
  messages: Message[];
  querying: boolean;
  papers: Paper[];
  onSend: (q: string) => void;
}

const SUGGESTIONS = [
  'What is the main contribution of this paper?',
  'Summarize the methodology used.',
  'What datasets were used for evaluation?',
  'What are the key results and metrics?',
  'What are the limitations of this work?',
  'How does this compare to prior baselines?',
  'What future work do the authors suggest?',
  'Explain the model architecture in detail.',
];

export default function ChatView({ messages, querying, papers, onSend }: Props) {
  const [input, setInput]   = useState('');
  const bottomRef           = useRef<HTMLDivElement>(null);
  const textareaRef         = useRef<HTMLTextAreaElement>(null);
  const isEmpty             = messages.length === 0;

  /* scroll to bottom on new messages */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, querying]);

  /* auto-resize textarea */
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, [input]);

  const handleSend = useCallback(() => {
    const q = input.trim();
    if (!q || querying) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    onSend(q);
  }, [input, querying, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-base)' }}>

      {/* Messages area */}
      <div className="scroll-area" style={{ flex: 1, padding: '24px 0' }}>
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '0 20px' }}>

          {isEmpty ? (
            <EmptyState papers={papers} onSuggest={q => { setInput(q); textareaRef.current?.focus(); }} />
          ) : (
            messages.map((msg, i) => (
              <MessageRow key={msg.id} msg={msg} animDelay={i * 0.04} papers={papers} />
            ))
          )}

          {/* Thinking indicator */}
          {querying && (
            <div className="animate-fade-in" style={{ display: 'flex', gap: 12, marginTop: 16, alignItems: 'flex-start' }}>
              <BotAvatar />
              <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: '4px 12px 12px 12px', padding: '12px 16px',
                display: 'flex', alignItems: 'center', gap: 8,
              }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Thinking</span>
                <span className="thinking-dot" />
                <span className="thinking-dot" />
                <span className="thinking-dot" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Suggestion chips (above input, when empty) */}
      {isEmpty && (
        <div style={{ maxWidth: 800, margin: '0 auto', width: '100%', padding: '0 20px 8px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {SUGGESTIONS.slice(0, 4).map(s => (
              <button
                key={s}
                onClick={() => { setInput(s); textareaRef.current?.focus(); }}
                style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  borderRadius: 999, padding: '5px 12px', cursor: 'pointer',
                  fontSize: 12, color: 'var(--text-secondary)',
                  transition: 'border-color .15s, color .15s',
                }}
                onMouseEnter={e => { (e.target as HTMLElement).style.borderColor = 'var(--accent)'; (e.target as HTMLElement).style.color = '#a5b4fc'; }}
                onMouseLeave={e => { (e.target as HTMLElement).style.borderColor = 'var(--border)'; (e.target as HTMLElement).style.color = 'var(--text-secondary)'; }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div style={{ flexShrink: 0, padding: '0 20px 16px', maxWidth: 800, margin: '0 auto', width: '100%' }}>
        <div style={{
          display: 'flex', gap: 10, alignItems: 'flex-end',
          background: 'var(--bg-input)', border: '1px solid var(--border)',
          borderRadius: 12, padding: '10px 12px',
          transition: 'border-color .15s',
          boxShadow: '0 2px 12px rgba(0,0,0,.3)',
        }}
          onFocus={() => {}} // handled via CSS focus-within if needed
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your papers… (⌘Enter to send)"
            rows={1}
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: 'var(--text-primary)', fontSize: 14, lineHeight: 1.6,
              resize: 'none', fontFamily: 'inherit',
              maxHeight: 200, overflowY: 'auto',
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || querying}
            style={{
              background: input.trim() && !querying ? 'var(--accent)' : 'var(--bg-hover)',
              border: 'none', borderRadius: 8, cursor: input.trim() && !querying ? 'pointer' : 'default',
              padding: '7px 14px', color: input.trim() && !querying ? '#fff' : 'var(--text-muted)',
              fontSize: 13, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6,
              transition: 'background .15s, color .15s', flexShrink: 0,
            }}
          >
            {querying ? <span className="spinner" /> : <SendIcon />}
            {querying ? 'Thinking…' : 'Send'}
          </button>
        </div>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
          ⌘ Enter to send · Select papers in sidebar to scope queries
        </p>
      </div>
    </div>
  );
}

/* ── Message row ── */
function MessageRow({ msg, animDelay, papers }: { msg: Message; animDelay: number; papers: Paper[] }) {
  if (msg.role === 'user') {
    return (
      <div className="animate-fade-up" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16, animationDelay: `${animDelay}s` }}>
        <div style={{
          background: 'var(--accent)', color: '#fff',
          borderRadius: '12px 4px 12px 12px',
          padding: '10px 16px', maxWidth: '75%', fontSize: 14, lineHeight: 1.6,
        }}>
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-up" style={{ display: 'flex', gap: 12, marginBottom: 24, alignItems: 'flex-start', animationDelay: `${animDelay}s` }}>
      <BotAvatar />
      <div style={{ flex: 1, minWidth: 0 }}>
        {msg.error ? (
          <ErrorCard error={msg.error} />
        ) : msg.result ? (
          <AnswerCard result={msg.result} papers={papers} />
        ) : null}
      </div>
    </div>
  );
}

/* ── Empty state ── */
function EmptyState({ papers, onSuggest }: { papers: Paper[]; onSuggest: (q: string) => void }) {
  return (
    <div style={{ textAlign: 'center', padding: '60px 20px 40px' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>🔬</div>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, letterSpacing: '-0.5px' }}>
        Research RAG
      </h2>
      <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7, maxWidth: 480, margin: '0 auto 32px' }}>
        Ask questions across your indexed research papers.<br />
        {papers.length > 0
          ? `${papers.length} paper${papers.length > 1 ? 's' : ''} ready — select specific papers in the sidebar to scope your query.`
          : 'Upload a PDF to get started.'}
      </p>

      {papers.length > 0 && (
        <div style={{ textAlign: 'left', maxWidth: 600, margin: '0 auto' }}>
          <p style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 10 }}>
            Suggested questions
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => onSuggest(s)}
                style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  borderRadius: 8, padding: '10px 14px', cursor: 'pointer',
                  fontSize: 13, color: 'var(--text-secondary)', textAlign: 'left', lineHeight: 1.4,
                  transition: 'all .15s',
                }}
                onMouseEnter={e => {
                  const el = e.currentTarget;
                  el.style.borderColor = 'rgba(99,102,241,.5)';
                  el.style.color = '#a5b4fc';
                  el.style.background = 'rgba(99,102,241,.06)';
                }}
                onMouseLeave={e => {
                  const el = e.currentTarget;
                  el.style.borderColor = 'var(--border)';
                  el.style.color = 'var(--text-secondary)';
                  el.style.background = 'var(--bg-card)';
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Error card ── */
function ErrorCard({ error }: { error: string }) {
  return (
    <div style={{
      background: 'rgba(239,68,68,.08)', border: '1px solid rgba(239,68,68,.3)',
      borderRadius: '4px 12px 12px 12px', padding: '12px 16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <span style={{ fontSize: 14 }}>⚠️</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#f87171' }}>Query Failed</span>
      </div>
      <p style={{ fontSize: 13, color: '#fca5a5', lineHeight: 1.5 }}>{error}</p>
    </div>
  );
}

/* ── Avatars & icons ── */
function BotAvatar() {
  return (
    <div style={{
      width: 32, height: 32, borderRadius: 8, flexShrink: 0,
      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 14, marginTop: 2,
    }}>🤖</div>
  );
}
function SendIcon() {
  return (
    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9"/>
    </svg>
  );
}
