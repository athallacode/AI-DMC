# Materi Presentasi AI-DMC

Bahan untuk menyusun slide presentasi hasil pengembangan AI-DMC tahap MVP. Tiap slide berisi judul, poin isi, angka, saran visual, dan sumber dokumennya. Poin ditulis ringkas supaya bisa langsung dipindah ke slide; penjelasan lisan ada di bagian "Catatan pembicara".

Semua angka diambil dari dokumen di folder `docs/` dan hasil uji 24 November 2026. Jangan menampilkan nama dosen, NIM, atau isi dokumen asli di slide.

Usulan durasi: 15 sampai 20 menit, 14 slide.

---

## Slide 1. Judul

- **AI-DMC: AI Document Management Center**
- Arsip dokumen eviden dosen dengan AI lokal
- CoE AIIS Telkom University, tahap MVP (31 Oktober sampai 24 November 2026)
- Nama tim dan pembimbing

Visual: logo Telkom University dan AIIS, tangkapan layar laman Unggah.

---

## Slide 2. Masalah

- Dosen mengumpulkan dokumen eviden untuk BKD, jabatan fungsional, dan akreditasi
- Dokumen tersebar di banyak tempat (email, WhatsApp, Google Drive, map fisik)
- Setiap dokumen harus dipilah dan diisi datanya satu per satu
- Dokumen berisi data pribadi, jadi tidak aman dikirim ke layanan AI publik

Catatan pembicara: tekankan bahwa masalahnya bukan menyimpan berkas, tetapi memilah dan mengisi metadata yang berulang setiap periode.

Sumber: Laporan Akhir Bagian 2.

---

## Slide 3. Solusi dan tujuan

AI-DMC: dosen cukup mengunggah, AI memilah dan mengisi data, dosen hanya menyetujui atau mengoreksi.

Tujuan:
1. Mengurangi kerja memilah dan mengisi metadata secara manual
2. Satu arsip tertata menurut kategori Tridharma dan penunjang
3. Data pribadi aman: seluruh AI berjalan di server sendiri

Visual: tiga ikon, Unggah, AI memilah, Dosen menyetujui.

Sumber: Laporan Akhir Bagian 1 dan 2; acuan rancangan DOK-CoE-AIIS-DMC-001.

---

## Slide 4. Cara kerja bagi dosen

1. Masuk, lalu seret banyak berkas sekaligus (PDF, DOCX, JPG, PNG, maksimal 20 MB)
2. AI membaca, menentukan jenis dokumen, dan mengisi nomor, tanggal, periode, dosen terkait
3. Yakin (skor 0,85 ke atas): langsung masuk arsip
4. Ragu: masuk Kotak Verifikasi, dosen menekan Setujui, Koreksi, atau Tolak
5. Arsip Saya: cari dan filter menurut kategori, status, tahun

Visual: diagram alur pengguna (Arsitektur Bagian 2), atau tiga tangkapan layar: Unggah, Kotak Verifikasi, Arsip.

Sumber: Arsitektur Bagian 2; Panduan Ringkas Dosen.

---

## Slide 5. Kategori dokumen

| Kode | Kategori | Contoh |
|---|---|---|
| PND | Pendidikan dan Pengajaran | SK mengajar, RPS, daftar nilai, presensi |
| PNL | Penelitian | SK penelitian, proposal, laporan |
| PKM | Pengabdian kepada Masyarakat | SK abdimas, laporan, dokumentasi |
| PUB | Publikasi dan HKI | Artikel jurnal, prosiding, sertifikat HKI |
| PNJ | Penunjang | SK kepanitiaan, sertifikat narasumber |
| ADM | Administrasi Kepegawaian | SK jabatan fungsional, ijazah, serdos |

- 7 kategori (termasuk Lainnya), 57 jenis dokumen
- AI hanya boleh memilih jenis dari daftar ini, sehingga tidak bisa mengarang kategori

Sumber: `pipeline/config/taxonomy.json`; Laporan Akhir Bagian 4.

---

## Slide 6. Arsitektur

- Frontend Next.js 15, backend FastAPI, database PostgreSQL 17
- Ekstraksi teks PyMuPDF dan python-docx; OCR PaddleOCR untuk scan dan foto
- LLM lokal: Ollama dengan model gemma4:e4b
- Semua komponen di satu server, tanpa layanan AI publik

