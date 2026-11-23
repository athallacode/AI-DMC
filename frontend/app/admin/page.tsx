'use client';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { ChevronDown, Copy, Download, FileUp, RotateCcw, Search, UserPlus } from 'lucide-react';
import Shell from '@/components/shell';
import { Empty, ErrorMessage, Modal, Status, required } from '@/components/ui';
import { API, api, token, User } from '@/lib/api';

type Akun = { id: string; username: string; nama: string; nip: string | null; peran: string; jumlah_dokumen: number; ditutup: boolean };
type DokumenGagal = { id: string; nama_berkas: string; pengunggah: string; created_at: string; keterangan: string | null };
type DokumenRingkas = { id: string; nama_berkas: string; pengunggah: string; status: string; created_at: string };
type DokumenDitolak = { id: string; nama_berkas: string; pengunggah: string; created_at: string; ditolak_at: string };
type Log = { created_at: string; username: string; nama: string; aksi: string; document_id: string | null; oleh: string | null };
type Password = { judul: string; baris: { username: string; nama?: string; password: string }[]; dilewati?: string[] };
type Tab = 'akun' | 'dokumen' | 'log';

const LABEL_AKSI: Record<string, string> = {
  login: 'Masuk', login_gagal: 'Gagal masuk', upload: 'Unggah dokumen', unduh: 'Unduh dokumen', approve: 'Setujui dokumen',
  reject: 'Tolak dokumen', koreksi: 'Koreksi dokumen', kelola_buat_akun: 'Akun dibuat', kelola_reset_password: 'Password direset',
  kelola_tutup_akun: 'Akun ditutup', kelola_proses_ulang: 'Dokumen diproses ulang', kelola_tautkan: 'Dosen ditautkan',
  kelola_batal_tolak: 'Penolakan dibatalkan', kelola_ubah_akun: 'Akun diubah',
};
const waktu = (value: string) => new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));

export default function AdminPage() {
  const [me, setMe] = useState<User | null>(null); const [tab, setTab] = useState<Tab>('akun'); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  useEffect(() => { if (token()) api<User>('/auth/me').then(setMe).catch(e => setError(e.message)); }, []);
  if (me && me.peran !== 'admin') return <Shell><Empty title="Khusus admin" text="Laman ini hanya untuk akun admin CoE." /></Shell>;
  return <Shell><div className="page-heading"><div><h1>Admin</h1><p>Kelola akun dosen, dokumen yang gagal diproses, dan lihat aktivitas.</p></div></div>
    <div className="segmented admin-tabs" role="tablist" aria-label="Bagian admin">{([['akun', 'Akun'], ['dokumen', 'Dokumen'], ['log', 'Log aktivitas']] as [Tab, string][]).map(([value, label]) => <button key={value} role="tab" aria-selected={tab === value} className={tab === value ? 'selected' : ''} onClick={() => { setTab(value); setError(''); setNotice(''); }}>{label}</button>)}</div>
    <ErrorMessage message={error} />{notice && <p className="admin-notice" role="status">{notice}</p>}
    {me && tab === 'akun' && <AkunTab me={me} setError={setError} setNotice={setNotice} />}
    {me && tab === 'dokumen' && <DokumenTab setError={setError} setNotice={setNotice} />}
    {me && tab === 'log' && <LogTab setError={setError} />}
  </Shell>;
}

