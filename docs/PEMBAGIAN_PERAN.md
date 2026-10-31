# Pembagian Peran Tim AI-DMC (MVP)

> Dokumen ini jadi acuan kerja tim selama magang di CoE AIIS (s.d. 20 November 2026).
> Kalau ada perubahan kesepakatan, update file ini lewat Pull Request supaya tercatat.

| Info | Isi |
|---|---|
| Proyek | AI-DMC (AI Document Management Center) CoE AIIS |
| Acuan | DOK-CoE-AIIS-DMC-001 v0.1 (Rancangan Sistem AI-DMC) |
| Target MVP | Aplikasi upload + klasifikasi AI + verifikasi dosen |
| Orang 1 | `[nama]`, AI Pipeline Engineer |
| Orang 2 | `[nama]`, Application Engineer (Frontend + API + Database) |

---

## 1. Ruang Lingkup MVP

### Masuk MVP
1. Login sederhana (username + password).
2. Upload banyak berkas sekaligus (PDF, DOCX, JPG/PNG).
3. Cek duplikat persis lewat hash SHA-256.
4. Pipeline AI: ekstraksi teks / OCR → klasifikasi → ekstraksi metadata.
5. Skor keyakinan ≥ 0,85 langsung masuk arsip, sisanya ke Kotak Verifikasi.
6. Kotak Verifikasi: Setujui, Koreksi, Tolak.
7. Laman Arsip Saya: daftar dokumen per kategori, filter status.
8. Koreksi dosen disimpan (nanti jadi contoh few-shot / data latih).

### Tidak masuk MVP (fase berikutnya)
1. SSO kampus.
2. Embedding, pencarian bahasa alami (Tanya Arsip).
3. Generator paket jafung / akreditasi, ekspor ZIP.
4. Dasbor Ketua CoE.
5. Deteksi versi dokumen (SK revisi).
6. Celery + Redis (MVP pakai background task FastAPI).

---

## 2. Tech Stack MVP

| Bagian | Teknologi |
|---|---|
| Frontend | Next.js |
| API | FastAPI (Python) |
| Database | PostgreSQL |
| Penyimpanan berkas | Folder lokal `storage/` (MinIO menyusul) |
| Ekstraksi teks | PyMuPDF (PDF digital), python-docx (DOCX) |
| OCR | PaddleOCR PP-OCRv6 (scan / foto) |
| LLM lokal | Ollama, model awal Gemma 4 E4B atau Qwen3 8B (bisa diganti lewat config) |
| Deploy | Docker Compose |

---

## 3. Pembagian Peran

### Orang 1: AI Pipeline Engineer

**Tanggung jawab utama:** semua yang terjadi dari "berkas masuk" sampai "keluar JSON hasil AI".

1. **Ekstraksi teks**
   - Deteksi jenis berkas: PDF digital, PDF scan, DOCX, gambar.
   - PDF digital dan DOCX diekstrak langsung, tanpa OCR.
   - PDF scan dan gambar masuk OCR.
2. **OCR**
   - Setup PaddleOCR, uji di dokumen bahasa Indonesia.
   - Pre-processing ringan kalau perlu (rotasi, grayscale).
3. **Klasifikasi dan ekstraksi metadata (LLM)**
   - Tulis taksonomi di `pipeline/config/taxonomy.json`.
   - Susun prompt klasifikasi + ekstraksi metadata, output wajib JSON valid.
   - Tangani output LLM yang rusak (retry, validasi skema).
4. **Skor keyakinan**
   - Tentukan metode yang masuk akal (misalnya voting 3x / self-consistency, atau logprobs kalau tersedia).
   - Dokumentasikan metodenya di `pipeline/README.md`.
5. **Evaluasi**
   - Kumpulkan dataset uji dummy, lalu data asli dari CoE.
   - Script evaluasi: akurasi kategori, akurasi jenis, akurasi field metadata.
   - Uji banding 2 sampai 3 model LLM.
6. **Setup Ollama di server** (bareng Orang 2 saat deploy).

**Deliverable:** fungsi Python `process_document(file_path) -> dict` sesuai kontrak di Bagian 4.1.

### Orang 2: Application Engineer

**Tanggung jawab utama:** semua yang dilihat dan dipakai dosen, plus penyimpanan datanya.

1. **Database**
   - Skema tabel sesuai Bagian 4.3, migrasi pakai Alembic.
2. **API (FastAPI)**
   - Endpoint sesuai Bagian 4.2.
   - Simpan berkas ke `storage/`, hitung hash, tolak duplikat.
   - Panggil `process_document()` sebagai background task, simpan hasilnya.
   - Terapkan aturan ambang 0,85.
   - Login sederhana + kontrol akses (dosen cuma lihat dokumen miliknya).
