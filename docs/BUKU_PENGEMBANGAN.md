# Buku Pengembangan AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Untuk pengembang lanjutan, November 2026

Buku ini untuk pengembang yang melanjutkan AI-DMC. Isinya cara kerja kode, aturan yang tidak boleh dilanggar, resep perubahan yang sering dibutuhkan, cara menguji, dan daftar pekerjaan yang belum selesai.

Cara menyiapkan laptop pengembang ada di Panduan Instalasi Bagian 3. Dokumen rujukan lain:

| Dokumen | Isi |
|---|---|
| `docs/PEMBAGIAN_PERAN.md` | Ruang lingkup MVP dan **kontrak antarmuka**: format JSON pipeline, endpoint API, skema database |
| `docs/ARSITEKTUR.md` | Diagram arsitektur, alur pengguna, status dokumen, ERD, sequence |
| `docs/PIPELINE_INTEGRATION.md` | Riwayat integrasi pipeline dan uji banding model |
| `docs/TINDAK_LANJUT.md` | Catatan diskusi yang belum dikerjakan |
| `pipeline/README.md`, `backend/README.md`, `frontend/README.md` | Rincian per bagian |
| `AGENTS.md` | Aturan untuk AI coding agent (berlaku juga untuk manusia) |

## 1. Aturan yang tidak boleh dilanggar

1. **Semua AI berjalan lokal.** Jangan menambah panggilan ke layanan AI publik (OpenAI, Anthropic, Google, dan sejenisnya) di kode aplikasi. Dokumen dosen berisi data pribadi.
2. **Jangan commit `data/`, `storage/`, `.env`, atau hasil evaluasi** (`pipeline/eval/hasil/`). Semuanya sudah ada di `.gitignore`; jangan dipaksa dengan `git add -f`.
3. **Teks dokumen adalah data, bukan instruksi.** Teks hasil OCR bisa berisi kalimat yang menyerupai perintah ke AI. Lihat Bagian 4.3.
4. **Metadata yang tidak ditemukan diisi `null`**, jangan ditebak.
5. **Kontrak antarmuka** di `docs/PEMBAGIAN_PERAN.md` (JSON pipeline, endpoint, skema database) tidak diubah tanpa persetujuan tertulis. Kalau memang perlu diubah, ubah kontraknya dulu, baru kodenya.
6. **Bahasa:** teks UI dan komentar kode dalam Bahasa Indonesia. Nama variabel konsisten per modul (pipeline memakai Bahasa Indonesia, backend kebanyakan Bahasa Inggris). Teks UI tidak memakai em-dash.
7. **Git:** kerjakan di branch `feat/...` atau `fix/...`, jangan langsung ke `main`. Format commit `<tipe>: <deskripsi>` dengan tipe `feat`, `fix`, `docs`, `chore`, `refactor`, atau `style`.

## 2. Peta repo

| Folder | Isi |
|---|---|
| `pipeline/` | Pipeline AI: ekstraksi teks, OCR, klasifikasi LLM, evaluasi. Bisa dipakai tanpa backend |
| `pipeline/config/taxonomy.json` | Daftar kategori, subkategori, dan jenis dokumen (7 kategori, 56 jenis) |
| `pipeline/prompts/klasifikasi_system.md` | Prompt sistem untuk LLM |
| `pipeline/eval/` | Skrip evaluasi akurasi dan templat label |
| `backend/app/` | FastAPI: API, model database, layanan, perintah pengelola |
| `backend/alembic/` | Migrasi database |
| `backend/tests/` | Tes backend (SQLite, pipeline mock) |
| `frontend/` | Next.js: laman Masuk, Unggah, Kotak Verifikasi, Arsip |
| `deploy/` | Berkas server: systemd, skrip pasang, cadangan, Caddy |
| `tools/` | Pembuat dokumen dummy untuk uji dan evaluasi |
| `docs/` | Dokumen tim, panduan, laporan mingguan |
| `.agents/skills/ai-dmc-apple-glass-ui/` | Panduan desain UI |

## 3. Alur data dari unggah sampai arsip

