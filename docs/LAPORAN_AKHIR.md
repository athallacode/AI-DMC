# Laporan Akhir Pengembangan AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Tahap MVP, 31 Oktober sampai 23 November 2026

## 1. Ringkasan

AI-DMC adalah aplikasi arsip dokumen eviden dosen. Dosen mengunggah dokumen (SK, surat tugas, sertifikat, RPS, daftar nilai, dan lainnya), AI lokal membaca dan mengklasifikasikannya serta mengisi metadata, lalu dosen cukup menyetujui atau mengoreksi.

Hasil tahap ini:

- **Aplikasi MVP selesai dan berjalan di laptop pengembang:** masuk, unggah banyak berkas, klasifikasi AI, Kotak Verifikasi, dan Arsip. Kedelapan butir ruang lingkup MVP terpenuhi.
- **AI sepenuhnya lokal:** Ollama dengan model `gemma4:e4b` dan PaddleOCR. Tidak ada dokumen yang dikirim ke layanan AI publik.
- **Akurasi pada 45 dokumen uji berformat mirip asli:** kategori 100% dan jenis 97,8%. Sebanyak 97,8% dokumen lolos otomatis, dan semua yang lolos otomatis benar jenisnya. Prompt disetel dari kesalahan pada data yang sama, jadi angka untuk dokumen baru kemungkinan lebih rendah (Bagian 5.4).
- **Pada 22 dokumen asli dari satu dosen:** tidak ada yang gagal diproses. Akurasi kategori bergantung pada keputusan taksonomi yang masih menunggu Admin CoE (Bagian 5.3).
- **Belum dilakukan:** deploy ke server CoE dan uji coba dengan dosen, karena server belum tersedia. Berkas dan panduan deploy sudah disiapkan, dan sebagian langkahnya sudah diuji di lingkungan Ubuntu.

## 2. Latar belakang dan tujuan

Dosen perlu mengumpulkan dokumen eviden untuk BKD, jabatan fungsional, dan akreditasi. Dokumen tersebar di banyak tempat dan harus dipilah satu per satu. AI-DMC bertujuan:

1. Mengurangi kerja memilah dan mengisi metadata dokumen secara manual.
2. Menyimpan dokumen di satu arsip yang tertata menurut kategori Tridharma dan penunjang.
3. Menjaga data pribadi dosen dengan menjalankan seluruh pemrosesan AI di server sendiri.

Acuan rancangan: DOK-CoE-AIIS-DMC-001 v0.1 (Rancangan Sistem AI-DMC).

## 3. Ruang lingkup dan status

| Butir MVP | Status |
|---|---|
| Masuk dengan username dan password | Selesai |
| Unggah banyak berkas sekaligus (PDF, DOCX, JPG, PNG) | Selesai. Maksimal 20 berkas dan 20 MB per berkas |
| Cek duplikat dengan SHA-256 | Selesai |
| Pipeline AI: ekstraksi teks dan OCR, klasifikasi, metadata | Selesai |
| Skor keyakinan 0,85 ke atas langsung masuk arsip, sisanya ke Kotak Verifikasi | Selesai |
| Kotak Verifikasi: Setujui, Koreksi, Tolak | Selesai, dengan pratinjau dokumen dan tombol Urungkan |
| Laman Arsip dengan filter kategori, status, tahun | Selesai |
| Koreksi dosen disimpan sebagai bahan perbaikan AI | Selesai. Riwayat bisa diekspor admin |

Tambahan di luar daftar MVP: perintah pengelola `app.kelola` (akun, dokumen gagal, SK bersama), log audit yang tidak bisa diubah, pertahanan prompt injection, tampilan HP, berkas deploy server, antrean pemrosesan yang dilanjutkan otomatis setelah restart, batas percobaan login, dan penyaring nomor serta tanggal dokumen yang tidak tertulis di teks.

Sesuai kesepakatan, yang tidak dikerjakan di tahap ini: SSO kampus, pencarian bahasa alami (Tanya Arsip), generator paket jabatan fungsional dan akreditasi, dasbor Ketua CoE, deteksi versi dokumen, dan antrean Celery dengan Redis.

## 4. Pendekatan dan arsitektur

| Bagian | Teknologi |
|---|---|
| Frontend | Next.js 15, desain Apple light dengan elemen glass |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 17 |
| Ekstraksi teks | PyMuPDF (PDF digital), python-docx (DOCX) |
| OCR | PaddleOCR 3.7 (PDF scan dan foto) |
| LLM | Ollama, `gemma4:e4b` |

Cara kerja AI secara singkat:

1. Teks diambil dari berkas. PDF scan dan foto melewati OCR.
2. LLM dipanggil tiga kali dan hanya boleh memilih jenis dari daftar taksonomi (7 kategori, 56 jenis). Kategori dan subkategori diturunkan dari jenis, sehingga AI tidak bisa mengarang kategori.
3. Skor keyakinan adalah tingkat kesepakatan ketiga panggilan. Dokumen langsung masuk arsip hanya kalau ketiganya sepakat.
4. Metadata yang tidak tertulis di dokumen diisi kosong, tidak ditebak.