function AkunTab({ me, setError, setNotice }: { me: User; setError: (v: string) => void; setNotice: (v: string) => void }) {
  const [akun, setAkun] = useState<Akun[]>([]); const [loading, setLoading] = useState(true); const [cari, setCari] = useState(''); const [tambah, setTambah] = useState(false);
  const [ubah, setUbah] = useState<Akun | null>(null);
  const [konfirmasi, setKonfirmasi] = useState<{ akun: Akun; aksi: 'reset' | 'tutup' } | null>(null); const [password, setPassword] = useState<Password | null>(null); const [busy, setBusy] = useState(false);
  const berkas = useRef<HTMLInputElement>(null);
  const muat = useCallback(() => { setLoading(true); api<Akun[]>('/admin/akun').then(setAkun).catch(e => setError(e.message)).finally(() => setLoading(false)); }, [setError]);
  useEffect(() => { muat(); }, [muat]);
  const terms = cari.toLowerCase().trim();
  const shown = terms ? akun.filter(a => [a.nama, a.username, a.nip].filter(Boolean).join(' ').toLowerCase().includes(terms)) : akun;
  async function jalankan() {
    if (!konfirmasi) return; setBusy(true); setError('');
    try {
      if (konfirmasi.aksi === 'reset') { const r = await api<{ username: string; password: string }>(`/admin/akun/${konfirmasi.akun.id}/reset-password`, { method: 'POST' }); setPassword({ judul: 'Password baru', baris: [{ username: r.username, nama: konfirmasi.akun.nama, password: r.password }] }); }
      else { await api(`/admin/akun/${konfirmasi.akun.id}/tutup`, { method: 'POST' }); setNotice(`Akun ${konfirmasi.akun.username} ditutup. Dokumennya tetap tersimpan.`); }
      setKonfirmasi(null); muat();
    } catch (e) { setError(e instanceof Error ? e.message : 'Aksi belum berhasil.'); } finally { setBusy(false); }
  }
  async function impor(file: File) {
    setError(''); setNotice(''); const form = new FormData(); form.append('berkas', file);
    try { const r = await api<{ dibuat: { username: string; nama: string; password: string }[]; dilewati: string[] }>('/admin/akun/impor', { method: 'POST', body: form }); setPassword({ judul: `${r.dibuat.length} akun dibuat`, baris: r.dibuat, dilewati: r.dilewati }); muat(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Impor belum berhasil.'); }
    finally { if (berkas.current) berkas.current.value = ''; }
  }
  return <section aria-label="Akun">
    <div className="admin-toolbar"><label className="admin-search">Cari akun<span className="search-wrap"><Search size={16} aria-hidden="true" /><input type="search" value={cari} onChange={e => setCari(e.target.value)} placeholder="Nama, username, atau NIP" /></span></label>
      <div className="admin-actions"><button className="neutral" onClick={() => berkas.current?.click()}><FileUp size={16} aria-hidden="true" />Impor CSV</button><input ref={berkas} type="file" accept=".csv,text/csv" hidden onChange={e => { const f = e.target.files?.[0]; if (f) void impor(f); }} /><button className="primary" onClick={() => setTambah(true)}><UserPlus size={16} aria-hidden="true" />Tambah akun</button></div></div>
    <p className="results-count" aria-live="polite">{loading ? 'Memuat akun…' : `${shown.length} akun`}</p>
    {!loading && shown.length === 0 ? <Empty title="Tidak ada akun" text="Tidak ada akun yang cocok dengan pencarian." /> :
      <ul className="card admin-list">{shown.map(a => <li key={a.id}><div className="list-text"><strong>{a.nama}</strong><span className="meta">{a.username} · {a.nip ? `NIP ${a.nip}` : 'Tanpa NIP'} · {a.jumlah_dokumen} dokumen</span></div>
        <div className="admin-row-end">{a.peran === 'admin' && <span className="status diproses">Admin</span>}{a.ditutup ? <span className="status ditolak">Ditutup</span> : <span className="status terverifikasi">Aktif</span>}
          <span className="admin-row-actions"><button className="text-button admin-edit" onClick={() => setUbah(a)}>Ubah</button>
          <button className="text-button" onClick={() => setKonfirmasi({ akun: a, aksi: 'reset' })}>{a.ditutup ? 'Buka lagi' : 'Reset password'}</button>
          {a.id === me.id ? <span className="meta admin-slot">Akun Anda</span> : a.ditutup ? <span className="admin-slot" aria-hidden="true" /> : <button className="destructive admin-slot" onClick={() => setKonfirmasi({ akun: a, aksi: 'tutup' })}>Tutup</button>}</span></div></li>)}</ul>}
    <details className="admin-help"><summary>Format CSV untuk impor</summary><p className="meta">Kolom <code>username</code> dan <code>nama</code> wajib, <code>nip</code> dan <code>peran</code> boleh kosong. Simpan dari Excel sebagai CSV UTF-8. Baris yang bermasalah dilewati, baris lain tetap dibuat.</p></details>
    {tambah && <TambahAkun onClose={() => setTambah(false)} onDone={p => { setTambah(false); setPassword(p); muat(); }} />}
    {ubah && <UbahAkun akun={ubah} onClose={() => setUbah(null)} onDone={teks => { setUbah(null); setNotice(teks); muat(); }} />}
    {konfirmasi && <Modal title={konfirmasi.aksi === 'tutup' ? 'Tutup akun?' : konfirmasi.akun.ditutup ? 'Buka lagi akun ini?' : 'Reset password?'} onClose={() => setKonfirmasi(null)}>
      <p>{konfirmasi.akun.nama} ({konfirmasi.akun.username})</p>
      <p className="meta">{konfirmasi.aksi === 'tutup' ? 'Akun tidak bisa dipakai masuk lagi. Dokumennya tetap tersimpan. Sesi yang sedang terbuka tetap berlaku paling lama 60 menit.' : 'Password lama tidak berlaku lagi. Password baru tampil sekali setelah ini.'}</p>
      <div className="form-actions"><button className="neutral" onClick={() => setKonfirmasi(null)}>Batal</button><button className={konfirmasi.aksi === 'tutup' ? 'danger' : 'primary'} disabled={busy} onClick={() => void jalankan()}>{busy ? 'Memproses…' : konfirmasi.aksi === 'tutup' ? 'Tutup akun' : 'Buat password baru'}</button></div></Modal>}
    {password && <PasswordModal data={password} onClose={() => setPassword(null)} />}
  </section>;
}

function TambahAkun({ onClose, onDone }: { onClose: () => void; onDone: (p: Password) => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true); const data = new FormData(event.currentTarget);
    try { const r = await api<{ username: string; nama: string; password: string }>('/admin/akun', { method: 'POST', body: JSON.stringify({ username: data.get('username'), nama: data.get('nama'), nip: data.get('nip') || null, peran: data.get('peran') }) }); onDone({ judul: 'Akun dibuat', baris: [r] }); }
    catch (e) { setError(e instanceof Error ? e.message : 'Akun belum berhasil dibuat.'); } finally { setBusy(false); }
  }
  return <Modal title="Tambah akun" onClose={onClose}><form onSubmit={submit}><div className="form-grid">
    <label>Nama lengkap<input name="nama" {...required} autoFocus /></label><label>Username<input name="username" autoComplete="off" {...required} /></label>
    <label>NIP<input name="nip" inputMode="numeric" /></label><label>Peran<span className="select-wrap"><select name="peran" defaultValue="dosen"><option value="dosen">Dosen</option><option value="admin">Admin</option></select><ChevronDown size={16} aria-hidden="true" /></span></label></div>
    <p className="meta">NIP wajib untuk dosen supaya bisa tertaut ke dokumen yang menyebut namanya. Password awal dibuat otomatis.</p>
    <ErrorMessage message={error} /><div className="form-actions"><button type="button" className="neutral" onClick={onClose}>Batal</button><button className="primary" disabled={busy}>{busy ? 'Menyimpan…' : 'Buat akun'}</button></div></form></Modal>;
}

function UbahAkun({ akun, onClose, onDone }: { akun: Akun; onClose: () => void; onDone: (teks: string) => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true); const data = new FormData(event.currentTarget);
    try { await api(`/admin/akun/${akun.id}`, { method: 'PATCH', body: JSON.stringify({ nama: data.get('nama'), nip: data.get('nip') }) }); onDone(`Akun ${akun.username} diperbarui.`); }
    catch (e) { setError(e instanceof Error ? e.message : 'Perubahan belum tersimpan.'); } finally { setBusy(false); }
  }
  return <Modal title="Ubah akun" onClose={onClose}><p className="meta">Username {akun.username} tidak bisa diubah.</p><form onSubmit={submit}><div className="form-grid">
    <label>Nama lengkap<input name="nama" defaultValue={akun.nama} {...required} autoFocus /></label><label>NIP<input name="nip" defaultValue={akun.nip || ''} inputMode="numeric" placeholder="Kosongkan kalau tidak ada" /></label></div>
    <p className="meta">NIP dipakai untuk menautkan dosen ke dokumen yang menyebut namanya. Perubahan NIP berlaku untuk dokumen yang diunggah sesudahnya; tautan yang sudah ada tidak berubah.</p>
    <ErrorMessage message={error} /><div className="form-actions"><button type="button" className="neutral" onClick={onClose}>Batal</button><button className="primary" disabled={busy}>{busy ? 'Menyimpan…' : 'Simpan'}</button></div></form></Modal>;
}