1. Frontend mengirim berkas ke `POST /documents` (maksimal 20 berkas, 20 MB per berkas).
2. Backend (`api/documents.py`) memeriksa tanda tangan berkas (PDF, PNG, JPG, DOCX), menghitung SHA-256, dan menolak duplikat. Berkas disimpan di `storage/` (`services/storage.py`) dan dicatat dengan status `diproses`.
3. Backend menjadwalkan `services/pipeline.process_document()` sebagai *background task* FastAPI. Dokumen diproses satu per satu (dikunci `_satu_per_satu`) supaya OCR dan LLM tidak berebut CPU dan GPU. Tabel `documents` sekaligus menjadi antrean: dokumen yang belum selesai tetap berstatus `diproses`.
4. Layanan pipeline memanggil fungsi yang ditunjuk `PIPELINE_IMPORT`:
   - mode `mock`: `integrations/mock.py`, hasil sintetis dari nama berkas;
   - mode `real`: `integrations/real.py`, yang meneruskan pengaturan backend ke `pipeline.main.process_document()`.
5. Hasil divalidasi dengan skema `PipelineResult` dan dicek terhadap taksonomi. Kalau skor keyakinan di atas atau sama dengan `CONFIDENCE_THRESHOLD` (0,85), status menjadi `terverifikasi`; kalau di bawah, `menunggu_verifikasi`. Galat apa pun membuat status `gagal` dengan pesan aman.
6. Dosen membuka Kotak Verifikasi, lalu menyetujui (`/approve`), menolak (`/reject`), atau mengoreksi (`PATCH`). Koreksi menyimpan snapshot sebelum dan sesudah di tabel `koreksi`.
7. Saat backend start, dokumen yang masih `diproses` (terputus oleh restart) diproses ulang di thread terpisah (`lanjutkan_antrean`). Jumlah percobaan dicatat di `metadata_lain._percobaan` sebelum pipeline jalan. Dokumen yang sudah 3 kali terputus ditandai `gagal`, supaya dokumen yang membuat backend crash tidak berputar terus.

Status dokumen: `diproses`, `menunggu_verifikasi`, `terverifikasi`, `ditolak`, `gagal`. Diagram lengkap ada di `docs/ARSITEKTUR.md`.

## 4. Pipeline AI

Titik masuknya `pipeline/main.py: process_document(file_path)`. Fungsi ini **tidak pernah melempar exception**: kalau gagal, hasilnya `status="gagal"` dengan pesan yang aman ditampilkan.

### 4.1 Ekstraksi teks (`extract.py`, `ocr.py`)

| Jenis berkas | Cara |
|---|---|
| PDF digital | PyMuPDF. Halaman dengan teks kurang dari `PDF_MIN_CHARS_PER_PAGE` (30) dianggap scan |
| PDF scan | Halaman dirender `OCR_DPI` (200), lalu PaddleOCR. Maksimal `OCR_MAX_PAGES` (5) halaman |
| Foto (JPG, PNG) | PaddleOCR, dengan koreksi orientasi dokumen |
| DOCX | python-docx, termasuk isi tabel |

Teks hasil di bawah 20 karakter dianggap tidak terbaca dan dokumen gagal dengan pesan untuk dosen. Model PaddleOCR diunduh saat pertama dipakai, lalu disimpan di cache folder home.

### 4.2 Klasifikasi dan skor keyakinan (`classify.py`)

1. Teks yang terlalu panjang dipotong: 2/3 awal dan 1/3 akhir dari `PIPELINE_MAX_CHARS` (12.000). Kop, judul, dan "MENETAPKAN" biasanya di awal; tanda tangan di akhir.
2. Prompt sistem (`prompts/klasifikasi_system.md`) berisi aturan ekstraksi, petunjuk membedakan jenis yang sering tertukar, dan daftar taksonomi.
3. LLM dipanggil `PIPELINE_VOTES` kali (3). Panggilan pertama suhu 0, sisanya suhu 0,4. Output dipaksa mengikuti JSON Schema lewat structured output Ollama, dan `jenis` dibatasi ke daftar taksonomi.
4. **LLM hanya memilih jenis.** Subkategori dan kategori diturunkan dari taksonomi, jadi tidak mungkin keluar dari daftar. Karena itu nama jenis wajib unik di seluruh taksonomi.
5. Skor = jumlah suara jenis pemenang dibagi jumlah panggilan. Dengan 3 panggilan, skor hanya bisa 0,33, 0,67, atau 1,00, jadi ambang 0,85 berarti **ketiga panggilan harus sepakat**.
6. Skor dibatasi turun pada kasus berisiko: jenis `Lainnya` (maksimal 0,5), teks di bawah 80 karakter (0,6), dan ada kalimat menyerupai perintah ke AI (0,5).
7. Metadata diambil dari panggilan pertama yang memilih jenis pemenang. Periode yang tidak menyebut tahun akademik (`2025/2026`) dikosongkan, karena LLM sering mengarang tahun dari tanggal dokumen.
8. Nomor dan tanggal dokumen hanya dipakai kalau benar-benar tertulis di teks (`saring_nomor`, `saring_tanggal`). Tanggal dikenali dalam bentuk angka (15-08-2026, 2026-08-15) dan nama bulan Indonesia atau Inggris. Kalau tidak ditemukan, field dikosongkan dan alasannya dicatat.