3. **Frontend (Next.js)**
   - Laman Login.
   - Laman Unggah: drag and drop, status proses per berkas.
   - Laman Kotak Verifikasi: pratinjau, hasil AI, tombol Setujui / Koreksi / Tolak.
   - Laman Arsip Saya: per kategori, filter status.
   - Responsif di HP, gaya Apple light + glass.
   - **Wajib ikut panduan desain:** `.agents/skills/ai-dmc-apple-glass-ui/SKILL.md`.
4. **Simpan koreksi dosen** ke tabel `koreksi` (dipakai Orang 1 untuk perbaikan model).

**Deliverable:** aplikasi web yang bisa dipakai end-to-end.

### Tugas Bersama
1. Setup repo, Docker Compose, `.env.example`.
2. Integrasi pipeline ke API (Minggu 2).
3. Deploy ke server CoE.
4. Laporan mingguan ke pembimbing.
5. Demo dan laporan akhir.

### Mock dulu, biar bisa kerja paralel
- Sebelum pipeline asli jadi, Orang 1 menyediakan `pipeline/mock.py` berisi `process_document()` palsu yang mengembalikan JSON contoh sesuai kontrak.
- Orang 2 membangun aplikasi pakai mock ini. Saat pipeline asli siap, cukup ganti import.

---

## 4. Kontrak Antarmuka (Wajib Dipatuhi Dua-duanya)

> Perubahan kontrak **harus** disepakati berdua dan diupdate di file ini dulu, baru diubah di kode.

### 4.1 Output `process_document()`

```json
{
  "status": "sukses",
  "jenis_berkas": "pdf_digital",
  "teks": "KEPUTUSAN DEKAN FAKULTAS ... (teks lengkap hasil ekstraksi)",
  "klasifikasi": {
    "kategori": "PND",
    "subkategori": "SK mengajar dan beban kerja",
    "jenis": "SK mengajar"
  },
  "skor_keyakinan": 0.91,
  "metadata": {
    "judul": "SK Penugasan Mengajar Semester Ganjil 2026/2027",
    "nomor_dokumen": "123/AKD/FIF/2026",
    "tanggal_terbit": "2026-08-15",
    "periode": "Ganjil 2026/2027",
    "dosen_terkait": [
      { "nama": "Nama Dosen", "nip": null, "peran": "Pengajar" }
    ],
    "mitra_penerbit": null,
    "sumber_dana": null,
    "identifier": null
  },
  "ringkasan": "SK penugasan mengajar untuk semester ganjil 2026/2027.",
  "model_dipakai": "gemma4:e4b",
  "waktu_proses_detik": 12.4,
  "error": null
}
```

Aturan:
1. `status`: `sukses` atau `gagal`. Kalau `gagal`, isi `error` dengan pesan singkat yang aman ditampilkan ke dosen, `klasifikasi` berisi `null` di ketiga field, `skor_keyakinan` 0, dan `metadata` berisi `null` / list kosong.
2. `jenis_berkas`: `pdf_digital`, `pdf_scan`, `docx`, `gambar`.
3. `kategori`: salah satu `PND`, `PNL`, `PKM`, `PUB`, `PNJ`, `ADM`, atau `LAINNYA` kalau tidak cocok.
4. `skor_keyakinan`: angka 0 sampai 1.
5. Field metadata yang tidak ditemukan diisi `null`, **jangan dikarang**.
6. Tanggal format `YYYY-MM-DD`.
7. Pipeline hanya meminta LLM memilih `jenis`. `kategori` dan `subkategori` diturunkan dari `pipeline/config/taxonomy.json`, jadi nama jenis wajib unik di seluruh taksonomi.

### 4.2 Endpoint API

| Method | Endpoint | Fungsi |
|---|---|---|
| POST | `/auth/login` | Login, balikan token |
| GET | `/taxonomy` | Daftar kategori, subkategori, jenis (untuk dropdown koreksi) |
| POST | `/documents` | Upload satu atau banyak berkas |
| GET | `/documents?status=&kategori=` | Daftar dokumen milik user |
| GET | `/documents/{id}` | Detail dokumen + hasil AI |
| GET | `/documents/{id}/file` | Unduh / pratinjau berkas asli |
| POST | `/documents/{id}/approve` | Setujui hasil AI |
| PATCH | `/documents/{id}` | Koreksi klasifikasi / metadata |
| POST | `/documents/{id}/reject` | Tolak dokumen |

Status dokumen: `diproses` → `menunggu_verifikasi` / `terverifikasi` → (`ditolak`). Plus `gagal` kalau pipeline error.

### 4.3 Skema Database

Skema ini mengikuti Bagian 6 dokumen rancangan (DOK-CoE-AIIS-DMC-001), ditambah kolom teknis yang dibutuhkan aplikasi. Field yang ditunda tetap disiapkan strukturnya supaya nanti tidak perlu merombak database.