Rincian ada di Arsitektur AI-DMC dan Buku Pengembangan Bagian 3 dan 4.

## 5. Hasil evaluasi AI

### 5.1 Pemilihan model

Uji banding awal (4 November 2026) pada 38 dokumen sintetis, laptop RTX 3050 6 GB:

| Ukuran | `qwen3:8b` | `gemma3:4b` | `gemma4:e4b` |
|---|---|---|---|
| Akurasi kategori | 84,2% | 55,3% | 92,1% |
| Akurasi jenis | 78,9% | 26,3% | 73,7% |
| Tanggal terbit benar | 78,9% | 71,1% | 94,7% |
| Tanggal dikarang pada dokumen tanpa tanggal | 7 dari 13 | 9 dari 13 | 1 dari 13 |
| Waktu 6 dokumen campuran | 362,7 detik | 151,5 detik | 138,9 detik |

`gemma4:e4b` dipilih karena kategorinya paling akurat, paling jarang mengarang tanggal, dan paling cepat. Setelah itu prompt disetel untuk model ini.

### 5.2 Evaluasi akhir dengan data uji

Data: 45 dokumen dummy berformat mirip dokumen asli (PDF digital, PDF scan, foto, DOCX), dibuat dengan `tools/generate_dummy_format_nyata.py`. Diuji 21 November 2026.

| Field | Akurasi |
|---|---|
| Kategori | 100% |
| Subkategori | 97,8% |
| Jenis | 97,8% |
| Nomor dokumen | 100% |
| Tanggal terbit | 100% |
| Periode | 91,1% |

- Lolos otomatis (langsung terverifikasi): 97,8%.
- Akurasi jenis di antara yang lolos otomatis: 100%. Artinya dokumen yang tidak dicek dosen semuanya benar pada data uji ini.
- Rata-rata waktu: 51 detik per dokumen di laptop RTX 3050 6 GB.

Sebelum penyetelan prompt terakhir, data yang sama menghasilkan jenis 86,7% dan lolos otomatis 82,2%. Penyetelan itu menambah petunjuk untuk jenis yang tertukar pada data ini (SK kepanitiaan dan SK pembina kegiatan mahasiswa, serta beberapa jenis surat tugas).

### 5.3 Uji dengan dokumen asli

Data: 22 dokumen asli dari satu dosen, dikelompokkan dosen tersebut ke folder kategori.

- Tidak ada dokumen yang gagal diproses.
- Kategori cocok dengan folder dosen 40,9%. Selisih terbesar karena SK pembimbing TA dan berita acara sidang masuk Pendidikan (PND) menurut taksonomi rancangan, tetapi masuk Penunjang (PNJ) menurut folder dosen. Kalau diukur terhadap taksonomi, kategori benar 95,5% sampai 100%.
- Rata-rata 181 detik per dokumen, karena sebagian besar dokumen asli adalah scan dan OCR masih berjalan di CPU laptop.
- Dokumen asli belum diberi label jenis, tanggal, dan nomor, jadi akurasi field tersebut belum terukur.

**Keputusan yang dibutuhkan dari Admin CoE:** SK pembimbing TA dan berita acara sidang masuk PND atau PNJ.

### 5.4 Keterbatasan evaluasi

- **Angka 97,8% kemungkinan terlalu optimis.** Petunjuk di prompt ditambahkan setelah melihat kesalahan pada 45 dokumen uji yang sama, tanpa set uji terpisah untuk mengukur ulang. Kenaikan 86,7% ke 97,8% menunjukkan perbaikannya bekerja untuk pola kesalahan itu, tetapi belum membuktikan akurasi pada dokumen baru. Evaluasi berikutnya perlu memakai dokumen yang belum pernah dilihat saat menyetel prompt.
- Data uji akhir adalah dokumen dummy. Bentuknya meniru dokumen asli, tetapi variasi dokumen asli (scan buram, cap, tulisan tangan, format lama) lebih besar.
- Dokumen asli baru 22 berkas dari satu dosen. Rancangan meminta 100 sampai 200 dokumen asli untuk evaluasi yang meyakinkan.
- Semua pengukuran waktu dilakukan di laptop dengan GPU 6 GB. Model tidak muat penuh di GPU, jadi server dengan GPU 12 GB diperkirakan jauh lebih cepat, tetapi belum diukur.

## 6. Keamanan dan privasi

- Semua AI berjalan lokal. Tidak ada panggilan ke layanan AI publik.
- Dosen hanya melihat dokumennya sendiri. Dosen yang disebut di dokumen orang lain baru bisa melihat setelah pengunggah menyetujui, dan tidak bisa mengubahnya. Dokumen yang tidak boleh dilihat dijawab "tidak ditemukan", supaya keberadaannya tidak bocor.
- Log audit dilindungi database dari perubahan dan penghapusan.
- Teks dokumen diperlakukan sebagai data. Kalimat yang menyerupai perintah ke AI disamarkan, dan dokumennya selalu masuk Kotak Verifikasi. Empat variasi serangan prompt injection diuji dan tertahan.
- Data dosen (`data/`, `storage/`, `.env`) tidak masuk repositori.