### 4.3 Pertahanan terhadap prompt injection

- Teks dibungkus tag `<dokumen>`, dan tag serupa di dalam teks dinetralkan.
- Prompt menegaskan isi dokumen adalah data, baik sebelum maupun sesudah dokumen.
- Baris yang cocok dengan pola `POLA_INJEKSI` disamarkan sebelum dikirim ke LLM, dan skornya dibatasi 0,5 sehingga dokumen pasti dicek dosen. Teks asli yang disimpan tidak berubah.
- Pola ini hanya menangkap kalimat yang dikenal, jadi bukan jaminan penuh. Pertahanan utamanya tetap: hasil AI hanya mengisi metadata, tidak pernah menjalankan aksi.

### 4.4 Hasil evaluasi terakhir

Model `gemma4:e4b`, 3 voting, ambang 0,85. Laporan lengkap ada di `pipeline/eval/hasil/` (tidak di-commit).

| Data uji | Hasil |
|---|---|
| 45 dokumen dummy berformat mirip asli, 21 November 2026 | Kategori 100%, jenis 97,8%, nomor dan tanggal 100%, periode 91,1%. Lolos otomatis 97,8%, dan semua yang lolos otomatis jenisnya benar. Rata-rata 51 detik per dokumen |
| 22 dokumen asli satu dosen | 0 gagal. Kategori 40,9% terhadap label folder dosen, 95,5% sampai 100% terhadap taksonomi. Selisihnya karena SK pembimbing TA dan berita acara sidang masuk PND di taksonomi, tetapi PNJ di folder dosen. Menunggu keputusan Admin CoE |

Dokumen asli belum punya label jenis dan tanggal, jadi akurasi jenis untuk data asli belum terukur.

Petunjuk jenis di prompt ditambahkan setelah melihat kesalahan pada 45 dokumen uji yang sama (sebelumnya jenis 86,7%), jadi angka 97,8% kemungkinan terlalu optimis untuk dokumen baru. Evaluasi berikutnya perlu set uji yang tidak dipakai saat menyetel prompt.

Diulang 23 November 2026 setelah `saring_nomor` dan `saring_tanggal` ditambahkan: hasil sama (nomor dan tanggal tetap 100%), jadi penyaring tidak membuang nilai yang benar. Periode naik ke 100% tanpa perubahan aturan periode, jadi anggap sebagai variasi. Catatan: `run_eval` tidak mengatur logging, sehingga catatan penyaring (level INFO) tidak tercetak. Tambahkan `logging.basicConfig(level=logging.INFO)` kalau ingin melihatnya.

## 5. Backend

### 5.1 Modul

| Berkas | Isi |
|---|---|
| `main.py` | Aplikasi FastAPI, CORS, `/health`, `/taxonomy`, `/admin/koreksi/export`, penanda proses terputus saat start |
| `config.py` | Semua pengaturan dari `.env` (pydantic-settings). Production menolak mode mock |
| `api/auth.py` | `POST /auth/login` (JWT), `GET /auth/me`, batas percobaan login per username (`PembatasLogin`) |
| `api/documents.py` | Unggah, daftar, detail, berkas, setujui, tolak, koreksi |
| `services/documents.py` | Aturan akses (`access_clause`, `accessible`, `owned`), serialisasi, penautan dosen |
| `services/pipeline.py` | Menjalankan pipeline dan menyimpan hasilnya |
| `services/storage.py` | Penyimpanan berkas dan pemeriksaan tanda tangan berkas |
| `services/taxonomy.py` | Memuat taksonomi dan memvalidasi klasifikasi |
| `integrations/mock.py`, `integrations/real.py` | Adapter pipeline |
| `kelola.py` | Perintah pengelola di terminal (lihat Panduan Admin) |
| `api/admin.py`, `services/admin.py` | Endpoint laman Admin. Logika akun dan dokumen ada di `services/admin.py`, dipakai bersama oleh `kelola.py` |
| `seed.py` | Akun dummy, hanya di development |

