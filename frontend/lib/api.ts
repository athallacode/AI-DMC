export type User = { id: string; nama: string; username: string; peran: string };
export type Dosen = { nama: string; nip: string | null; peran: string | null; user_id?: string | null; dikonfirmasi?: boolean };
export type Document = { id: string; owner_id?: string; nama_berkas: string; jenis_berkas?: string; kategori?: string | null; subkategori?: string | null; jenis?: string | null; judul?: string | null; nomor_dokumen?: string | null; tanggal_terbit?: string | null; periode?: string | null; metadata_lain?: Record<string, string | null>; dosen_terkait?: Dosen[]; skor_keyakinan?: number | null; status: string; created_at: string; ringkasan?: string | null; error?: string | null; model_dipakai?: string | null };
export type Taxonomy = { source: string; categories: { kode: string; nama: string; subkategori: { nama: string; jenis: string[] }[] }[] };
export const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export function token() { return typeof window === 'undefined' ? null : sessionStorage.getItem('ai-dmc-token'); }
export const DRAF_PREFIX = 'ai-dmc-draf-';
// Keluar lewat tombol menghapus draf koreksi (komputer bersama). Sesi yang habis sendiri tidak menghapusnya,
// supaya draf bisa dipakai lagi setelah masuk kembali di tab yang sama.
export function logout(hapusDraf = false) {
  sessionStorage.removeItem('ai-dmc-token');
  if (hapusDraf) Object.keys(sessionStorage).filter(key => key.startsWith(DRAF_PREFIX)).forEach(key => sessionStorage.removeItem(key));
  window.location.assign('/login');
}
export function simpanSesi(accessToken: string, username: string) { sessionStorage.setItem('ai-dmc-token', accessToken); sessionStorage.setItem('ai-dmc-username', username); }
export function usernameSesi() { return typeof window === 'undefined' ? '' : sessionStorage.getItem('ai-dmc-username') || ''; }
/** Sesi habis saat pemanggil memilih tetap di laman (misalnya formulir koreksi yang belum tersimpan). */
export class SesiHabis extends Error {}
export async function api<T>(path: string, options: RequestInit = {}, opsi: { tetapDiLaman?: boolean } = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (token()) headers.set('Authorization', `Bearer ${token()}`);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API}${path}`, { ...options, headers, cache: 'no-store' });
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      if (opsi.tetapDiLaman) throw new SesiHabis('Sesi Anda berakhir. Masuk lagi untuk melanjutkan.');
      logout();
    }
    const result = await response.json().catch(() => ({}));
    throw new Error(typeof result.detail === 'string' ? result.detail : 'Permintaan belum berhasil. Periksa isian dan coba lagi.');
  }
  return response.json() as Promise<T>;
}
export async function getFile(id: string) {
  const response = await fetch(`${API}/documents/${id}/file`, { headers: { Authorization: `Bearer ${token()}` } });
  if (!response.ok) throw new Error('Berkas tidak dapat dibuka. Silakan masuk kembali atau coba lagi.');
  return URL.createObjectURL(await response.blob());
}
export const statusLabels: Record<string, string> = { diproses: 'Diproses', menunggu_verifikasi: 'Menunggu verifikasi', terverifikasi: 'Terverifikasi', ditolak: 'Ditolak', gagal: 'Gagal' };
export function date(value?: string | null) { return value ? new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium' }).format(new Date(value)) : 'Tidak ditemukan'; }
