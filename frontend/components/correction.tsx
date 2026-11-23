'use client';
import { ChevronDown } from 'lucide-react';
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react';
import { api, Document, Dosen, DRAF_PREFIX, SesiHabis, simpanSesi, Taxonomy, User, usernameSesi } from '@/lib/api';
import { ErrorMessage, Modal, required } from './ui';
type FormValues = {kategori: string; subkategori: string; jenis: string; judul: string; nomor_dokumen: string; tanggal_terbit: string; periode: string; mitra_penerbit: string; sumber_dana: string; identifier: string};
type Draf = { values: FormValues; dosen: Dosen[] };

// Draf koreksi disimpan di sessionStorage tab ini saja: bertahan saat laman dimuat ulang atau sesi habis,
// hilang saat tab ditutup atau dosen menekan Keluar. Tidak dikirim ke mana pun.
function bacaDraf(key: string): Draf | null { try { const raw = sessionStorage.getItem(key); return raw ? JSON.parse(raw) as Draf : null; } catch { return null; } }
function tulisDraf(key: string, draf: Draf | null) { try { if (draf) sessionStorage.setItem(key, JSON.stringify(draf)); else sessionStorage.removeItem(key); } catch {} }

export function Correction({ doc, onClose, onSaved }: {doc: Document; onClose: () => void; onSaved: () => void}) {
  const initial: FormValues = {kategori: doc.kategori || '', subkategori: doc.subkategori || '', jenis: doc.jenis || '', judul: doc.judul || '', nomor_dokumen: doc.nomor_dokumen || '', tanggal_terbit: doc.tanggal_terbit || '', periode: doc.periode || '', mitra_penerbit: doc.metadata_lain?.mitra_penerbit || '', sumber_dana: doc.metadata_lain?.sumber_dana || '', identifier: doc.metadata_lain?.identifier || ''};
  const kunciDraf = `${DRAF_PREFIX}koreksi:${doc.id}`;
  const [values, setValues] = useState(initial); const [dosen, setDosen] = useState<Dosen[]>(doc.dosen_terkait || []); const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false); const keepEditing = useRef<HTMLButtonElement>(null);
  const [drafLama, setDrafLama] = useState<Draf | null>(null); const [sesiHabis, setSesiHabis] = useState(false); const [masukError, setMasukError] = useState(''); const passwordRef = useRef<HTMLInputElement>(null);
  // Form dianggap berubah kalau ada field atau dosen terkait yang berbeda dari hasil AI.
  const dirty = (Object.keys(initial) as (keyof FormValues)[]).some(key => values[key] !== initial[key]) || JSON.stringify(dosen) !== JSON.stringify(doc.dosen_terkait || []);
  // Dibaca lewat ref supaya `close` tetap stabil; kalau berubah, Modal akan memasang ulang efeknya dan fokus input lompat.
  const dirtyRef = useRef(dirty); dirtyRef.current = dirty;
  const close = useCallback(() => { if (busy) return; if (dirtyRef.current) setConfirming(true); else onClose(); }, [busy, onClose]);
  useEffect(() => { if (confirming) keepEditing.current?.focus(); }, [confirming]);
  useEffect(() => { api<Taxonomy>('/taxonomy').then(setTaxonomy).catch(e => setError(e.message)); }, []);
  // Tawarkan draf yang belum tersimpan dari sebelumnya (misalnya laman sempat dimuat ulang).
  useEffect(() => { setDrafLama(bacaDraf(kunciDraf)); }, [kunciDraf]);
  // Simpan draf setiap ada perubahan; draf lama tidak ditimpa sebelum dosen memutuskan memakainya atau tidak.
  useEffect(() => { if (dirty && !drafLama) tulisDraf(kunciDraf, { values, dosen }); }, [dirty, drafLama, values, dosen, kunciDraf]);
  useEffect(() => { if (sesiHabis) passwordRef.current?.focus(); }, [sesiHabis]);
  const category = taxonomy?.categories.find(item => item.kode === values.kategori); const subcategory = category?.subkategori.find(item => item.nama === values.subkategori);
  function change(field: keyof FormValues, value: string) {setValues(old => ({...old, [field]: value, ...(field === 'kategori' ? {subkategori:'', jenis:''} : field === 'subkategori' ? {jenis:''} : {})}));}
  function label(field: keyof FormValues, text: string) { return <span>{text}{values[field] !== initial[field] && <span className="changed" aria-label="Diubah"> •</span>}</span>; }
  function pakaiDraf() { if (drafLama) { setValues(drafLama.values); setDosen(drafLama.dosen); } setDrafLama(null); }
  function buangDraf() { tulisDraf(kunciDraf, null); setDrafLama(null); }
  function buangPerubahan() { tulisDraf(kunciDraf, null); onClose(); }
  async function simpan() {
    setBusy(true); setError(''); const nullable = (value: string) => value.trim() || null;
    try {
      await api(`/documents/${doc.id}`, {method: 'PATCH', body: JSON.stringify({kategori: values.kategori, subkategori: nullable(values.subkategori), jenis: nullable(values.jenis), judul: nullable(values.judul), nomor_dokumen: nullable(values.nomor_dokumen), tanggal_terbit: nullable(values.tanggal_terbit), periode: nullable(values.periode), metadata_lain: {mitra_penerbit: nullable(values.mitra_penerbit), sumber_dana: nullable(values.sumber_dana), identifier: nullable(values.identifier)}, dosen_terkait: dosen.map(item => ({nama:item.nama, nip:item.nip || null, peran:item.peran || null}))}) }, { tetapDiLaman: true });
      tulisDraf(kunciDraf, null); onSaved(); onClose();
    } catch(e) { if (e instanceof SesiHabis) setSesiHabis(true); else setError(e instanceof Error ? e.message : 'Koreksi belum tersimpan.'); }
    finally { setBusy(false); }
  }
  function submit(event: FormEvent) { event.preventDefault(); void simpan(); }
  async function masukLagi(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMasukError(''); setBusy(true); const data = new FormData(event.currentTarget); const username = String(data.get('username') || '');
    try {
      const result = await api<{access_token: string; user: User}>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password: data.get('password') }) });
      simpanSesi(result.access_token, result.user.username); setSesiHabis(false); setBusy(false); await simpan();
    } catch (e) { setMasukError(e instanceof Error ? e.message : 'Belum berhasil masuk. Coba lagi.'); setBusy(false); }
  }
  const usernameLama = usernameSesi();
  return <Modal title="Koreksi dokumen" onClose={close}>{confirming && <div className="discard-confirm" role="alertdialog" aria-label="Buang perubahan?"><p><strong>Buang perubahan?</strong> Koreksi yang belum disimpan akan hilang.</p><div><button ref={keepEditing} type="button" className="secondary" onClick={() => setConfirming(false)}>Lanjutkan mengedit</button><button type="button" className="destructive" onClick={buangPerubahan}>Buang perubahan</button></div></div>}
    {sesiHabis && <form className="session-panel" onSubmit={masukLagi} role="alert" aria-label="Sesi berakhir"><p><strong>Sesi Anda berakhir.</strong> Masukkan password untuk melanjutkan. Isian koreksi tidak hilang dan langsung disimpan setelah Anda masuk.</p><div className="session-fields">{usernameLama ? <input type="hidden" name="username" value={usernameLama} /> : <label>Username<input name="username" autoComplete="username" {...required} /></label>}<label><span>Password{usernameLama && <span className="meta"> untuk {usernameLama}</span>}</span><input ref={passwordRef} name="password" type="password" autoComplete="current-password" {...required} /></label><button className="primary" disabled={busy}>{busy ? 'Memeriksa…' : 'Masuk dan simpan'}</button></div><ErrorMessage message={masukError} /></form>}
    {drafLama && <div className="draft-banner" role="status"><p><strong>Ada koreksi yang belum disimpan</strong> dari sebelumnya untuk dokumen ini.</p><div><button type="button" className="secondary" onClick={pakaiDraf}>Pakai draf</button><button type="button" className="text-button" onClick={buangDraf}>Buang</button></div></div>}
    <p className="muted">Periksa hasil yang sudah terisi. Perubahan disimpan sebagai riwayat koreksi.</p>{taxonomy?.source === 'demo' && <p className="demo-notice">Taksonomi demo sementara. Menunggu taksonomi resmi Orang 1.</p>}<form onSubmit={submit}><div className="form-grid"><label>{label('kategori','Kategori')}<span className="select-wrap"><select {...required} value={values.kategori} onChange={e => change('kategori',e.target.value)}><option value="">Pilih kategori</option>{taxonomy?.categories.map(item => <option key={item.kode} value={item.kode}>{item.kode} · {item.nama}</option>)}</select><ChevronDown size={16} aria-hidden="true" /></span></label><label>{label('subkategori','Subkategori')}<span className="select-wrap"><select value={values.subkategori} onChange={e => change('subkategori',e.target.value)}><option value="">Tidak ditemukan</option>{category?.subkategori.map(item => <option key={item.nama}>{item.nama}</option>)}</select><ChevronDown size={16} aria-hidden="true" /></span></label><label>{label('jenis','Jenis')}<span className="select-wrap"><select value={values.jenis} onChange={e => change('jenis',e.target.value)}><option value="">Tidak ditemukan</option>{subcategory?.jenis.map(item => <option key={item}>{item}</option>)}</select><ChevronDown size={16} aria-hidden="true" /></span></label>{([['judul','Judul'],['nomor_dokumen','Nomor dokumen'],['tanggal_terbit','Tanggal terbit'],['periode','Periode'],['mitra_penerbit','Mitra / penerbit'],['sumber_dana','Sumber dana'],['identifier','Identifier']] as [keyof FormValues,string][]).map(([key,text]) => <label key={key}>{label(key,text)}<input type={key === 'tanggal_terbit' ? 'date' : 'text'} value={values[key]} onChange={e => change(key,e.target.value)} placeholder="Tidak ditemukan" /></label>)}</div><fieldset><legend>Dosen terkait</legend>{dosen.map((item,index) => <div className="dosen-edit" key={index}><label>Nama<input {...required} value={item.nama} onChange={e => setDosen(items => items.map((d,i) => i === index ? {...d,nama:e.target.value} : d))} /></label><label>NIP<input value={item.nip || ''} onChange={e => setDosen(items => items.map((d,i) => i === index ? {...d,nip:e.target.value} : d))} /></label><label>Peran<input value={item.peran || ''} onChange={e => setDosen(items => items.map((d,i) => i === index ? {...d,peran:e.target.value} : d))} /></label><button type="button" className="destructive" onClick={() => setDosen(items => items.filter((_,i) => i !== index))}>Hapus dosen</button></div>)}<button type="button" className="text-button" onClick={() => setDosen(items => [...items,{nama:'',nip:null,peran:null}])}>Tambah dosen terkait</button></fieldset><ErrorMessage message={error} /><div className="form-actions"><button type="button" className="text-button" disabled={busy} onClick={close}>Batal</button><button className="primary" disabled={busy || !taxonomy || sesiHabis}>{busy ? 'Menyimpan…' : 'Simpan dan setujui'}</button></div></form></Modal>;
}