Aturan lengkap, hak dosen, dan daftar celah yang belum ditutup ada di Kebijakan Data dan Keamanan.

## 7. Pengujian

| Pengujian | Hasil |
|---|---|
| Tes otomatis backend | 23 tes lulus: alur unggah sampai verifikasi, hak akses antardosen, duplikat, validasi berkas, ambang skor, riwayat koreksi, log audit, perintah pengelola |
| Tes otomatis pipeline | 53 tes lulus: ekstraksi, klasifikasi, voting, penyaring prompt injection, pembersihan metadata |
| Uji ujung ke ujung | PDF digital, PDF scan, foto, dan DOCX lewat aplikasi sampai status akhir |
| Uji tampilan | Laman Unggah, Kotak Verifikasi, dan Arsip pada lebar 375 px dan 1280 px tanpa tampilan terpotong (UI V2 Review) |
| Uji pemasangan server | Dependensi terpasang di Ubuntu 24.04 tanpa konflik, aplikasi dapat dimuat |
| Uji cadangan dan pemulihan | Database dipulihkan ke PostgreSQL kosong dengan jumlah baris sama dan pelindung log audit utuh |

## 8. Jadwal dan realisasi

| Minggu | Rencana | Realisasi |
|---|---|---|
| 0 (31 Okt sampai 1 Nov) | Penyiapan repo, konfirmasi ke pembimbing | Selesai |
| 1 (2 sampai 6 Nov) | Pipeline AI berjalan, kerangka aplikasi | Selesai, termasuk uji banding model awal |
| 2 (9 sampai 13 Nov) | Pipeline tersambung ke aplikasi, uji data asli | Selesai. Data asli yang tersedia 22 dokumen |
| 3 (16 sampai 20 Nov) | Model final, deploy, uji coba dosen, serah terima | Model final dan penyetelan prompt selesai. Deploy dan uji coba dosen belum, karena server belum tersedia |
| Tambahan (21 sampai 23 Nov) | | Perbaikan hak akses, perintah pengelola, berkas deploy, dokumen serah terima |

Tugas di Rincian Tugas yang belum selesai: deploy ke server (B-08), uji coba dosen (B-09), few-shot dari koreksi dosen (P1-13), dan uji banding pada 100 sampai 200 dokumen asli.

## 9. Kendala

1. **Server belum tersedia.** Semua pengembangan dan pengukuran dilakukan di laptop dengan GPU 6 GB. Model AI tidak muat penuh di GPU, dan OCR berjalan di CPU.
2. **Data asli terbatas.** Hanya 22 dokumen dari satu dosen, tanpa label lengkap.
3. **Taksonomi belum final.** Pengelompokan beberapa jenis dokumen di rancangan berbeda dengan kebiasaan dosen.
4. **Akses repositori.** Push ke repositori utama ditolak karena akun tim hanya punya izin baca. Semua pekerjaan ada di branch `feat/ai-asli-dan-perbaikan-ui` dan belum masuk repositori utama.

## 10. Rekomendasi tahap berikutnya

Urut dari yang paling mendesak:

1. **Sediakan server** sesuai Kebutuhan Server (GPU NVIDIA 12 GB, RAM 32 GB), lalu deploy mengikuti Panduan Instalasi.
2. **Putuskan taksonomi** untuk SK pembimbing TA dan berita acara sidang.
3. **Uji coba dengan 3 sampai 5 dosen** selama dua minggu, sambil mengumpulkan dokumen asli berlabel. Target 100 dokumen untuk evaluasi ulang, dengan sebagian disisihkan sebagai set uji yang tidak dipakai menyetel prompt.
4. **Lengkapi fitur admin:** status akun nonaktif, laman admin, dan kebijakan hapus dokumen.
5. **Tambah batas login per alamat IP** setelah reverse proxy meneruskan IP asli.
6. **Manfaatkan koreksi dosen** sebagai contoh di prompt (few-shot), lalu fine-tune setelah data cukup.
7. Setelah stabil, lanjut ke fitur fase berikutnya: Tanya Arsip, generator paket jabatan fungsional dan akreditasi, dan SSO kampus.

Daftar lengkap pekerjaan teknis yang belum selesai ada di Buku Pengembangan Bagian 9.

## 11. Dokumen serah terima

| Dokumen | Untuk |
|---|---|
| Panduan Dosen | Dosen pengguna aplikasi |
| Panduan Ringkas Dosen (1 halaman) | Dibagikan atau ditempel saat sosialisasi |
| Panduan Admin dan Pengelola | Admin CoE dan pengelola server |
| Kebijakan Data dan Keamanan | Admin CoE, pimpinan prodi |
| Kebutuhan Server | Pengadaan dan pengelola jaringan |
| Panduan Instalasi dan Operasional | Pengelola server |
| Arsitektur AI-DMC | Pengembang |
| Buku Pengembangan | Pengembang lanjutan |
| Laporan Akhir (dokumen ini) | Pembimbing, Ketua CoE |

Kode sumber ada di branch `feat/ai-asli-dan-perbaikan-ui`. Semua dokumen di atas ada di folder `docs/`, dalam format Markdown dan PDF.
