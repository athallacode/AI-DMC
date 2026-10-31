'use client';
import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { X, FileText, CircleAlert, ArrowUpRight } from 'lucide-react';
import { Document, getFile, statusLabels } from '@/lib/api';

export function Status({ status }: { status: string }) { return <span className={`status ${status}`}>{status === 'gagal' && <CircleAlert size={12} aria-hidden="true" />}{statusLabels[status] || status}</span>; }
export const ConfidenceThreshold = createContext(.85);
export function Confidence({ value, needsReview = false }: { value?: number | null; needsReview?: boolean }) {
  const threshold = useContext(ConfidenceThreshold);
  if (value == null) return null;
  const low = value < threshold || needsReview;
  return <div className="confidence"><div><span>Keyakinan AI {Math.round(value * 100)}%</span><span className="confidence-track"><span style={{ width: `${Math.min(100, Math.max(0, value * 100))}%` }} className={low ? 'low' : ''} /></span></div>{low && <p>AI kurang yakin, mohon dicek.</p>}</div>;
}
export function Empty({ text, children, title }: { text: string; children?: React.ReactNode; title?: string }) { return <section className="empty" aria-label={title || text}><span className="app-icon"><FileText size={24} strokeWidth={1.75} aria-hidden="true" /></span>{title && <h2>{title}</h2>}<p>{text}</p>{children}</section>; }
export function ErrorMessage({ message }: { message: string }) { return message ? <p className="error-message" role="alert"><CircleAlert size={18} aria-hidden="true" />{message}</p> : null; }
export function Modal({ title, children, onClose, wide = false }: { title: string; children: React.ReactNode; onClose: () => void; wide?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    ref.current?.focus();
    function handle(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const nodes = Array.from(ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], iframe[tabindex="0"]') || []);
        const first = nodes[0], last = nodes[nodes.length - 1];
        if (!first) { event.preventDefault(); return; }
        if (event.shiftKey && (document.activeElement === first || document.activeElement === ref.current)) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && (document.activeElement === last || document.activeElement === ref.current)) { event.preventDefault(); first.focus(); }
      }
    }
    document.addEventListener('keydown', handle);
    return () => { document.body.style.overflow = oldOverflow; document.removeEventListener('keydown', handle); previous?.focus(); };
  }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} className={`modal glass ${wide ? 'wide' : ''}`}><div className="modal-heading"><h2>{title}</h2><button className="text-button close-button" onClick={onClose}><X size={18} />Tutup</button></div>{children}</div></div>;
}
export function Preview({ doc, compact = false, allowExpand = true }: { doc: Document; compact?: boolean; allowExpand?: boolean }) {
  const [url, setUrl] = useState(''); const [error, setError] = useState(''); const [open, setOpen] = useState(false);
  useEffect(() => { let live = true; let objectUrl = ''; getFile(doc.id).then(value => { objectUrl = value; if (live) setUrl(value); else URL.revokeObjectURL(value); }).catch(e => { if (live) setError(e.message); }); return () => { live = false; if (objectUrl) URL.revokeObjectURL(objectUrl); }; }, [doc.id]);
  const pdf = doc.nama_berkas.toLowerCase().endsWith('.pdf');
  const image = /\.(png|jpe?g)$/i.test(doc.nama_berkas);
  const content = image ? <img src={url} alt={`Pratinjau ${doc.nama_berkas}`} /> : pdf ? <iframe tabIndex={-1} src={`${url}#toolbar=0`} title={`Pratinjau ${doc.nama_berkas}`} /> : <div className="empty"><span className="app-icon"><FileText size={24} aria-hidden="true" /></span><p>Pratinjau DOCX tersedia melalui unduhan.</p></div>;
  return <><div className={`preview ${compact ? 'compact' : ''}`}>{error ? <ErrorMessage message={error} /> : !url ? <p className="muted">Memuat pratinjau…</p> : content}{url && <div className="preview-actions">{allowExpand && (pdf || image) && <button className="text-button" onClick={() => setOpen(true)}>Perbesar<ArrowUpRight size={16} /></button>}<a href={url} download={doc.nama_berkas}>Unduh berkas</a></div>}</div>{open && <Modal title={doc.nama_berkas} onClose={() => setOpen(false)} wide><div className="preview expanded">{content}</div></Modal>}</>;
}
