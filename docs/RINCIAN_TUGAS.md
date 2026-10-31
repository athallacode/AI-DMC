# Rincian Tugas Tim AI-DMC (MVP)

> Pasangan dari `docs/PEMBAGIAN_PERAN.md`. Dokumen peran menjelaskan **siapa pegang apa**, dokumen ini menjelaskan **apa saja yang harus dikerjakan, kapan, dan kapan dianggap selesai**.

## Cara Pakai
1. Setiap tugas punya ID: `B-xx` (bersama), `P1-xx` (Orang 1), `P2-xx` (Orang 2).
2. Jadikan setiap tugas satu GitHub Issue dengan judul diawali ID, misalnya `P1-05 Ekstraksi teks PDF dan DOCX`.
3. Centang kotak di file ini lewat PR saat tugas selesai, atau cukup tutup Issue-nya.
4. Kolom **Butuh** menunjukkan tugas lain yang harus selesai dulu. Kalau tertahan, kabari di sync harian.
5. Semua tugas tetap mengikuti **Definition of Done** di `PEMBAGIAN_PERAN.md` Bagian 9.

## Ringkasan Jadwal

| Minggu | Tanggal | Fokus |
|---|---|---|
| 0 | 31 Okt s.d. 1 Nov | Setup repo, konfirmasi ke pembimbing |
| 1 | 2 s.d. 6 Nov | Orang 1 membuktikan AI-nya jalan, Orang 2 membangun kerangka aplikasi |
| 2 | 9 s.d. 13 Nov | Sambungkan pipeline ke aplikasi, uji di data asli |
| 3 | 16 s.d. 20 Nov | Uji banding model, rapikan, deploy, uji coba dosen, serahkan |

## Titik Serah Terima (Handoff)

Ini momen di mana pekerjaan satu orang dibutuhkan orang lain. Paling rawan telat, jadi diprioritaskan.

| Kapan | Dari | Ke | Apa |
|---|---|---|---|
| Senin 2 Nov | Orang 1 | Orang 2 | `pipeline/mock.py` (P1-01) |
| Senin 2 Nov | Orang 1 | Orang 2 | `pipeline/config/taxonomy.json` versi awal (P1-04) |
| Jumat 6 Nov | Orang 1 | Orang 2 | `process_document()` versi pertama yang jalan (P1-08) |
| Rabu 11 Nov | Orang 2 | Orang 1 | Endpoint ekspor koreksi (P2-18) |
| Jumat 13 Nov | Bersama | | Pipeline asli terpasang di aplikasi, tes end-to-end lolos (B-06, B-07) |

---

## A. Tugas Bersama

| ID | Tugas | Butuh | Selesai kalau |
|---|---|---|---|
| B-01 | Setup repo: struktur folder, `README.md`, `.gitignore`, `AGENTS.md`, dokumen di `docs/`, skill desain | | Struktur sesuai `PEMBAGIAN_PERAN.md` Bagian 5, `data/` dan `storage/` ter-ignore |
| B-02 | `docker-compose.yml` berisi PostgreSQL, backend, frontend (Ollama opsional untuk lokal) | B-01 | `docker compose up` menjalankan semua layanan di laptop masing-masing |
| B-03 | `.env.example` (DB, port, model Ollama, ambang keyakinan, secret JWT) | B-01 | Semua konfigurasi dibaca dari env, tidak ada nilai rahasia di kode |
| B-04 | Kirim pesan ke pembimbing: minta data, konfirmasi pendekatan LLM, akses server, kategori prioritas, hari laporan | | Pesan terkirim, jawaban dicatat di `PEMBAGIAN_PERAN.md` Bagian 10 |
| B-05 | Review dan bekukan kontrak Bagian 4 (output pipeline, API, skema DB) | | Dua-duanya setuju, perubahan berikutnya wajib lewat PR |
| B-06 | Ganti mock dengan pipeline asli di backend | P1-08, P2-11 | Upload berkas asli menghasilkan klasifikasi asli di aplikasi |
| B-07 | Tes end-to-end dengan 10 dokumen campuran (PDF digital, scan, DOCX, foto) | B-06 | Semua dokumen sampai ke status akhir tanpa error tak tertangani |
| B-08 | Deploy ke server CoE | P1-17, P2-19 | Aplikasi bisa diakses dari jaringan kampus |
| B-09 | Uji coba dengan beberapa dosen, kumpulkan masukan | B-08, P2-20 | Masukan tercatat di Issue berlabel `diskusi` |
| B-10 | Laporan mingguan ke pembimbing (3 kali) | | File di `docs/laporan-mingguan/` + terkirim |
| B-11 | Laporan akhir dan demo | semua | Demo jalan dari upload sampai arsip, laporan diserahkan |

