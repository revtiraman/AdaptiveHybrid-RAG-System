import React, { useState, useRef, useCallback } from 'react';
import { uploadPdf } from '../api';

interface Props {
  onClose: () => void;
  onSuccess: () => void;
}

type Stage = 'idle' | 'uploading' | 'success' | 'error';

export default function UploadModal({ onClose, onSuccess }: Props) {
  const [file, setFile]         = useState<File | null>(null);
  const [title, setTitle]       = useState('');
  const [stage, setStage]       = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [message, setMessage]   = useState('');
  const [isDragOver, setDragOver] = useState(false);
  const inputRef                = useRef<HTMLInputElement>(null);

  const pickFile = (f: File) => {
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      setMessage('Only PDF files are supported.');
      return;
    }
    setFile(f);
    setMessage('');
    if (!title) setTitle(f.name.replace(/\.pdf$/i, ''));
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) pickFile(f);
  }, [title]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) pickFile(f);
  };

  const handleUpload = async () => {
    if (!file || stage === 'uploading') return;
    setStage('uploading');
    setProgress(0);
    setMessage('');
    try {
      const result = await uploadPdf(file, title || undefined, pct => setProgress(pct));
      setStage('success');
      setMessage(
        `✅ Indexed "${result.paper.title}" — ` +
        `${result.paper.page_count} pages, ${result.paper.chunk_count} chunks, ` +
        `${result.paper.claims_extracted} claims extracted.`
      );
      setTimeout(onSuccess, 1800);
    } catch (err) {
      setStage('error');
      setMessage(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  const reset = () => {
    setFile(null); setTitle(''); setStage('idle'); setProgress(0); setMessage('');
  };

  return (
    <div
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200,
      }}
    >
      <div className="animate-fade-up" style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 14, width: 480, maxWidth: '92vw',
        boxShadow: '0 32px 80px rgba(0,0,0,.7)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>Upload PDF</span>
          <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--text-muted)', fontSize:20, lineHeight:1 }}>×</button>
        </div>

        <div style={{ padding: '20px' }}>
          {/* Drop zone */}
          <div
            onClick={() => inputRef.current?.click()}
            onDrop={onDrop}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            style={{
              border: `2px dashed ${isDragOver ? '#6366f1' : file ? '#10b981' : 'var(--border-light)'}`,
              borderRadius: 10, padding: '28px 20px', textAlign: 'center',
              cursor: 'pointer', background: isDragOver ? 'rgba(99,102,241,.06)' : 'var(--bg-input)',
              transition: 'all .15s', marginBottom: 16,
            }}
          >
            <div style={{ fontSize: 32, marginBottom: 8 }}>{file ? '📄' : '☁️'}</div>
            {file ? (
              <>
                <p style={{ fontSize: 14, fontWeight: 600, color: '#10b981', marginBottom: 4 }}>{file.name}</p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </>
            ) : (
              <>
                <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4 }}>
                  Drop a PDF here or click to browse
                </p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>PDF files only</p>
              </>
            )}
            <input ref={inputRef} type="file" accept=".pdf" onChange={onFileChange} style={{ display:'none' }} />
          </div>

          {/* Title input */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display:'block', fontSize:12, fontWeight:600, color:'var(--text-secondary)', marginBottom:5 }}>
              Title (optional)
            </label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Paper title…"
              style={{
                width:'100%', background:'var(--bg-input)', border:'1px solid var(--border)',
                borderRadius:7, padding:'8px 12px', color:'var(--text-primary)',
                fontSize:13, outline:'none',
              }}
            />
          </div>

          {/* Progress bar */}
          {stage === 'uploading' && (
            <div style={{ marginBottom: 14 }}>
              <div style={{ display:'flex', justifyContent:'space-between', fontSize:11, color:'var(--text-muted)', marginBottom:5 }}>
                <span>{progress < 100 ? 'Uploading…' : 'Processing & indexing…'}</span>
                <span>{progress}%</span>
              </div>
              <div className="quality-bar-track">
                <div className="quality-bar-fill" style={{ width:`${progress}%`, background:'#6366f1' }} />
              </div>
            </div>
          )}

          {/* Message */}
          {message && (
            <div style={{
              fontSize:12, lineHeight:1.6, padding:'8px 12px', borderRadius:7, marginBottom:14,
              background: stage === 'error' ? 'rgba(239,68,68,.1)' : 'rgba(16,185,129,.1)',
              border: `1px solid ${stage === 'error' ? 'rgba(239,68,68,.3)' : 'rgba(16,185,129,.3)'}`,
              color: stage === 'error' ? '#f87171' : '#6ee7b7',
            }}>
              {message}
            </div>
          )}

          {/* Actions */}
          <div style={{ display:'flex', gap:8, justifyContent:'flex-end' }}>
            {stage === 'error' && (
              <button onClick={reset} style={secondaryBtn}>Try again</button>
            )}
            {stage !== 'success' && (
              <button onClick={onClose} style={secondaryBtn}>Cancel</button>
            )}
            {stage !== 'success' && stage !== 'uploading' && (
              <button
                onClick={handleUpload}
                disabled={!file}
                style={{
                  background: file ? 'var(--accent)' : 'var(--bg-hover)',
                  border:'none', color: file ? '#fff' : 'var(--text-muted)',
                  borderRadius:7, padding:'8px 20px', cursor: file ? 'pointer' : 'default',
                  fontSize:13, fontWeight:600, transition:'all .15s',
                }}
              >
                Index Paper
              </button>
            )}
            {stage === 'uploading' && (
              <button disabled style={{ ...secondaryBtn, display:'flex', alignItems:'center', gap:6 }}>
                <span className="spinner" /> Indexing…
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const secondaryBtn: React.CSSProperties = {
  background:'none', border:'1px solid var(--border)', borderRadius:7,
  color:'var(--text-secondary)', padding:'8px 16px', cursor:'pointer', fontSize:13,
};