### 5.2 Database

Lima tabel (migrasi `0001_initial.py`):

| Tabel | Isi |
|---|---|
| `users` | Akun: username, nama, NIP (unik), hash password, peran `dosen` atau `admin` |
| `documents` | Berkas, hash SHA-256 (unik global), klasifikasi, metadata, skor, teks, status, tingkat akses |
| `dokumen_dosen` | Dosen yang disebut di dokumen. `user_id` terisi kalau NIP cocok dengan akun; `dikonfirmasi` setelah pengunggah menyetujui |
| `koreksi` | Snapshot sebelum dan sesudah setiap koreksi dosen. Bahan perbaikan AI |
| `audit_log` | Log aktivitas. Trigger PostgreSQL menolak UPDATE, DELETE, dan TRUNCATE |

Kolom `versi` dan `induk_versi` sudah ada di skema, tetapi belum dipakai kode.

### 5.3 Aturan akses

Aturan ada di satu tempat, `services/documents.py`:

- Pengunggah melihat dan mengubah dokumennya sendiri.
- Dosen tertaut hanya **melihat**, dan hanya setelah pengunggah menyetujui (`dikonfirmasi`), dan hanya kalau tingkat aksesnya bukan `rahasia`.
- Setujui, tolak, dan koreksi hanya untuk pengunggah (`owned`, selain itu 403).
- Admin tidak punya akses khusus ke isi dokumen. Lewat laman Admin, admin hanya melihat data ringkas (nama berkas, pengunggah, status, waktu) untuk dokumen gagal dan pencarian SK bersama.
- Dokumen yang tidak boleh dilihat dijawab 404, bukan 403, supaya keberadaannya tidak bocor.

Setiap endpoint dokumen baru wajib memakai `accessible()` atau `owned()`, bukan query sendiri.

### 5.4 Pengaturan penting

Semua ada di `config.py` dan `.env.example`. Yang paling sering diubah: `CONFIDENCE_THRESHOLD`, `PIPELINE_VOTES`, `OLLAMA_MODEL`, `PIPELINE_MODE`. Tabel lengkap ada di Panduan Instalasi Bagian 2.

## 6. Frontend

| Berkas | Isi |
|---|---|
| `app/login/page.tsx` | Laman masuk |
| `app/unggah/page.tsx` | Unggah banyak berkas, antrean, polling status tiap 2,5 detik |
| `app/verifikasi/page.tsx` | Kotak Verifikasi: pratinjau, setujui, tolak, koreksi |
| `app/arsip/page.tsx` | Arsip dengan filter kategori, status, tahun |
| `app/admin/page.tsx` | Laman Admin: akun, dokumen gagal, SK bersama, log aktivitas. Menu hanya muncul untuk peran admin |
| `components/` | Kerangka laman (`shell.tsx`), komponen dasar (`ui.tsx`), formulir koreksi (`correction.tsx`) |
| `lib/api.ts` | Semua panggilan API, token di `sessionStorage` |
| `lib/format.ts` | Format tanggal, status, dan label |

- Desain mengikuti skill `ai-dmc-apple-glass-ui`: latar abu flat, satu warna aksen, warna dan ukuran tombol dari Apple HIG, glass hanya untuk elemen kecil yang mengambang. Baca skill itu sebelum mengubah UI.
- Tampilan harus jalan di lebar 375 px (HP) dan 1280 px.
- `NEXT_PUBLIC_API_URL` ditanam saat build.
- Skrip pemeriksaan browser ada di `frontend/scripts/` dan membutuhkan backend yang berjalan.

## 7. Resep perubahan

### Menambah atau mengubah jenis dokumen