### Checklist Bersama
- [ ] B-01 Setup repo
- [ ] B-02 Docker Compose
- [ ] B-03 `.env.example`
- [ ] B-04 Pesan ke pembimbing
- [ ] B-05 Bekukan kontrak
- [ ] B-06 Integrasi pipeline asli
- [ ] B-07 Tes end-to-end
- [ ] B-08 Deploy server
- [ ] B-09 Uji coba dosen
- [ ] B-10 Laporan mingguan (1 / 2 / 3)
- [ ] B-11 Laporan akhir dan demo

---

## B. Orang 1: AI Pipeline Engineer

### Minggu 1 (2 s.d. 6 Nov): Buktikan AI-nya jalan

| ID | Tugas | Hari | Butuh | Selesai kalau |
|---|---|---|---|---|
| P1-01 | **`pipeline/mock.py`**: `process_document()` palsu yang mengembalikan JSON sesuai kontrak 4.1. Sediakan 3 variasi: skor tinggi, skor rendah, gagal. | Senin | B-05 | Orang 2 bisa import dan memakainya |
| P1-02 | Setup lingkungan: `requirements.txt`, install Ollama, unduh 1 model kecil (Gemma 4 E4B atau Qwen3 8B), install PaddleOCR | Senin | | Model menjawab prompt tes, PaddleOCR membaca 1 gambar contoh |
| P1-03 | Kumpulkan 15 s.d. 20 dokumen dummy + label manual di `data/labels.csv` (nama_berkas, kategori, subkategori, jenis, nomor_dokumen, tanggal_terbit, periode) | Senin s.d. Selasa | | Campuran PDF digital, scan, DOCX, foto. Minimal 5 dari kategori PND. Data pribadi disamarkan |
| P1-04 | **`pipeline/config/taxonomy.json`**: semua kategori, subkategori, jenis dari Bagian 3 rancangan, plus `LAINNYA` | Senin | | Valid JSON, diserahkan ke Orang 2 untuk dropdown koreksi |
| P1-05 | **`extract.py`**: deteksi jenis berkas dan ekstraksi teks. PDF dicek per halaman: kalau teks hampir kosong dianggap scan. DOCX pakai python-docx. | Selasa | P1-02 | Mengembalikan `teks` dan `jenis_berkas` dengan benar untuk 4 jenis berkas |
| P1-06 | **`ocr.py`**: PaddleOCR untuk gambar dan PDF scan. PDF scan dirender per halaman (sekitar 200 dpi), batasi jumlah halaman yang di-OCR (misalnya 5 halaman pertama) | Selasa s.d. Rabu | P1-05 | Teks SK hasil scan terbaca dan bisa dipahami manusia |
| P1-07 | **`classify.py`**: prompt klasifikasi + ekstraksi metadata, output JSON. Validasi dengan Pydantic, retry maksimal 2 kali kalau JSON rusak, kategori di luar taksonomi jadi `LAINNYA` | Rabu s.d. Kamis | P1-04 | Output selalu valid sesuai kontrak, tidak pernah crash karena output LLM |
| P1-08 | **`main.py`**: `process_document()` menggabungkan P1-05 s.d. P1-07, mencatat `waktu_proses_detik` dan `model_dipakai`, semua error ditangkap jadi `status: "gagal"` | Kamis | P1-05, P1-06, P1-07 | Fungsi tidak pernah melempar exception ke pemanggil |
| P1-09 | **`eval/run_eval.py`**: jalankan pipeline ke semua dokumen di `labels.csv`, hitung akurasi kategori, akurasi jenis, akurasi tiap field metadata, simpan laporan ke `eval/hasil/` | Jumat | P1-03, P1-08 | Ada angka akurasi awal + daftar dokumen yang salah beserta dugaan penyebabnya |