**users**
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID | |
| nama | TEXT | |
| nip | TEXT | unik, boleh kosong |
| username | TEXT | unik |
| password_hash | TEXT | |
| peran | TEXT | `dosen` / `admin` |
| created_at | TIMESTAMPTZ | |

**documents**
| Kolom | Tipe | Diisi oleh | Keterangan |
|---|---|---|---|
| id | UUID | Sistem | = `doc_id` di rancangan |
| owner_id | UUID → users | Sistem | yang mengunggah |
| nama_berkas | TEXT | Sistem | nama asli berkas |
| path_berkas | TEXT | Sistem | lokasi di `storage/` |
| hash_sha256 | TEXT | Sistem | unik, deteksi duplikat |
| jenis_berkas | TEXT | AI | `pdf_digital` / `pdf_scan` / `docx` / `gambar` |
| kategori | TEXT | AI | kode taksonomi |
| subkategori | TEXT | AI | |
| jenis | TEXT | AI | |
| judul | TEXT | AI | |
| nomor_dokumen | TEXT | AI (OCR) | |
| tanggal_terbit | DATE | AI | |
| periode | TEXT | AI | contoh `Ganjil 2026/2027` |
| metadata_lain | JSONB | AI | `mitra_penerbit`, `sumber_dana`, `identifier` |
| skor_keyakinan | NUMERIC(3,2) | AI | 0 s.d. 1 |
| ringkasan | TEXT | AI | |
| teks | TEXT | AI | teks hasil ekstraksi / OCR |
| model_dipakai | TEXT | Sistem | |
| status | TEXT | Sistem / dosen | `diproses`, `menunggu_verifikasi`, `terverifikasi`, `ditolak`, `gagal` |
| tingkat_akses | TEXT | Sistem | `publik_coe` / `pribadi` / `rahasia`, default `pribadi` |
| versi | INT | Sistem | default 1 (fitur versi ditunda) |
| induk_versi | UUID → documents | Sistem | boleh kosong (fitur versi ditunda) |
| created_at, updated_at | TIMESTAMPTZ | Sistem | |

**dokumen_dosen** (= `dosen_terkait` di rancangan: satu dokumen bisa ditautkan ke banyak dosen)
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | UUID | |
| document_id | UUID → documents | |
| user_id | UUID → users | boleh kosong kalau dosen belum punya akun |
| nama | TEXT | nama sesuai dokumen |
| nip | TEXT | boleh kosong |
| peran | TEXT | contoh `Ketua`, `Anggota`, `Pengajar` |
| dikonfirmasi | BOOLEAN | default false, true setelah dosen menyetujui |

**koreksi**: `id`, `document_id`, `user_id`, `sebelum` (JSONB), `sesudah` (JSONB), `created_at`

**audit_log**: `id`, `user_id`, `aksi` (`upload` / `approve` / `koreksi` / `reject` / `unduh` / `login`), `document_id` (boleh kosong), `detail` (JSONB), `created_at`. Tabel ini **hanya boleh INSERT**, tidak ada UPDATE atau DELETE.

**Ditunda ke fase 2** (tabel terpisah, tidak mengubah tabel di atas): `label_jafung`, `label_akreditasi`, `embedding`.

**Pemetaan dari output pipeline (4.1) ke database:**
1. `metadata.judul`, `nomor_dokumen`, `tanggal_terbit`, `periode` → kolom dengan nama yang sama.
2. `metadata.mitra_penerbit`, `sumber_dana`, `identifier` → `metadata_lain`.
3. `metadata.dosen_terkait[]` → satu baris per dosen di `dokumen_dosen`. Pengunggah otomatis ditautkan juga.

---

## 5. Struktur Repo

```
ai-dmc/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── AGENTS.md                   ← instruksi untuk Codex / AI agent
├── .agents/
│   └── skills/
│       └── ai-dmc-apple-glass-ui/
│           └── SKILL.md        ← panduan desain UI (dibaca Codex)
├── .claude/
│   └── skills/
│       └── ai-dmc-apple-glass-ui/
│           └── SKILL.md        ← salinan yang sama (dibaca Claude Code)
├── docs/
│   ├── PEMBAGIAN_PERAN.md      ← file ini
│   ├── RINCIAN_TUGAS.md        ← daftar tugas per orang
│   └── laporan-mingguan/       ← laporan per minggu
├── pipeline/                   ← Orang 1
│   ├── README.md
│   ├── config/taxonomy.json
│   ├── extract.py
│   ├── ocr.py
│   ├── classify.py
│   ├── prompts/
│   ├── mock.py
│   ├── main.py                 ← process_document()
│   └── eval/
├── backend/                    ← Orang 2
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   └── alembic/
├── frontend/                   ← Orang 2
└── data/                       ← DI-IGNORE, jangan di-commit
```