1. Ubah `pipeline/config/taxonomy.json`. Nama jenis wajib unik di seluruh taksonomi.
2. Kalau jenis baru mirip jenis lain, tambahkan petunjuk pembeda di bagian "PETUNJUK MEMBEDAKAN JENIS" pada prompt.
3. Tambahkan contoh dokumen dummy di `tools/generate_dummy_format_nyata.py` dan labelnya.
4. Jalankan tes pipeline dan evaluasi akurasi (Bagian 8). Bandingkan dengan laporan sebelumnya.
5. Dokumen lama tidak ikut berubah. Kalau perlu, buat skrip migrasi data terpisah.

### Mengubah prompt

1. Ubah `pipeline/prompts/klasifikasi_system.md`. Jangan hapus aturan nomor 1 (dokumen adalah data) dan aturan `null`.
2. Jalankan evaluasi dengan data dummy sebelum dan sesudah. Perubahan kecil bisa memperbaiki satu jenis tetapi merusak jenis lain.
3. Kalau memungkinkan, ulangi evaluasi pada dokumen asli.

### Menambah field metadata

Ini mengubah kontrak, jadi perlu persetujuan dulu (Bagian 1 aturan 5). Urutannya:

1. `docs/PEMBAGIAN_PERAN.md`.
2. Skema LLM di `pipeline/schemas.py` dan aturan di prompt.
3. Pengisian di `classify.py`.
4. Skema backend `schemas.py`.
5. Simpan di `metadata_lain` (tanpa migrasi), atau sebagai kolom baru (dengan migrasi).
6. Tampilan dan formulir koreksi di frontend.
7. Label evaluasi.

### Menambah migrasi database

```
cd backend
set PYTHONPATH=..
..\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "deskripsi singkat"
```

Periksa berkas yang dihasilkan di `alembic/versions/`, karena autogenerate tidak menangkap trigger dan beberapa perubahan tipe. Jalankan tes backend, yang memakai migrasi yang sama di SQLite. Lalu jalankan `alembic upgrade head` di PostgreSQL lokal. Migrasi berjalan otomatis saat backend start di server, jadi pastikan migrasi aman untuk data yang sudah ada.

### Menambah endpoint API

1. Tambahkan di `api/`. Pakai `current_user` untuk autentikasi dan `accessible()` atau `owned()` untuk dokumen.
2. Catat aksi penting di `audit_log`.
3. Tambahkan tes di `backend/tests/`, termasuk tes bahwa dosen lain tidak bisa mengakses.
4. Perbarui kontrak API di `docs/PEMBAGIAN_PERAN.md`.

### Menambah fitur pengelola

1. Tulis logikanya di `backend/app/services/admin.py`. Perubahan data wajib memanggil `catat()` untuk log audit, dengan `oleh` berisi nama pelaku.
2. Laman Admin: tambahkan endpoint di `api/admin.py` (lindungi dengan `admin_saja`) dan tampilannya di `frontend/app/admin/page.tsx`. Tes di `backend/tests/test_admin.py`, termasuk tes bahwa akun dosen mendapat 403.
3. Perintah terminal: tambahkan fungsi dan parser di `kelola.py` yang memanggil fungsi yang sama. Perintah yang mengubah data wajib memakai `oleh(sp)`. Tes di `backend/tests/test_kelola.py`.
4. Perbarui Panduan Admin dan kontrak di `docs/PEMBAGIAN_PERAN.md`.

### Mengganti model LLM

Ubah `OLLAMA_MODEL`, unduh dengan `ollama pull`, lalu jalankan evaluasi akurasi. Prompt disetel untuk `gemma4:e4b`; model lain bisa membutuhkan penyesuaian. Riwayat uji banding model ada di `docs/PIPELINE_INTEGRATION.md`.

## 8. Pengujian dan evaluasi

| Pemeriksaan | Perintah | Butuh |
|---|---|---|
| Tes backend (30 tes) | `cd backend`, lalu `PYTHONPATH=.. ../.venv/Scripts/python.exe -m pytest -q` | Tidak butuh PostgreSQL atau Ollama |
| Tes pipeline (53 tes) | `.venv/Scripts/python.exe -m pytest pipeline/tests -q` | Tidak butuh OCR atau Ollama |
| Tipe frontend | `cd frontend`, lalu `npm run typecheck` | |
| Build frontend | `npm run build` | Internet untuk Google Fonts |
| Coba satu dokumen | `uji-dokumen.cmd <berkas>` | Ollama, PaddleOCR |
| Evaluasi akurasi | `uji-dokumen.cmd --akurasi` | Ollama, PaddleOCR, `data/dummy/labels.csv` |