### Minggu 2 (9 s.d. 13 Nov): Perkuat dan uji di data asli

| ID | Tugas | Butuh | Selesai kalau |
|---|---|---|---|
| P1-10 | **Skor keyakinan**: jalankan klasifikasi beberapa kali (misalnya 3) dan hitung tingkat kesepakatan, atau pakai logprobs kalau model mendukung. Dokumentasikan metodenya di `pipeline/README.md` | P1-08 | Skor dokumen yang jelas tinggi, dokumen yang ambigu rendah. Diuji di data dummy |
| P1-11 | **Pengaman prompt injection**: teks dokumen dibungkus pembatas yang jelas, prompt menegaskan isi dokumen adalah data, bukan instruksi | P1-07 | Uji dengan dokumen berisi kalimat "abaikan instruksi sebelumnya", hasil tetap normal |
| P1-12 | **Dokumen panjang**: kalau teks melebihi batas konteks, ambil bagian awal + akhir (SK biasanya penting di kop dan bagian penetapan) | P1-07 | Dokumen 30+ halaman tetap terproses tanpa error |
| P1-13 | **Few-shot dari koreksi**: `process_document()` menerima parameter opsional `contoh_fewshot` (daftar contoh hasil koreksi dosen) yang disisipkan ke prompt | P2-18, B-05 | Perubahan kontrak disetujui Orang 2, akurasi tidak turun saat contoh ditambahkan |
| P1-14 | **Uji di data asli dari CoE**: label manual, jalankan evaluasi, perbaiki prompt, evaluasi ulang | data dari pembimbing | Laporan akurasi sebelum dan sesudah perbaikan |
| P1-15 | Bantu B-06: pastikan pipeline jalan di dalam container backend | P1-08 | B-06 lolos |

### Minggu 3 (16 s.d. 20 Nov): Pilih model final dan serahkan

| ID | Tugas | Butuh | Selesai kalau |
|---|---|---|---|
| P1-16 | **Uji banding 2 s.d. 3 model** di set uji yang sama: akurasi, waktu per dokumen, pemakaian memori GPU | P1-14 | Tabel perbandingan + rekomendasi model final |
| P1-17 | **Setup di server**: Ollama + model final + PaddleOCR | akses server | Pipeline jalan di server dengan model final |
| P1-18 | **Kalibrasi ambang 0,85**: hitung berapa persen dokumen lolos otomatis dan berapa yang salah di antara yang lolos, usulkan ambang baru kalau perlu | P1-10, P1-16 | Ambang final tertulis di `.env` dan laporan |
| P1-19 | **Dokumentasi**: `pipeline/README.md` (cara pakai, metode skor, cara ganti model) + laporan akurasi final | semua | Orang lain bisa menjalankan pipeline hanya dari README |

### Checklist Orang 1
- [ ] P1-01 Mock pipeline
- [ ] P1-02 Setup lingkungan
- [ ] P1-03 Dataset dummy + label
- [ ] P1-04 `taxonomy.json`
- [ ] P1-05 Ekstraksi teks
- [ ] P1-06 OCR
- [ ] P1-07 Klasifikasi LLM
- [ ] P1-08 `process_document()`
- [ ] P1-09 Evaluasi awal
- [ ] P1-10 Skor keyakinan
- [ ] P1-11 Pengaman prompt injection
- [ ] P1-12 Dokumen panjang
- [ ] P1-13 Few-shot dari koreksi
- [ ] P1-14 Uji data asli
- [ ] P1-15 Bantu integrasi
- [ ] P1-16 Uji banding model
- [ ] P1-17 Setup di server
- [ ] P1-18 Kalibrasi ambang
- [ ] P1-19 Dokumentasi pipeline

---

## C. Orang 2: Application Engineer

### Minggu 1 (2 s.d. 6 Nov): Kerangka aplikasi