Visual: diagram arsitektur sistem (Arsitektur Bagian 1, sudah ada di `Arsitektur-AI-DMC.pdf`).

Sumber: Arsitektur Bagian 1; Laporan Akhir Bagian 4.

---

## Slide 7. Cara AI memutuskan

1. Teks diambil dari berkas; halaman scan dan foto melewati OCR
2. AI dipanggil 3 kali dan hanya boleh memilih jenis dari taksonomi
3. Skor keyakinan = tingkat kesepakatan 3 panggilan. Langsung diarsipkan hanya kalau ketiganya sepakat
4. Data yang tidak tertulis di dokumen diisi kosong, tidak ditebak
5. Kalimat di dokumen yang menyerupai perintah ke AI disamarkan, dan dokumennya selalu dicek dosen

Catatan pembicara: poin 3 adalah pengaman utama. Dokumen yang membuat AI ragu tidak pernah lolos tanpa dicek manusia.

Sumber: Laporan Akhir Bagian 4 dan 6.

---

## Slide 8. Pemilihan model AI

Uji banding 38 dokumen, laptop dengan GPU 6 GB (4 November 2026):

| | qwen3:8b | gemma3:4b | gemma4:e4b |
|---|---|---|---|
| Kategori benar | 84,2% | 55,3% | **92,1%** |
| Tanggal benar | 78,9% | 71,1% | **94,7%** |
| Tanggal dikarang (dari 13) | 7 | 9 | **1** |
| Waktu 6 dokumen | 363 dtk | 152 dtk | **139 dtk** |

Dipilih gemma4:e4b: paling akurat untuk kategori, paling jarang mengarang, paling cepat.

Visual: grafik batang kategori benar per model.

Sumber: Laporan Akhir Bagian 5.1.

---

## Slide 9. Hasil uji data dummy

45 dokumen dummy berformat mirip asli (PDF digital, scan, foto, DOCX):

| Field | Akurasi |
|---|---|
| Kategori | 100% |
| Jenis | 97,8% |
| Nomor dan tanggal dokumen | 100% |
| Lolos otomatis | 97,8%, semuanya benar |

Catatan jujur: prompt disetel dari kesalahan pada data yang sama, jadi angka ini kemungkinan terlalu optimis. Karena itu dilanjutkan uji dengan dokumen asli (slide berikutnya).

Sumber: Laporan Akhir Bagian 5.2 dan 5.4.

---

## Slide 10. Uji dengan dokumen asli (24 November 2026)

89 dokumen asli dari satu dosen, kategori Pendidikan dan Pengajaran: 24 SK mengajar, 31 daftar nilai, 34 presensi perkuliahan.

| Jenis | Jumlah | Benar, awal | Benar, sesudah perbaikan |
|---|---|---|---|
| SK mengajar | 24 | 23 (96%) | 24 (100%) |
| Daftar nilai | 31 | 30 (97%) | 31 (100%) |
| Presensi | 34 | 0 (0%) | 34 (100%) |
| Lolos otomatis tapi salah | | 28 dokumen | 0 dokumen |

- Hasil awal: presensi selalu terbaca sebagai daftar nilai, karena taksonomi belum punya jenis presensi
- Sesudah perbaikan, semua dokumen benar jenisnya, dan tidak ada lagi dokumen salah yang lolos tanpa dicek dosen
- Rata-rata waktu: sekitar 15 detik untuk PDF digital, sekitar 10 menit untuk dokumen scan (OCR di CPU laptop)

Catatan pembicara: ringkasan buatan AI sendiri sudah menyebut "laporan presensi", jadi AI paham isinya, hanya tidak ada pilihan jenis yang sesuai. Ini masalah taksonomi, bukan kemampuan model. Angka 100% ini berlaku untuk satu dosen dan tiga jenis dokumen Pendidikan; perbaikan juga disetel dari data yang sama, jadi perlu diuji ulang dengan dokumen dosen lain. Daftar nilai, presensi, dan SK gabungan diuji ulang dengan versi akhir; 23 SK lainnya diuji sebelum aturan terakhir ditambahkan (aturan itu tidak menyangkut SK).

Visual: tabel di atas, kolom awal dan sesudah berdampingan, baris presensi diberi warna penanda.