**Penting soal data:** dokumen dosen berisi data pribadi (NIP, KTP, ijazah). Folder `data/` dan `storage/` wajib masuk `.gitignore`. Jangan pernah commit dokumen asli ke GitHub, termasuk di repo private.

---

## 6. Aturan Kerja di GitHub

### Branch
1. `main`: versi stabil, hanya lewat Pull Request.
2. `dev`: tempat integrasi harian.
3. Branch fitur: `feat/<fitur>`, misalnya `feat/ocr-paddle`, `feat/halaman-verifikasi`.
4. Perbaikan bug: `fix/<masalah>`.

### Commit
Format: `<tipe>: <deskripsi singkat>`
- `feat: tambah ekstraksi teks dari DOCX`
- `fix: tanggal kosong bikin pipeline error`
- `docs: update kontrak output pipeline`
- `chore: setup docker compose`

### Pull Request
1. PR ke `dev`, minimal di-review partner sebelum merge.
2. Deskripsi PR: apa yang diubah, cara ngetes, screenshot kalau ada UI.
3. Perubahan kontrak (Bagian 4) wajib di-approve dua-duanya.

### Issues dan Board
1. Setiap tugas dibuat jadi Issue, assign ke pemiliknya.
2. Pakai GitHub Projects dengan kolom: `To Do`, `In Progress`, `Review`, `Done`.
3. Label: `pipeline`, `backend`, `frontend`, `bug`, `diskusi`.

---

## 7. Timeline

### Minggu 0 (31 Okt s.d. 1 Nov)
| Siapa | Tugas |
|---|---|
| Bersama | Setup repo, isi nama di dokumen ini, kirim pesan ke pembimbing (data, server, konfirmasi scope) |

### Minggu 1 (2 s.d. 6 Nov): Buktikan AI-nya jalan
| Orang 1 | Orang 2 |
|---|---|
| `mock.py` jadi di hari pertama | Wireframe 3 laman inti |
| Kumpulkan 15 sampai 20 dokumen dummy | Skema database + migrasi |
| `taxonomy.json` | Setup FastAPI + endpoint upload, cek hash |
| Ekstraksi teks + OCR jalan | Setup Next.js + laman Login dan Unggah |
| Prototype klasifikasi dengan LLM | Endpoint daftar dan detail dokumen |
| Evaluasi awal di data dummy | |

### Minggu 2 (9 s.d. 13 Nov): Sambungkan jadi aplikasi
| Orang 1 | Orang 2 |
|---|---|
| Metode skor keyakinan | Laman Kotak Verifikasi + Arsip Saya |
| Perbaiki prompt dari hasil evaluasi | Endpoint approve, koreksi, reject |
| Uji di data asli dari CoE | Background task + aturan ambang 0,85 |
| **Bersama:** ganti mock dengan pipeline asli, tes end-to-end | |

### Minggu 3 (16 s.d. 20 Nov): Uji, rapikan, serahkan
| Orang 1 | Orang 2 |
|---|---|
| Uji banding model, pilih model final | Rapikan UI, responsif HP |
| Laporan akurasi | Audit log |
| **Bersama:** deploy ke server CoE, uji coba dengan dosen, laporan akhir, demo | |

---

## 8. Komunikasi

1. Sync singkat tiap hari (chat atau call 10 sampai 15 menit): kemarin ngapain, hari ini ngapain, ada hambatan apa.
2. Laporan mingguan ke pembimbing, hari: `[isi setelah konfirmasi]`. Template di `docs/laporan-mingguan/`.
3. Diskusi teknis yang penting dicatat di Issue berlabel `diskusi`, bukan cuma di chat, supaya tidak hilang.
4. Kalau ragu soal batas tugas: cek Bagian 3. Kalau tidak tercantum, diskusikan dulu, lalu tambahkan ke dokumen ini.

---

## 9. Definition of Done

Sebuah tugas dianggap selesai kalau:
1. Kode sudah di-merge ke `dev` lewat PR yang di-review.
2. Sudah dites minimal secara manual, cara ngetesnya ditulis di PR.
3. Tidak ada data pribadi atau dokumen asli yang ikut ter-commit.
4. Kalau mengubah kontrak atau alur, dokumen ini sudah diupdate.

---

## 10. Pertanyaan Terbuka (Konfirmasi ke Pembimbing)

1. Data contoh dokumen: kapan dan berapa banyak?
2. Pendekatan LLM + prompt dulu (training menyusul) disetujui?
3. Server GPU yang dipakai yang mana, cara aksesnya, dan spesifikasinya?
4. Kategori prioritas: eviden BKD pengajaran dulu?
5. Hari laporan mingguan?
6. Standar integrasi ke website AIIS nanti?
