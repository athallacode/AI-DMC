# Berita Acara Serah Terima Hasil Pengembangan AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Nomor: ........................................

Pada hari ................ tanggal ........................, bertempat di ........................................, yang bertanda tangan di bawah ini:

| | Nama | Jabatan atau peran |
|---|---|---|
| Pihak Pertama | ........................................ | AI Pipeline Engineer, tim magang |
| | ........................................ | Application Engineer, tim magang |
| Pihak Kedua | ........................................ | Ketua CoE AIIS, atau yang ditunjuk |

Pihak Pertama menyerahkan kepada Pihak Kedua hasil pengembangan AI-DMC tahap MVP (31 Oktober sampai 23 November 2026), dengan rincian berikut.

## 1. Kode sumber

| Butir | Keterangan |
|---|---|
| Repositori | github.com/athallacode/AI-DMC |
| Branch | feat/ai-asli-dan-perbaikan-ui |
| Commit terakhir | ................ (isi dengan hasil `git rev-parse --short HEAD` saat penandatanganan) |
| Cara penyerahan | [ ] Push ke repositori di atas [ ] Salinan repositori (git bundle) pada media: ................ |

Catatan: pada 23 November 2026 branch ini sudah di-push ke repositori di atas dan diajukan sebagai Pull Request ke `main`. Push sebelumnya gagal karena akun GitHub tim ditangguhkan (suspended) oleh GitHub, sehingga push dilakukan dengan akun pemilik repositori. Salinan git bundle tetap disertakan sebagai cadangan.

## 2. Dokumen

Selain berita acara ini, dokumen berikut ada di folder `docs/` dalam format Markdown. Berkas PDF tidak tersimpan di repositori, jadi diserahkan sebagai berkas terpisah.

| No | Dokumen | Berkas PDF | Halaman |
|---|---|---|---|
| 1 | Laporan Akhir | Laporan-Akhir-AI-DMC.pdf | 8 |
| 2 | Panduan Dosen | Panduan-Dosen-AI-DMC.pdf | 16 |
| 3 | Panduan Admin dan Pengelola | Panduan-Admin-AI-DMC.pdf | 7 |
| 4 | Kebijakan Data dan Keamanan | Kebijakan-Data-AI-DMC.pdf | 7 |
| 5 | Kebutuhan Server | Kebutuhan-Server-AI-DMC.pdf | 5 |
| 6 | Panduan Instalasi dan Operasional | Panduan-Instalasi-AI-DMC.pdf | 11 |
| 7 | Arsitektur AI-DMC | Arsitektur-AI-DMC.pdf | 8 |
| 8 | Buku Pengembangan | Buku-Pengembangan-AI-DMC.pdf | 11 |
| 9 | Panduan Ringkas Dosen | Panduan-Ringkas-Dosen-AI-DMC.pdf | 1 |

## 3. Kondisi saat diserahkan

Berfungsi dan teruji di laptop pengembang:

- Aplikasi web: masuk, unggah, klasifikasi AI lokal, Kotak Verifikasi, Arsip, dan laman Admin.
- Pengelolaan akun dan dokumen lewat laman Admin atau perintah `kelola` di server.
- 34 tes backend dan 53 tes pipeline lulus.
- Pemasangan dependensi di Ubuntu 24.04, serta cadangan dan pemulihan database.

Belum dikerjakan atau belum diuji:

- Deploy ke server CoE, karena server belum tersedia.
- Uji coba dengan dosen.
- Layanan backend di server, OCR dengan GPU, dan HTTPS.
- Pekerjaan teknis lain tercantum di Buku Pengembangan Bagian 9.

Keputusan yang ditunggu dari Pihak Kedua: SK pembimbing TA dan berita acara sidang masuk kategori Pendidikan (PND) atau Penunjang (PNJ).

## 4. Data dan rahasia

1. **Dokumen asli dosen** yang dipakai untuk pengujian (22 dokumen dari satu dosen, folder `data/nyata`), beserta salinannya di folder `storage/` dan database pengembangan, berada di laptop pengembang. Setelah berita acara ini ditandatangani, data tersebut:

   [ ] dihapus dari laptop pengembang, dan Pihak Pertama menyatakannya secara tertulis
   [ ] diserahkan kepada Pihak Kedua pada media: ................, lalu dihapus dari laptop pengembang

2. **Data dummy** (folder `data/dummy` dan `data/dummy_nyata`) tidak berisi data pribadi dan bisa dibuat ulang dengan skrip di folder `tools/`.
3. **Rahasia** (password database, kunci JWT, password akun dummy) tidak ditulis di dokumen mana pun. Server baru wajib memakai rahasia baru sesuai Panduan Instalasi Bagian 2.
4. Akun dummy (`dosen1`, `dosen2`, `admin`) hanya untuk pengembangan dan wajib ditutup sebelum aplikasi dipakai dosen.

## 5. Ketentuan

1. Sejak berita acara ini ditandatangani, pengelolaan, pemeliharaan, dan pengembangan lanjutan AI-DMC menjadi tanggung jawab Pihak Kedua.
2. Pihak Pertama bersedia dihubungi untuk pertanyaan tentang hasil pengembangan sampai tanggal ........................
3. Pihak Pertama tidak menyimpan salinan data pribadi dosen setelah butir 4.1 dilaksanakan.

Demikian berita acara ini dibuat dengan sebenarnya, dalam rangkap dua, masing-masing untuk Pihak Pertama dan Pihak Kedua.

<div class="ttd">
<div><p>Pihak Pertama</p><p class="garis">........................................</p><p class="garis">........................................</p></div>
<div><p>Pihak Kedua</p><p class="garis">........................................</p></div>
<div><p>Mengetahui,<br>Pembimbing</p><p class="garis">........................................</p></div>
</div>