Sumber: hasil uji 24 November 2026 (`data/nyata_2026-11-24`, tidak masuk repositori).

---

## Slide 11. Temuan dan perbaikan dari dokumen asli

| Temuan | Dampak | Perbaikan |
|---|---|---|
| Taksonomi belum punya jenis presensi | 34 presensi salah jenis, 27 di antaranya lolos tanpa dicek | Jenis baru "Presensi perkuliahan" dan aturan pembeda dengan daftar nilai |
| Berita acara input nilai dari iGracias | Terbaca sebagai berita acara sidang dan lolos tanpa dicek | Aturan: bukti input nilai termasuk daftar nilai |
| SK berlampiran puluhan dosen | Jawaban AI meluber dan terpotong, 2 dari 6 SK scan gagal | Daftar dosen dibatasi 10 orang di skema jawaban AI |
| Lapisan teks PDF rusak (huruf tergeser, "1DPD" untuk "Nama") | AI membaca karakter acak dan salah jenis | Halaman rusak dikenali otomatis lalu dibaca ulang dengan OCR |
| Batas konteks bawaan server Ollama | Prompt atau jawaban AI bisa terpotong diam-diam | Ukuran konteks dikunci 16.384 token |

Hasil: semua 89 dokumen benar jenisnya (slide 10). Uji ulang data dummy untuk memastikan kategori lain tidak rusak: **[diisi setelah uji regresi selesai]**

Catatan pembicara: tiga dari lima temuan (teks PDF rusak, lampiran panjang, batas konteks) tidak akan muncul di data dummy. Ini alasan uji dengan dokumen asli wajib dilakukan sebelum dipakai dosen.

Sumber: hasil uji 24 November 2026.

---

## Slide 12. Keamanan dan privasi

- Seluruh AI berjalan lokal; tidak ada dokumen yang dikirim ke layanan AI publik
- Dosen hanya melihat dokumennya sendiri; dosen yang disebut di SK bersama baru melihat setelah disetujui pengunggah
- Log audit tidak bisa diubah atau dihapus, termasuk oleh admin
- Pertahanan prompt injection: 4 variasi serangan diuji dan tertahan
- Batas percobaan login: 5 kali gagal dalam 15 menit

Sumber: Laporan Akhir Bagian 6; Kebijakan Data dan Keamanan.

---

## Slide 13. Status dan kendala

Selesai:
- Delapan butir ruang lingkup MVP terpenuhi
- Tambahan: laman Admin, log audit, tampilan HP, berkas deploy server, antrean yang dilanjutkan otomatis
- Tes otomatis: 34 tes backend, 57 tes pipeline, semua lulus

Kendala:
- Server belum tersedia: semua uji di laptop GPU 6 GB, OCR di CPU (dokumen scan sekitar 10 menit)
- Data asli masih dari satu atau dua dosen dan sebagian besar kategori Pendidikan
- Taksonomi masih draf dan perlu keputusan Admin CoE

Sumber: Laporan Akhir Bagian 3, 7, dan 9.

---

## Slide 14. Rekomendasi tahap berikutnya

1. Sediakan server: GPU NVIDIA 12 GB, RAM 32 GB, SSD 512 GB, Ubuntu 24.04
2. Putuskan taksonomi: presensi perkuliahan, SK pembimbing TA dan berita acara sidang (PND atau PNJ)
3. Uji coba dengan 3 sampai 5 dosen selama 2 minggu, kumpulkan sekitar 100 dokumen asli dari semua kategori
4. Manfaatkan koreksi dosen untuk memperbaiki AI
5. Fitur fase berikutnya: Tanya Arsip, generator paket jabatan fungsional dan akreditasi, SSO kampus

Sumber: Laporan Akhir Bagian 10; Kebutuhan Server Bagian 2.

---

## Lampiran: bahan visual yang sudah tersedia

| Bahan | Lokasi |
|---|---|
| Diagram arsitektur, alur dosen, status dokumen, ERD | `docs/Arsitektur-AI-DMC.pdf` |
| Tangkapan layar aplikasi (7 gambar) | `docs/Panduan-Dosen-AI-DMC.pdf` |
| Ringkasan cara pakai satu halaman | `docs/Panduan-Ringkas-Dosen-AI-DMC.pdf` |
| Spesifikasi server | `docs/Kebutuhan-Server-AI-DMC.pdf` |