| ID | Tugas | Hari | Butuh | Selesai kalau |
|---|---|---|---|---|
| P2-01 | **Wireframe** 4 laman (Login, Unggah, Kotak Verifikasi, Arsip Saya) versi desktop dan HP, mengikuti skill `ai-dmc-apple-glass-ui` | Senin | | Disetujui Orang 1, gambar disimpan di `docs/wireframe/` |
| P2-02 | **Setup backend**: struktur FastAPI, config dari env, koneksi PostgreSQL (SQLAlchemy), Alembic | Senin | B-02 | `GET /health` menjawab, koneksi DB jalan |
| P2-03 | **Migrasi skema** sesuai `PEMBAGIAN_PERAN.md` 4.3 (5 tabel) + seed 2 dosen dummy dan 1 admin | Selasa | P2-02, B-05 | `alembic upgrade head` membuat semua tabel, seed bisa dipakai login |
| P2-04 | **Login**: hash password (bcrypt atau argon2), token JWT, dependency `current_user`, catat `login` di audit_log | Selasa | P2-03 | Endpoint tanpa token ditolak 401 |
| P2-05 | **`POST /documents`**: banyak berkas sekaligus, validasi tipe (PDF, DOCX, JPG, PNG) dan ukuran (maks 20 MB per berkas), hitung SHA-256, tolak duplikat, simpan ke `storage/<uuid>.<ext>`, status `diproses`, catat audit | Rabu | P2-04 | Duplikat mengembalikan pesan "Sudah pernah diunggah" + id dokumen lama |
| P2-06 | **`GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/file`** dengan filter status, kategori, tahun. Cek akses: hanya pemilik atau dosen yang tertaut di `dokumen_dosen`, dokumen `rahasia` hanya pemilik | Rabu s.d. Kamis | P2-05 | Dosen A tidak bisa membuka dokumen dosen B (dites) |
| P2-07 | **`GET /taxonomy`**: baca `pipeline/config/taxonomy.json` | Kamis | P1-04 | Mengembalikan struktur kategori lengkap |
| P2-08 | **Setup frontend**: Next.js, token desain di `globals.css`, font Inter, layout dengan navbar glass + tab bar HP | Senin s.d. Selasa | | Tampilan dasar sesuai skill desain di 375px dan 1280px |
| P2-09 | **Laman Login** | Rabu | P2-04, P2-08 | Login berhasil masuk ke laman Unggah, gagal menampilkan pesan jelas |
| P2-10 | **Laman Unggah**: dropzone, panel antrean mengambang, polling status tiap 2 s.d. 3 detik sampai selesai | Kamis s.d. Jumat | P2-05, P2-09 | Upload 5 berkas sekaligus, status tiap berkas terlihat berubah |

### Minggu 2 (9 s.d. 13 Nov): Alur verifikasi lengkap

| ID | Tugas | Butuh | Selesai kalau |
|---|---|---|---|
| P2-11 | **Background task**: setelah upload, panggil `process_document()` (mock dulu), petakan hasil ke kolom dan `dokumen_dosen` sesuai aturan pemetaan 4.3, terapkan ambang dari env (default 0,85), status `gagal` kalau pipeline gagal | P1-01, P2-05 | Dokumen skor tinggi langsung `terverifikasi`, skor rendah `menunggu_verifikasi` |
| P2-12 | **`POST /approve`, `PATCH /documents/{id}`, `POST /reject`**: PATCH menyimpan nilai sebelum dan sesudah ke tabel `koreksi`, semua aksi tercatat di audit_log | P2-11 | Koreksi tersimpan lengkap, audit_log terisi |
| P2-13 | **Laman Kotak Verifikasi** + form koreksi (sheet glass, field terisi hasil AI, dropdown dari `/taxonomy`) | P2-07, P2-12 | Dosen bisa Setujui, Koreksi, Tolak dari laman ini |
| P2-14 | **Laman Arsip Saya**: toolbar filter (kategori, status, tahun), tabel di desktop, kartu di HP, pratinjau berkas | P2-06 | Filter bekerja, dokumen bisa dibuka |
| P2-15 | **Toast + Urungkan** untuk Setujui dan Tolak | P2-13 | Aksi bisa dibatalkan dalam beberapa detik |
| P2-16 | **Indikator keyakinan AI + pill status** sesuai skill desain | P2-13 | Skor di bawah ambang menampilkan "AI kurang yakin, mohon dicek" |
| P2-17 | **Bagian "Dosen terkait"** di kartu verifikasi: daftar dari `dokumen_dosen`, bisa dikonfirmasi atau dikoreksi | P2-13 | Kolom `dikonfirmasi` jadi true setelah disetujui |
| P2-18 | **`GET /admin/koreksi/export`** (khusus admin): ekspor koreksi dalam JSON untuk dipakai Orang 1 sebagai few-shot | P2-12 | Diserahkan ke Orang 1 paling lambat Rabu 11 Nov |

