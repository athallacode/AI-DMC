'use client';
import Link from 'next/link';
import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import Shell from '@/components/shell';
import { Confidence, Empty, ErrorMessage, Preview, Status } from '@/components/ui';
import { Correction } from '@/components/correction';
import { API, api, date, Document, token } from '@/lib/api';
import { judulDokumen } from '@/lib/format';
export default function VerificationPage() {
  const [docs,setDocs] = useState<Document[]>([]); const [error,setError] = useState(''); const [loading,setLoading] = useState(true); const [correction,setCorrection] = useState<Document | null>(null); const [pending,setPending] = useState<{id:string;action:string} | null>(null); const [sending,setSending] = useState(false); const [notice,setNotice] = useState(''); const timer = useRef<ReturnType<typeof setTimeout> | null>(null); const noticeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Satu dokumen tampil penuh dalam satu waktu; antrean di samping untuk berpindah.
  const [active,setActive] = useState(0); const [showMissing,setShowMissing] = useState(false);
  const refresh = useCallback(async () => { if (!token()) return; try {const summaries = await api<Document[]>('/documents?status=menunggu_verifikasi'); setDocs(await Promise.all(summaries.map(doc => api<Document>(`/documents/${doc.id}`))));} catch(e) {setError(e instanceof Error ? e.message : 'Dokumen belum dapat dimuat.');} finally {setLoading(false);} }, []);
  // Aksi yang masih dalam jeda Urungkan. Kalau laman ditinggalkan, aksi langsung dikirim agar tidak hilang diam-diam.
  const queued = useRef<{id:string;action:string} | null>(null);
  useEffect(() => {
    function flush() {const item = queued.current; if(!item) return; queued.current = null; if(timer.current) clearTimeout(timer.current); fetch(`${API}/documents/${item.id}/${item.action}`, {method:'POST', keepalive:true, headers:{Authorization:`Bearer ${token()}`}}).catch(() => {});}
    window.addEventListener('pagehide', flush);
    return () => {window.removeEventListener('pagehide', flush); flush();};
  }, []);
  useEffect(() => {void refresh(); return () => {if(timer.current) clearTimeout(timer.current); if(noticeTimer.current) clearTimeout(noticeTimer.current);};}, [refresh]);
  function schedule(doc:Document,action:'approve'|'reject') {if(pending || sending) return; setError(''); setNotice(''); setPending({id:doc.id,action}); queued.current = {id:doc.id,action}; timer.current = setTimeout(async () => {queued.current = null;setSending(true); try {await api(`/documents/${doc.id}/${action}`, {method:'POST'}); setNotice(action === 'approve' ? 'Dokumen disetujui dan masuk arsip.' : 'Dokumen ditolak.'); await refresh(); noticeTimer.current = setTimeout(() => setNotice(''),3000);} catch(e) {setError(e instanceof Error ? e.message : 'Aksi belum berhasil.');} finally {setPending(null);setSending(false);}},3000);}
  function undo() {if(timer.current) clearTimeout(timer.current);queued.current = null;setPending(null);setNotice('Aksi dibatalkan.'); noticeTimer.current = setTimeout(() => setNotice(''),3000);}
  function pick(index:number) {setActive(index); setShowMissing(false);}
  const index = Math.min(active, Math.max(docs.length - 1, 0)); const doc = docs[index];
  const fields: [string, string | null | undefined][] = doc ? [['Judul',doc.judul],['Nomor dokumen',doc.nomor_dokumen],['Tanggal terbit',doc.tanggal_terbit ? date(doc.tanggal_terbit) : null],['Periode',doc.periode],['Mitra / penerbit',doc.metadata_lain?.mitra_penerbit],['Sumber dana',doc.metadata_lain?.sumber_dana],['DOI / ISSN / ISBN',doc.metadata_lain?.identifier]] : [];
  // Judul yang terbaca sudah jadi judul kartu, jadi tidak diulang di daftar data.
  const found = fields.filter(([label,value]) => value && label !== 'Judul'); const missing = fields.filter(([,value]) => !value);
  const list = (items: typeof fields) => items.map(([label,value]) => <div key={label}><dt>{label}</dt><dd className={!value ? 'missing' : ''}>{value || 'Tidak ditemukan'}</dd></div>);
  const percent = (value?: number | null) => value == null ? '' : ` · ${Math.round(value * 100)}%`;
  return <Shell refreshKey={docs.length}><div className="page-heading"><div><h1>Kotak Verifikasi</h1><p>{loading ? 'Memuat dokumen…' : `${docs.length} dokumen menunggu konfirmasi`}</p></div></div><ErrorMessage message={error} />{!loading && docs.length === 0 && <Empty title="Semua sudah dicek" text="Belum ada dokumen yang menunggu konfirmasi."><Link className="secondary button" href="/unggah">Unggah dokumen</Link></Empty>}
    {doc && <div className="workspace">
      <nav className="queue card" aria-label="Antrean verifikasi"><ul>{docs.map((item,i) => <li key={item.id}><button aria-current={i === index ? 'true' : undefined} onClick={() => pick(i)}><span className="queue-title">{judulDokumen(item)}</span><span className="meta">{item.jenis || 'Jenis belum terbaca'}{percent(item.skor_keyakinan)}</span></button></li>)}</ul></nav>
      <div className="focus-area">
        <div className="stepper"><span>Dokumen {index + 1} dari {docs.length}</span><div><button aria-label="Dokumen sebelumnya" disabled={index === 0} onClick={() => pick(index - 1)}><ChevronLeft size={18} /></button><button aria-label="Dokumen berikutnya" disabled={index === docs.length - 1} onClick={() => pick(index + 1)}><ChevronRight size={18} /></button></div></div>
        <article key={doc.id} className="verification-card card"><Preview doc={doc} compact /><div className="document-info">
          <div className="document-heading"><h2>{judulDokumen(doc)}</h2></div>
          <p className="file-line"><span>{doc.nama_berkas}</span><Status status={doc.status} /></p>
          <Confidence value={doc.skor_keyakinan} needsReview={doc.status === 'menunggu_verifikasi'} />
          <p className="breadcrumb">{[doc.kategori,doc.subkategori,doc.jenis].filter(Boolean).join(' › ') || 'Tidak ditemukan'}</p>
          {doc.ringkasan && <p className="summary"><span>Ringkasan AI</span>{doc.ringkasan}</p>}
          {found.length > 0 && <dl className="metadata">{list(found)}</dl>}
          {missing.length > 0 && <><button className="text-button missing-toggle" aria-expanded={showMissing} onClick={() => setShowMissing(open => !open)}><ChevronDown size={16} aria-hidden="true" />{missing.length} data tidak ditemukan</button>{showMissing && <dl className="metadata missing-list">{list(missing)}</dl>}</>}
          <div className="related"><h3>Dosen terkait</h3>{doc.dosen_terkait?.length ? <>{doc.dosen_terkait.map((d,i) => <p key={i}>{d.nama}{d.peran ? ` · ${d.peran}` : ''}</p>)}<span className="meta">{doc.dosen_terkait.every(d => d.dikonfirmasi) ? 'Sudah dikonfirmasi.' : 'Dikonfirmasi saat Anda menyetujui.'}</span></> : <p className="missing">Tidak ditemukan</p>}</div>
          <div className="document-actions"><button className="destructive" disabled={!!pending || sending} onClick={() => schedule(doc,'reject')}>Tolak</button><button className="secondary" disabled={!!pending || sending} onClick={() => setCorrection(doc)}>Koreksi</button><button className="primary" disabled={!!pending || sending} onClick={() => schedule(doc,'approve')}>{pending?.id === doc.id ? sending ? 'Menyimpan…' : 'Menunggu konfirmasi…' : 'Setujui'}</button></div>
        </div></article>
      </div>
    </div>}
    {(pending || notice) && <div className="toast glass" role="status"><span>{pending ? sending ? 'Menyimpan perubahan…' : `Akan ${pending.action === 'approve' ? 'menyetujui' : 'menolak'} dokumen dalam 3 detik.` : notice}</span>{pending && !sending && <button className="text-button" onClick={undo}>Urungkan</button>}</div>}{correction && <Correction doc={correction} onClose={() => setCorrection(null)} onSaved={() => {void refresh();}} />}</Shell>;
}