function PasswordModal({ data, onClose }: { data: Password; onClose: () => void }) {
  const [copied, setCopied] = useState('');
  function salin(teks: string, kunci: string) { void navigator.clipboard?.writeText(teks).then(() => setCopied(kunci)); }
  function unduh() {
    const baris = [['username', 'nama', 'password_awal'], ...data.baris.map(b => [b.username, b.nama || '', b.password])];
    const csv = baris.map(r => r.map(v => `"${v.replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'password_awal.csv'; a.click(); URL.revokeObjectURL(url);
  }
  return <Modal title={data.judul} onClose={onClose}>
    <p className="admin-warning">Password hanya tampil sekali. Sampaikan langsung ke pemilik akun, jangan lewat grup chat.</p>
    {data.baris.length > 0 && <ul className="password-list">{data.baris.map(b => <li key={b.username}><div className="list-text"><strong>{b.nama || b.username}</strong><span className="meta">{b.username}</span></div><code>{b.password}</code><button className="text-button" onClick={() => salin(b.password, b.username)}><Copy size={16} aria-hidden="true" />{copied === b.username ? 'Tersalin' : 'Salin'}</button></li>)}</ul>}
    {data.dilewati && data.dilewati.length > 0 && <><p className="meta">{data.dilewati.length} baris dilewati:</p><ul className="skipped-list">{data.dilewati.map(d => <li key={d}>{d}</li>)}</ul></>}
    <div className="form-actions">{data.baris.length > 1 && <button className="neutral" onClick={unduh}><Download size={16} aria-hidden="true" />Unduh CSV password</button>}<button className="primary" onClick={onClose}>Selesai</button></div>
    {data.baris.length > 1 && <p className="meta">Hapus berkas CSV password setelah semua password dibagikan.</p>}
  </Modal>;
}

function DokumenTab({ setError, setNotice }: { setError: (v: string) => void; setNotice: (v: string) => void }) {
  const [gagal, setGagal] = useState<DokumenGagal[]>([]); const [loading, setLoading] = useState(true); const [busy, setBusy] = useState('');
  const [cari, setCari] = useState(''); const [hasil, setHasil] = useState<DokumenRingkas[] | null>(null); const [tautkan, setTautkan] = useState<DokumenRingkas | null>(null);
  const [ditolak, setDitolak] = useState<DokumenDitolak[]>([]);
  const muat = useCallback(() => { setLoading(true); Promise.all([api<DokumenGagal[]>('/admin/dokumen-gagal'), api<DokumenDitolak[]>('/admin/dokumen-ditolak')]).then(([g, d]) => { setGagal(g); setDitolak(d); }).catch(e => setError(e.message)).finally(() => setLoading(false)); }, [setError]);
  useEffect(() => { muat(); }, [muat]);
  async function kembalikan(doc: DokumenDitolak) {
    setBusy(doc.id); setError(''); setNotice('');
    try { await api(`/admin/dokumen/${doc.id}/kembalikan`, { method: 'POST' }); setDitolak(items => items.filter(item => item.id !== doc.id)); setNotice(`${doc.nama_berkas} dikembalikan ke Kotak Verifikasi ${doc.pengunggah}.`); }
    catch (e) { setError(e instanceof Error ? e.message : 'Dokumen belum berhasil dikembalikan.'); } finally { setBusy(''); }
  }
  async function prosesUlang(doc: DokumenGagal) {
    setBusy(doc.id); setError(''); setNotice('');
    try { await api(`/admin/dokumen/${doc.id}/proses-ulang`, { method: 'POST' }); setGagal(items => items.filter(item => item.id !== doc.id)); setNotice(`${doc.nama_berkas} sedang diproses ulang. Hasilnya muncul di akun ${doc.pengunggah}.`); }
    catch (e) { setError(e instanceof Error ? e.message : 'Proses ulang belum berhasil.'); } finally { setBusy(''); }
  }
  async function cariDokumen(event: FormEvent) { event.preventDefault(); setError(''); try { setHasil(await api<DokumenRingkas[]>(`/admin/dokumen?cari=${encodeURIComponent(cari.trim())}`)); } catch (e) { setError(e instanceof Error ? e.message : 'Pencarian belum berhasil.'); } }
  return <>
    <section className="admin-section" aria-labelledby="judul-gagal"><div className="section-heading"><h2 id="judul-gagal">Dokumen gagal</h2><button className="text-button" onClick={muat}><RotateCcw size={16} aria-hidden="true" />Muat ulang</button></div>
      {loading ? <p className="muted">Memuat…</p> : gagal.length === 0 ? <p className="muted">Tidak ada dokumen gagal.</p> :
        <ul className="card admin-list">{gagal.map(doc => <li key={doc.id}><div className="list-text"><strong>{doc.nama_berkas}</strong><span className="meta">{doc.pengunggah} · {waktu(doc.created_at)}</span>{doc.keterangan && <span className="meta">{doc.keterangan}</span>}</div>
          <div className="admin-row-end"><button className="secondary" disabled={busy === doc.id} onClick={() => void prosesUlang(doc)}>{busy === doc.id ? 'Memproses…' : 'Proses ulang'}</button></div></li>)}</ul>}</section>
    <section className="admin-section" aria-labelledby="judul-ditolak"><div className="section-heading"><h2 id="judul-ditolak">Dokumen ditolak</h2></div>
      <p className="meta">Kalau dosen salah menekan Tolak, kembalikan dokumennya ke Kotak Verifikasi supaya bisa diperiksa ulang. Dosen tertaut baru bisa melihatnya lagi setelah pengunggah menyetujui.</p>
      {loading ? <p className="muted">Memuat…</p> : ditolak.length === 0 ? <p className="muted">Tidak ada dokumen ditolak.</p> :
        <ul className="card admin-list">{ditolak.map(doc => <li key={doc.id}><div className="list-text"><strong>{doc.nama_berkas}</strong><span className="meta">{doc.pengunggah} · ditolak {waktu(doc.ditolak_at)}</span></div>
          <div className="admin-row-end"><button className="secondary" disabled={busy === doc.id} onClick={() => void kembalikan(doc)}>{busy === doc.id ? 'Memproses…' : 'Kembalikan ke Kotak Verifikasi'}</button></div></li>)}</ul>}</section>
    <section className="admin-section" aria-labelledby="judul-tautkan"><div className="section-heading"><h2 id="judul-tautkan">SK bersama</h2></div>
      <p className="meta">Kalau dosen mendapat pesan &quot;Sudah pernah diunggah&quot; untuk SK yang sudah diunggah dosen lain, cari dokumennya lalu tautkan dosen itu. Dosen yang ditautkan bisa melihat dan mengunduh, tetapi tidak bisa mengubah.</p>
      <form className="admin-find" onSubmit={cariDokumen}><label className="admin-search">Nama berkas<span className="search-wrap"><Search size={16} aria-hidden="true" /><input type="search" value={cari} onChange={e => setCari(e.target.value)} placeholder="Minimal 3 huruf, misalnya pengajaran" minLength={3} {...required} /></span></label><button className="neutral">Cari</button></form>
      {hasil && (hasil.length === 0 ? <p className="muted">Tidak ada dokumen dengan nama itu.</p> :
        <ul className="card admin-list">{hasil.map(doc => <li key={doc.id}><div className="list-text"><strong>{doc.nama_berkas}</strong><span className="meta">Diunggah {doc.pengunggah} · {waktu(doc.created_at)}</span></div>
          <div className="admin-row-end"><Status status={doc.status} /><button className="text-button" onClick={() => setTautkan(doc)}>Tautkan dosen</button></div></li>)}</ul>)}
    </section>
    {tautkan && <TautkanModal doc={tautkan} onClose={() => setTautkan(null)} onDone={teks => { setTautkan(null); setNotice(teks); }} />}
  </>;
}

function TautkanModal({ doc, onClose, onDone }: { doc: DokumenRingkas; onClose: () => void; onDone: (teks: string) => void }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true); const data = new FormData(event.currentTarget); const username = String(data.get('username') || '').trim();
    try { await api(`/admin/dokumen/${doc.id}/tautkan`, { method: 'POST', body: JSON.stringify({ username, peran: data.get('peran') || null }) }); onDone(`${username} sekarang tertaut ke ${doc.nama_berkas} dan bisa melihatnya di Arsip.`); }
    catch (e) { setError(e instanceof Error ? e.message : 'Penautan belum berhasil.'); } finally { setBusy(false); }
  }
  return <Modal title="Tautkan dosen" onClose={onClose}><p>{doc.nama_berkas}</p><p className="meta">Diunggah {doc.pengunggah}</p><form onSubmit={submit}><div className="form-grid">
    <label>Username dosen<input name="username" autoComplete="off" {...required} autoFocus /></label><label>Peran di dokumen<input name="peran" placeholder="Misalnya Anggota" /></label></div>
    <ErrorMessage message={error} /><div className="form-actions"><button type="button" className="neutral" onClick={onClose}>Batal</button><button className="primary" disabled={busy}>{busy ? 'Menyimpan…' : 'Tautkan'}</button></div></form></Modal>;
}

function LogTab({ setError }: { setError: (v: string) => void }) {
  const [log, setLog] = useState<Log[]>([]); const [loading, setLoading] = useState(true);
  useEffect(() => { api<Log[]>('/admin/log?batas=200').then(setLog).catch(e => setError(e.message)).finally(() => setLoading(false)); }, [setError]);
  async function unduhKoreksi() {
    setError('');
    try { const r = await fetch(`${API}/admin/koreksi/export`, { headers: { Authorization: `Bearer ${token()}` } }); if (!r.ok) throw new Error(); const url = URL.createObjectURL(await r.blob()); const a = document.createElement('a'); a.href = url; a.download = 'riwayat-koreksi.json'; a.click(); URL.revokeObjectURL(url); }
    catch { setError('Riwayat koreksi belum bisa diunduh. Coba lagi.'); }
  }
  return <section aria-label="Log aktivitas"><div className="section-heading"><p className="results-count">{loading ? 'Memuat log…' : `${log.length} aktivitas terakhir`}</p><button className="neutral" onClick={() => void unduhKoreksi()}><Download size={16} aria-hidden="true" />Unduh riwayat koreksi</button></div>
    {!loading && log.length === 0 ? <p className="muted">Belum ada aktivitas.</p> :
      <ul className="card admin-list">{log.map((l, i) => <li key={`${l.created_at}-${i}`}><div className="list-text"><strong>{LABEL_AKSI[l.aksi] || l.aksi}</strong><span className="meta">{l.nama} ({l.username}){l.oleh ? ` · oleh ${l.oleh}` : ''}</span></div><span className="meta admin-time">{waktu(l.created_at)}</span></li>)}</ul>}
  </section>;
}
