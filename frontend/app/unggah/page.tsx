'use client';
import Link from 'next/link';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, ChevronDown, ChevronUp, FileUp, FileText, Image as ImageIcon, X } from 'lucide-react';
import Shell from '@/components/shell';
import { Empty, ErrorMessage, Status } from '@/components/ui';
import { api, Document, token } from '@/lib/api';
import { judulDokumen, waktuUnggah } from '@/lib/format';
type QueueItem = { key: string; name: string; id?: string; state: string; message?: string };
type UploadResult = { documents: Document[]; duplicates: {nama_berkas: string; message: string; document_id?: string}[]; errors: {nama_berkas: string; message: string}[] };
const KUNCI_KECIL = 'ai-dmc-antrean-kecil';
export default function UploadPage() {
  const [docs, setDocs] = useState<Document[]>([]); const [queue, setQueue] = useState<QueueItem[]>([]); const [error, setError] = useState(''); const [drag, setDrag] = useState(false); const [busy, setBusy] = useState(false); const input = useRef<HTMLInputElement>(null); const camera = useRef<HTMLInputElement>(null);
  // Panel antrean bisa dikecilkan supaya tidak menutupi daftar; pilihannya diingat di browser ini saja.
  const [small, setSmall] = useState(false); const [finished, setFinished] = useState<{text: string; review: boolean} | null>(null); const wasProcessing = useRef(false); const finishedTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => { try { setSmall(localStorage.getItem(KUNCI_KECIL) === '1'); } catch {} return () => { if (finishedTimer.current) clearTimeout(finishedTimer.current); }; }, []);
  function toggleSmall() { setSmall(value => { try { localStorage.setItem(KUNCI_KECIL, value ? '' : '1'); } catch {} return !value; }); }
  const refresh = useCallback(() => { if (token()) api<Document[]>('/documents').then(setDocs).catch(e => setError(e.message)); }, []);
  useEffect(refresh, [refresh]);
  const processing = queue.some(item => item.id && item.state === 'diproses');
  const remaining = queue.filter(item => item.state === 'diproses' || item.state === 'mengunggah').length;
  const failed = queue.filter(item => item.state === 'gagal').length;
  useEffect(() => { if (!processing) return; let cancelled = false; const interval = setInterval(async () => { try { const results = await Promise.all(queue.filter(item => item.id && item.state === 'diproses').map(async item => ({ id: item.id, doc: await api<Document>(`/documents/${item.id}`) }))); if (!cancelled) { setQueue(items => items.map(item => { const result = results.find(result => result.id === item.id); return result ? {...item, state: result.doc.status, message: result.doc.error || undefined} : item; })); refresh(); } } catch(e) { if (!cancelled) setError(e instanceof Error ? e.message : 'Status belum dapat diperbarui.'); } }, 2500); return () => { cancelled = true; clearInterval(interval); }; }, [processing, queue, refresh]);
  // Beri tahu sekali saat semua dokumen di antrean selesai diproses AI.
  useEffect(() => {
    if (wasProcessing.current && !processing) {
      const done = queue.filter(item => item.id), review = done.filter(item => item.state === 'menunggu_verifikasi').length;
      if (done.length) { setFinished({text: review ? `${done.length} dokumen selesai diproses. ${review} perlu dicek.` : `${done.length} dokumen selesai diproses.`, review: review > 0}); if (finishedTimer.current) clearTimeout(finishedTimer.current); finishedTimer.current = setTimeout(() => setFinished(null), 8000); }
    }
    wasProcessing.current = processing;
  }, [processing, queue]);
  async function upload(files: FileList | File[] | null) {
    if (!files?.length || busy) return;
    setError(''); const selected = Array.from(files); const valid: File[] = []; const rejected: QueueItem[] = [];
    for (const file of selected) { if (!/\.(pdf|docx|jpe?g|png)$/i.test(file.name)) rejected.push({key: crypto.randomUUID(), name: file.name, state: 'gagal', message: 'Gunakan PDF, DOCX, JPG, atau PNG.'}); else if (file.size > 20 * 1024 * 1024) rejected.push({key: crypto.randomUUID(), name: file.name, state: 'gagal', message: 'Ukuran maksimal 20 MB per berkas.'}); else valid.push(file); }
    setQueue(items => [...items, ...rejected]); if (!valid.length) return; setBusy(true);
    const entries = valid.map(file => ({key: crypto.randomUUID(), name: file.name, state: 'mengunggah'})); setQueue(items => [...items, ...entries]);
    try { const data = new FormData(); valid.forEach(file => data.append('files', file)); const result = await api<UploadResult>('/documents', {method: 'POST', body: data});
      const completed: QueueItem[] = [...result.documents.map(doc => ({key: crypto.randomUUID(), name: doc.nama_berkas, id: doc.id, state: doc.status})), ...result.duplicates.map(item => ({key: crypto.randomUUID(), name: item.nama_berkas, state: 'duplikat', message: item.message})), ...result.errors.map(item => ({key: crypto.randomUUID(), name: item.nama_berkas, state: 'gagal', message: item.message}))];
      setQueue(items => [...items.filter(item => !entries.some(entry => entry.key === item.key)), ...completed]); refresh();
    } catch (e) { const message = e instanceof Error ? e.message : 'Unggah belum berhasil. Coba lagi.'; setError(message); setQueue(items => items.map(item => entries.some(entry => entry.key === item.key) ? {...item, state: 'gagal', message} : item)); } finally {setBusy(false); if(input.current) input.current.value = ''; if(camera.current) camera.current.value = ''; }
  }
  const status = (item: QueueItem) => item.message || (item.state === 'mengunggah' ? 'Mengunggah' : item.state === 'diproses' ? 'Memproses dokumen' : item.state === 'menunggu_verifikasi' ? 'Selesai · Perlu verifikasi' : 'Selesai');
  return <Shell refreshKey={docs.length}><div className="page-heading"><div><h1>Unggah</h1><p>Tambahkan dokumen untuk diproses dan diarsipkan.</p></div></div><ErrorMessage message={error} /><section aria-label="Area unggah" className={`dropzone ${drag ? 'dragging' : ''}`} onDragOver={e => {e.preventDefault(); setDrag(true);}} onDragLeave={() => setDrag(false)} onDrop={e => {e.preventDefault(); setDrag(false); void upload(e.dataTransfer.files);}}><span className="app-icon"><FileUp size={24} strokeWidth={1.75} aria-hidden="true" /></span><h2>Seret berkas ke sini atau pilih berkas</h2><p>PDF, DOCX, JPG, PNG · Maksimal 20 MB per berkas · Sekitar 1 menit per dokumen</p><button className="primary" disabled={busy} onClick={() => input.current?.click()}>{busy ? 'Mengunggah…' : 'Pilih berkas'}</button><button className="neutral camera-button" disabled={busy} onClick={() => camera.current?.click()}><Camera size={18} />Pindai dengan kamera</button><input ref={input} type="file" hidden multiple accept=".pdf,.docx,.jpg,.jpeg,.png" onChange={e => void upload(e.target.files)} /><input ref={camera} type="file" hidden accept="image/jpeg,image/png" capture="environment" onChange={e => void upload(e.target.files)} /></section>
    <section className={`recent ${queue.length ? 'with-queue' : ''}`}><div className="section-heading"><h2>Unggahan terakhir</h2><Link href="/arsip">Lihat Arsip Saya</Link></div><div className="card grouped-list">{docs.length ? docs.slice(0,5).map(doc => { const time = waktuUnggah(doc.created_at); return <div key={doc.id} className="recent-row"><span className="file-icon">{/\.(png|jpe?g)$/i.test(doc.nama_berkas) ? <ImageIcon size={18} aria-hidden="true" /> : <FileText size={18} aria-hidden="true" />}</span><div className="list-text"><strong title={doc.nama_berkas}>{judulDokumen(doc)}</strong><span className="meta"><time dateTime={doc.created_at} title={time.lengkap}>{time.teks}</time> · {doc.nama_berkas.split('.').pop()?.toUpperCase()}</span></div><Status status={doc.status} /></div>; }) : <Empty text="Belum ada dokumen yang diunggah." />}</div></section>
    {queue.length > 0 && (small
      ? <aside className="upload-queue glass compact" aria-label="Antrean unggah" aria-live="polite"><button className="queue-pill" aria-expanded={false} onClick={toggleSmall}><span>{remaining ? `Memproses ${remaining} dokumen · sekitar ${remaining} menit` : failed ? `${failed} berkas gagal diunggah` : 'Antrean unggah selesai'}</span><ChevronUp size={16} aria-hidden="true" /><span className="sr-only">Tampilkan rincian antrean</span></button>{remaining > 0 && <progress aria-label="Proses antrean" />}</aside>
      : <aside className="upload-queue glass" aria-label="Antrean unggah" aria-live="polite"><div className="section-heading queue-heading"><div><h2>{remaining ? `Memproses ${remaining} dokumen` : 'Antrean unggah'}</h2>{remaining > 0 && <p className="meta">Sekitar {remaining} menit lagi. Proses tetap berjalan walau laman ini ditinggal.</p>}</div><div className="queue-tools"><button className="icon-button" aria-label="Kecilkan antrean" aria-expanded={true} onClick={toggleSmall}><ChevronDown size={18} /></button><button className="text-button" disabled={busy || processing} onClick={() => setQueue([])}><X size={16} />Tutup</button></div></div>{queue.map(item => <div key={item.key} className="queue-row"><strong>{item.name}</strong><span className={item.state === 'gagal' ? 'queue-error' : 'meta'}>{status(item)}</span>{(item.state === 'mengunggah' || item.state === 'diproses') && <progress aria-label={`Proses ${item.name}`} />}</div>)}</aside>)}
    {finished && <div className="toast glass" role="status"><span>{finished.text}</span><Link className="text-button" href={finished.review ? '/verifikasi' : '/arsip'}>{finished.review ? 'Buka Kotak Verifikasi' : 'Buka Arsip Saya'}</Link></div>}</Shell>;
}
