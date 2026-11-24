import { Document } from './api';

const KATA_KECIL = new Set(['dan', 'di', 'ke', 'dari', 'pada', 'untuk', 'tentang', 'yang', 'atau', 'dengan']);
const SINGKATAN = /^\(?(rps|sk|ta|hki|bkd|skp|edom|lppm|ri|ui|ai|it|ti|s1|s2|s3)\)?[.,:]?$/;

// Judul hasil OCR sering ditulis HURUF BESAR semua; tampilkan dengan huruf kapital di awal kata saja.
export function rapikanJudul(teks: string) {
  const huruf = teks.replace(/[^A-Za-z]/g, '');
  if (!huruf || huruf.replace(/[^A-Z]/g, '').length / huruf.length < 0.8) return teks;
  return teks.toLowerCase().split(' ').map((kata, i) => {
    if (i > 0 && KATA_KECIL.has(kata)) return kata;
    if (/\d/.test(kata) || SINGKATAN.test(kata)) return kata.toUpperCase();
    return kata.charAt(0).toUpperCase() + kata.slice(1);
  }).join(' ');
}

export function judulDokumen(doc: Document) {
  return rapikanJudul((doc.judul || doc.nama_berkas).replace(/^\s*\[MOCK\]\s*/i, ''));
}

const ZONA = 'Asia/Jakarta';
const hari = (waktu: Date) => new Intl.DateTimeFormat('en-CA', { timeZone: ZONA }).format(waktu);
const jam = (waktu: Date) => new Intl.DateTimeFormat('id-ID', { timeZone: ZONA, hour: '2-digit', minute: '2-digit' }).format(waktu);
const tanggal = (waktu: Date) => new Intl.DateTimeFormat('id-ID', { timeZone: ZONA, dateStyle: 'medium' }).format(waktu);

// Waktu unggah relatif dalam WIB. Database menyimpan UTC, jadi zona waktu harus diubah di sini.
export function waktuUnggah(nilai?: string | null) {
  if (!nilai) return { teks: '', lengkap: '' };
  const waktu = new Date(nilai), menit = Math.floor((Date.now() - waktu.getTime()) / 60000);
  const lengkap = `${tanggal(waktu)}, ${jam(waktu)} WIB`;
  if (menit < 1) return { teks: 'Diunggah baru saja', lengkap };
  if (menit < 60) return { teks: `Diunggah ${menit} menit lalu`, lengkap };
  if (hari(waktu) === hari(new Date())) return { teks: `Diunggah hari ini ${jam(waktu)}`, lengkap };
  if (hari(waktu) === hari(new Date(Date.now() - 86400000))) return { teks: `Diunggah kemarin ${jam(waktu)}`, lengkap };
  return { teks: `Diunggah ${tanggal(waktu)}, ${jam(waktu)}`, lengkap };
}