### Minggu 3 (16 s.d. 20 Nov): Rapikan dan deploy

| ID | Tugas | Butuh | Selesai kalau |
|---|---|---|---|
| P2-19 | **Dockerfile** backend dan frontend, siapkan untuk server | B-02 | Image jalan di server CoE |
| P2-20 | **Panduan singkat untuk dosen uji coba** (1 halaman: cara login, unggah, verifikasi) | P2-14 | Dibagikan sebelum B-09 |
| P2-21 | **Cek responsif dan aksesibilitas**: 375px dan 1280px, bisa dipakai pakai keyboard, kontras lolos checklist skill desain | P2-14 | Semua item checklist skill desain Bagian 11 terpenuhi |
| P2-22 | **Audit log lengkap**: pastikan unduh berkas juga tercatat, tabel audit tidak bisa di-UPDATE atau DELETE dari aplikasi | P2-06 | Dicek manual dengan query |
| P2-23 | **Perbaikan dari uji coba dosen** | B-09 | Issue dari uji coba ditutup atau dijadwalkan ke fase berikutnya |
| P2-24 | **Dokumentasi**: `backend/README.md` dan `frontend/README.md` (cara setup, env, migrasi) | semua | Orang baru bisa menjalankan aplikasi dari README |

### Checklist Orang 2
- [ ] P2-01 Wireframe
- [ ] P2-02 Setup backend
- [ ] P2-03 Migrasi skema + seed
- [ ] P2-04 Login
- [ ] P2-05 Upload + cek duplikat
- [ ] P2-06 Daftar, detail, unduh + cek akses
- [ ] P2-07 Endpoint taksonomi
- [ ] P2-08 Setup frontend
- [ ] P2-09 Laman Login
- [ ] P2-10 Laman Unggah
- [ ] P2-11 Background task + ambang
- [ ] P2-12 Approve, koreksi, reject
- [ ] P2-13 Laman Kotak Verifikasi
- [ ] P2-14 Laman Arsip Saya
- [ ] P2-15 Toast + Urungkan
- [ ] P2-16 Indikator keyakinan + pill status
- [ ] P2-17 Dosen terkait
- [ ] P2-18 Ekspor koreksi
- [ ] P2-19 Dockerfile
- [ ] P2-20 Panduan dosen
- [ ] P2-21 Responsif + aksesibilitas
- [ ] P2-22 Audit log lengkap
- [ ] P2-23 Perbaikan dari uji coba
- [ ] P2-24 Dokumentasi aplikasi

---

## D. Kalau Waktu Mepet: Urutan yang Boleh Dipangkas

Pangkas dari atas ke bawah. Yang di luar daftar ini wajib ada untuk demo.

1. P2-15 Toast + Urungkan
2. P1-13 Few-shot dari koreksi (P2-18 ikut dipangkas)
3. P2-17 Konfirmasi dosen terkait (data tetap tersimpan, hanya UI-nya ditunda)
4. P1-16 Uji banding model (cukup 1 model, tulis sebagai rencana lanjutan)
5. P1-12 Dokumen panjang (batasi jumlah halaman saja)

## E. Risiko dan Antisipasi

| Risiko | Antisipasi |
|---|---|
| Data asli dari CoE telat | Kerjakan semua dengan data dummy dulu, P1-14 digeser tanpa menahan tugas lain |
| Akses server GPU belum ada | Develop pakai model kecil di laptop, deploy di akhir. Siapkan demo dari laptop sebagai cadangan |
| Akurasi klasifikasi rendah | Perbaiki prompt dan contoh few-shot dulu, baru pertimbangkan ganti model. Kotak Verifikasi tetap jadi pengaman |
| OCR lambat di server tanpa GPU | Batasi halaman yang di-OCR, prioritaskan PDF digital yang tidak perlu OCR |
| Kontrak berubah di tengah jalan | Semua perubahan lewat PR yang disetujui dua-duanya (B-05) |
