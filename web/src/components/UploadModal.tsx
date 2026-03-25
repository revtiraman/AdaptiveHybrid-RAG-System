import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, X, FileText, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { logActivity } from '../lib/history';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type Stage = 'drop' | 'file' | 'uploading' | 'success' | 'error';

const PHASE_LABELS: Record<string, string> = {
  '0':  'Uploading PDF...',
  '20': 'Extracting text...',
  '40': 'Chunking document...',
  '70': 'Generating embeddings...',
  '90': 'Building index...',
};

function getPhaseLabel(pct: number): string {
  const keys = [0, 20, 40, 70, 90];
  const key = [...keys].reverse().find(k => pct >= k) ?? 0;
  return PHASE_LABELS[String(key)];
}

export default function UploadModal({ open, onClose, onSuccess }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [stage, setStage] = useState<Stage>('drop');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [isDragOver, setDragOver] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [result, setResult] = useState<any>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const pickFile = (f: File) => {
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setMessage('Only PDF files are supported.');
      return;
    }
    setFile(f);
    setMessage('');
    setStage('file');
    if (!title) setTitle(f.name.replace(/\.pdf$/i, ''));
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setStage('uploading');
    setProgress(0);
    try {
      const res = await api.upload(file, title || undefined, (pct) => setProgress(pct));
      setResult(res);
      setStage('success');
      logActivity('ingest', `Indexed: ${res.paper?.title ?? title}`);
      onSuccess();
    } catch (err: any) {
      setMessage(err.message ?? 'Upload failed');
      setStage('error');
    }
  };

  const reset = () => {
    setFile(null);
    setTitle('');
    setStage('drop');
    setProgress(0);
    setMessage('');
    setResult(null);
    setAdvancedOpen(false);
  };

  const handleClose = () => { reset(); onClose(); };

  if (!open) return null;

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 500,
        background: 'rgba(0,0,0,0.65)',
        backdropFilter: 'blur(12px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onClick={handleClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 8 }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        onClick={e => e.stopPropagation()}
        style={{
          width: 560,
          background: 'var(--bg-raised)',
          borderRadius: 28,
          boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
          overflow: 'hidden',
          // gradient border
          backgroundClip: 'padding-box',
          border: '1px solid var(--border-default)',
          position: 'relative',
        }}
      >
        {/* Gradient border accent */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: 28,
          background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.1))',
          pointerEvents: 'none', zIndex: 0,
        }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          {/* Header */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '24px 24px 0',
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)' }}>
              {stage === 'success' ? 'Paper indexed!' : stage === 'error' ? 'Upload failed' : 'Upload Paper'}
            </h2>
            <button
              onClick={handleClose}
              style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'var(--bg-overlay)', border: 'none',
                cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--text-muted)',
              }}
            >
              <X size={15} />
            </button>
          </div>

          <div style={{ padding: 24 }}>
            <AnimatePresence mode="wait">
              {stage === 'drop' && (
                <motion.div key="drop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <DropZone
                    isDragOver={isDragOver}
                    onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => inputRef.current?.click()}
                  />
                  {message && (
                    <p style={{ fontSize: 12, color: 'var(--danger-text)', marginTop: 8 }}>{message}</p>
                  )}
                </motion.div>
              )}

              {stage === 'file' && (
                <motion.div key="file" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                  <FilePreview file={file!} onClear={reset} />
                  <div style={{ marginTop: 16 }}>
                    <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                      Title
                    </label>
                    <input
                      value={title}
                      onChange={e => setTitle(e.target.value)}
                      style={{
                        width: '100%', padding: '9px 12px',
                        background: 'var(--bg-sunken)',
                        border: '1px solid var(--border-default)',
                        borderRadius: 8, color: 'var(--text-primary)',
                        fontSize: 14, outline: 'none',
                        fontFamily: 'inherit',
                        boxSizing: 'border-box',
                      }}
                      onFocus={e => (e.currentTarget.style.borderColor = 'var(--brand-500)')}
                      onBlur={e => (e.currentTarget.style.borderColor = 'var(--border-default)')}
                    />
                  </div>

                  <button
                    onClick={() => setAdvancedOpen(!advancedOpen)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      marginTop: 12, background: 'none', border: 'none',
                      cursor: 'pointer', color: 'var(--text-muted)', fontSize: 12, padding: 0,
                    }}
                  >
                    Advanced options
                    <motion.div animate={{ rotate: advancedOpen ? 180 : 0 }} transition={{ duration: 0.15 }}>
                      <ChevronDown size={12} />
                    </motion.div>
                  </button>

                  <AnimatePresence>
                    {advancedOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{ paddingTop: 12 }}>
                          <label style={{
                            display: 'flex', alignItems: 'center', gap: 8,
                            fontSize: 13, color: 'var(--text-secondary)', cursor: 'pointer',
                          }}>
                            <input type="checkbox" defaultChecked style={{ accentColor: 'var(--brand-500)' }} />
                            Section detection
                          </label>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <button
                    onClick={handleUpload}
                    style={{
                      marginTop: 20, width: '100%', padding: '11px',
                      background: 'var(--brand-500)', color: 'white',
                      border: 'none', borderRadius: 10, cursor: 'pointer',
                      fontSize: 14, fontWeight: 600,
                      transition: 'background 150ms',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--brand-400)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'var(--brand-500)')}
                  >
                    Upload & Index
                  </button>
                </motion.div>
              )}

              {stage === 'uploading' && (
                <motion.div
                  key="uploading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '24px 0' }}
                >
                  <CircleProgress value={progress} />
                  <motion.p
                    key={getPhaseLabel(progress)}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ marginTop: 16, fontSize: 14, color: 'var(--text-secondary)' }}
                  >
                    {getPhaseLabel(progress)}
                  </motion.p>
                  {/* Bar */}
                  <div style={{
                    marginTop: 24, width: '100%', height: 4,
                    background: 'var(--bg-sunken)', borderRadius: 999, overflow: 'hidden',
                  }}>
                    <motion.div
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                      style={{
                        height: '100%',
                        background: 'linear-gradient(90deg, var(--brand-600), var(--brand-400))',
                        borderRadius: 999,
                      }}
                    />
                  </div>
                </motion.div>
              )}

              {stage === 'success' && (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0' }}
                >
                  <CheckCircle size={48} style={{ color: 'var(--success-text)' }} />
                  <p style={{ marginTop: 12, fontSize: 16, fontWeight: 500, color: 'var(--text-primary)' }}>
                    Paper indexed successfully!
                  </p>
                  {result?.paper && (
                    <div style={{
                      marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center',
                    }}>
                      {[
                        `${result.paper.chunk_count} chunks`,
                        `${result.paper.page_count} pages`,
                      ].map(s => (
                        <span key={s} style={{
                          fontSize: 12, padding: '3px 8px',
                          background: 'var(--success-bg)', color: 'var(--success-text)',
                          borderRadius: 999, border: '1px solid var(--success-border)',
                        }}>
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
                    <button
                      onClick={handleClose}
                      style={{
                        padding: '8px 16px', background: 'var(--bg-overlay)',
                        border: '1px solid var(--border-default)',
                        borderRadius: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)',
                      }}
                    >
                      Close
                    </button>
                    <button
                      onClick={reset}
                      style={{
                        padding: '8px 16px', background: 'var(--brand-500)',
                        border: 'none', borderRadius: 8, cursor: 'pointer',
                        fontSize: 13, fontWeight: 500, color: 'white',
                      }}
                    >
                      Upload another
                    </button>
                  </div>
                </motion.div>
              )}

              {stage === 'error' && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '16px 0' }}
                >
                  <AlertCircle size={48} style={{ color: 'var(--danger-text)' }} />
                  <p style={{ marginTop: 12, fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>Upload failed</p>
                  {message && (
                    <div style={{
                      marginTop: 10, padding: '10px 14px', width: '100%',
                      background: 'var(--danger-bg)',
                      border: '1px solid var(--danger-border)',
                      borderRadius: 8, fontSize: 13, color: 'var(--danger-text)',
                    }}>
                      {message}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
                    <button
                      onClick={handleClose}
                      style={{
                        padding: '8px 16px', background: 'transparent',
                        border: '1px solid var(--border-default)',
                        borderRadius: 8, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)',
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={reset}
                      style={{
                        padding: '8px 16px', background: 'var(--brand-500)',
                        border: 'none', borderRadius: 8, cursor: 'pointer',
                        fontSize: 13, fontWeight: 500, color: 'white',
                      }}
                    >
                      Try again
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        style={{ display: 'none' }}
        onChange={e => e.target.files?.[0] && pickFile(e.target.files[0])}
      />
    </div>
  );
}

function DropZone({ isDragOver, onDragOver, onDragLeave, onDrop, onClick }: any) {
  return (
    <div
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={onClick}
      style={{
        height: 180,
        border: `2px dashed ${isDragOver ? 'var(--brand-500)' : 'var(--border-default)'}`,
        borderRadius: 14,
        background: isDragOver ? 'rgba(99,102,241,0.08)' : 'var(--bg-sunken)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 8,
        cursor: 'pointer',
        transform: isDragOver ? 'scale(1.01)' : 'scale(1)',
        transition: 'border-color 150ms, background 150ms, transform 150ms',
      }}
    >
      <div className="animate-bob-up">
        <Upload size={36} style={{ color: isDragOver ? 'var(--brand-400)' : 'var(--brand-500)' }} />
      </div>
      <span style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)' }}>
        {isDragOver ? 'Release to upload' : 'Drop your PDF here'}
      </span>
      <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
        {isDragOver ? '' : 'or click to browse'}
      </span>
      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>PDF files only · Max 50MB</span>
    </div>
  );
}

function FilePreview({ file, onClear }: { file: File; onClear: () => void }) {
  const size = file.size < 1024 * 1024
    ? `${(file.size / 1024).toFixed(0)} KB`
    : `${(file.size / 1024 / 1024).toFixed(1)} MB`;

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: 14,
      background: 'var(--bg-sunken)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 12,
    }}>
      <FileText size={40} style={{ color: 'var(--rose-500)', flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 14, fontWeight: 500, color: 'var(--text-primary)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {file.name}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{size} · PDF Document</div>
      </div>
      <button
        onClick={onClear}
        style={{
          width: 28, height: 28,
          background: 'var(--bg-raised)', border: 'none',
          borderRadius: 8, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-muted)', flexShrink: 0,
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
}

function CircleProgress({ value }: { value: number }) {
  const r = 40, cx = 52, cy = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - value / 100);

  return (
    <div style={{ position: 'relative', width: 104, height: 104 }}>
      <svg width={104} height={104}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bg-overlay)" strokeWidth={8} />
        <motion.circle
          cx={cx} cy={cy} r={r} fill="none"
          stroke="var(--brand-500)" strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circ}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          style={{ transform: 'rotate(-90deg)', transformOrigin: '52px 52px' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 18, fontWeight: 700, color: 'var(--text-primary)',
      }}>
        {value}%
      </div>
    </div>
  );
}