Catatan:

- Tes backend memakai SQLite. JSONB, row lock, dan trigger audit hanya teruji di PostgreSQL, jadi uji manual di PostgreSQL lokal sebelum rilis.
- Membuat data evaluasi: `python tools/generate_dummy_format_nyata.py` membuat dokumen dummy berformat mirip asli di `data/dummy_nyata/latih` dan `data/dummy_nyata/uji`, masing-masing dengan `labels.csv`. Evaluasi data uji itu dengan `python -m pipeline.eval.run_eval --data data/dummy_nyata/uji --labels data/dummy_nyata/uji/labels.csv`. Hasil 45 dokumen di Bagian 4.4 berasal dari data uji ini.
- Evaluasi mencatat akurasi per field, persen dokumen yang lolos ambang, dan akurasi di antara yang lolos. Angka terakhir paling penting: dokumen yang lolos otomatis tidak dicek dosen.
- Jangan memakai dokumen asli dosen sebagai contoh di prompt, tes, atau dokumen yang di-commit.

## 9. Pekerjaan yang belum selesai

Diurutkan dari yang paling berdampak. Sumber lain: `docs/TINDAK_LANJUT.md` dan Kebijakan Data Bagian 10.

**Sebelum dipakai prodi**

1. **Uji di server sungguhan:** systemd, OCR dengan GPU, HTTPS (Panduan Instalasi Bagian 9).
2. **Keputusan taksonomi:** SK pembimbing TA dan berita acara sidang masuk PND atau PNJ. Begitu diputuskan, ubah `taxonomy.json` atau label evaluasi, lalu ukur ulang.
3. **Batas login per alamat IP.** Batas sekarang per username, karena di belakang reverse proxy semua permintaan ber-IP sama. Akibatnya orang lain bisa mengunci akun dosen selama 15 menit dengan sengaja salah password. Perlu Caddy meneruskan IP asli dan backend memercayainya.
4. **Antrean di proses terpisah.** Antrean sudah permanen (dilanjutkan saat restart), tetapi masih berjalan di proses backend. Untuk beban besar, pindahkan ke worker terpisah.

**Fitur admin** (sekarang lewat perintah `kelola`)

5. Status akun aktif dan nonaktif (sekarang akun ditutup dengan password acak).
6. Laman Admin: tambah hapus dokumen, batalkan Ditolak, dan ubah nama atau NIP akun.
7. Hapus dokumen dan kebijakan retensi.
8. Membatalkan status Ditolak.
9. Mengubah tingkat akses dokumen dari UI.

Butir 5 dan 7 mengubah skema dan kontrak.

**Akurasi AI**

10. Aturan tanggal berita acara sudah ada di prompt, tetapi belum terbukti pada dokumen asli: teks sintetis dengan tanggal formulir di kop sudah benar dengan prompt lama maupun baru. Perlu contoh dokumen asli yang salah.
11. Penyaring nomor dan tanggal bisa mengosongkan nilai yang benar kalau OCR salah baca (misalnya huruf O dibaca angka 0). Pantau lewat koreksi dosen.
12. Contoh di prompt untuk jenis yang masih tertukar (surat tugas asesor, narasumber, reviewer).
13. Fine-tune (LoRA) ditunda sampai ada sekitar 100 dokumen asli berlabel. Bahannya dari tabel `koreksi`.

**Kecepatan**

14. OCR di GPU dan OCR hanya beberapa halaman awal (lihat `docs/TINDAK_LANJUT.md` Bagian 1).
15. Dokumen diproses satu per satu, jadi unggahan banyak dosen sekaligus mengantre. Kecepatan di server GPU 12 GB belum diukur.

**Keamanan**

16. Token di `sessionStorage` (lebih aman di cookie httpOnly).
17. Enkripsi berkas di `storage/`.
18. Sesi habis setelah 60 menit membuat isian koreksi hilang.

**Di luar MVP**, jangan dikerjakan tanpa permintaan: embedding dan pencarian semantik, Tanya Arsip, generator paket dokumen (BKD, akreditasi), dan SSO kampus.
