# Kebutuhan Server AI-DMC (1 prodi, sekitar 50 dosen)

Disusun 21 November 2026 dari kode di branch `feat/ai-asli-dan-perbaikan-ui`. Dokumen ini daftar persiapan sebelum deploy. Belum ada yang dibangun atau diuji di server.

## 1. Ringkasan

- Satu mesin menjalankan semuanya: frontend, backend, PostgreSQL, Ollama (LLM), dan PaddleOCR.
- Server diletakkan di kampus (on-premise). Dokumen dosen berisi data pribadi dan aturan proyek mewajibkan AI berjalan lokal.
- Untuk 50 dosen, cukup satu PC workstation dengan GPU NVIDIA 12 GB. Tidak perlu server rak.

## 2. Perangkat keras

| Komponen | Kebutuhan | Alasan |
|---|---|---|
| GPU | NVIDIA, VRAM minimal 12 GB (contoh RTX 3060 12 GB, RTX 4060 Ti 16 GB) | Model gemma4:e4b berukuran 6,6 GB. Di VRAM 6 GB model terbagi ke CPU dan lambat. Sisa VRAM dipakai PaddleOCR |
| CPU | 8 inti | OCR dan backend; jadi cadangan kalau OCR belum di GPU |
| RAM | 32 GB | PostgreSQL, backend + PaddleOCR, Ollama, Next.js |
| Penyimpanan utama | SSD 512 GB | Sistem, image Docker, model AI (sekitar 7 GB), database, berkas dokumen |
| Backup | Disk eksternal atau NAS terpisah, minimal 1 TB | Salinan database dan folder `storage/` |
| Listrik | UPS | Mati mendadak saat proses membuat dokumen berstatus gagal |

Perkiraan beban (bukan hasil ukur):

- Dokumen: 50 dosen x 300 dokumen = sekitar 15.000 berkas, sekitar 15 GB.
- Saat ramai (20 dosen x 20 dokumen = 400 dokumen): sekitar 3 jam di GPU 12 GB, berjalan di background.
- Unggah awal arsip lama (2.500 dokumen): sekitar 17 jam, bisa dicicil.

## 3. Perangkat lunak

| Perangkat lunak | Versi | Catatan |
|---|---|---|
| Ubuntu Server | 24.04 LTS | Atau 22.04 LTS |
| Driver NVIDIA | Sesuai GPU | Cek dengan `nvidia-smi` |
| Docker Engine + Docker Compose | Terbaru stabil | |
| NVIDIA Container Toolkit | Terbaru stabil | Supaya container bisa memakai GPU |
| Ollama | Terbaru stabil | Model `gemma4:e4b` diunduh sekali (6,6 GB) |
| Reverse proxy | Caddy atau Nginx | HTTPS dan satu pintu masuk |

Unduhan pertama butuh internet: image Docker, model Ollama, dan model PaddleOCR (sekitar 140 MB). Setelah itu aplikasi bisa berjalan tanpa internet.

## 4. Jaringan dan keamanan

- Akses dari jaringan kampus. Kalau perlu dari luar, lewat VPN kampus.
- IP tetap dan nama domain internal (contoh `ai-dmc.<domain-kampus>`), dengan sertifikat HTTPS.
- Hanya port 443 (dan 80 untuk redirect) yang terbuka. PostgreSQL (5432), backend (8000), frontend (3000), dan Ollama (11434) hanya bisa diakses dari mesin itu sendiri.
- Akses SSH hanya untuk admin, memakai kunci, bukan password.
- Folder `storage/` tidak boleh disajikan langsung oleh web server.

## 5. Yang perlu diminta ke CoE atau prodi

- [ ] Ada PC atau server dengan GPU NVIDIA 12 GB ke atas? Kalau belum, apakah bisa diadakan?
- [ ] Mesin boleh menyala terus dan tersambung ke jaringan kampus?
- [ ] IP tetap dan nama domain internal dari pengelola jaringan kampus.
- [ ] Sertifikat HTTPS: dari kampus, atau boleh dibuat sendiri.
- [ ] Siapa admin server (akses SSH) dan siapa penanggung jawab backup.
- [ ] Tempat backup (disk eksternal atau NAS) dan jadwalnya.
- [ ] Daftar 50 dosen (nama, NIP) untuk dibuatkan akun.
- [ ] Keputusan taksonomi: SK pembimbing TA dan berita acara sidang masuk Pendidikan (PND) atau Penunjang (PNJ).
- [ ] Logo resmi untuk tampilan aplikasi.

## 6. Kesiapan kode untuk deploy

Sudah ada:

- `docker-compose.yml` berisi PostgreSQL 17, backend, dan frontend. Port hanya dibuka ke `127.0.0.1`.
- `backend/Dockerfile` (Python 3.12, migrasi Alembic otomatis saat start, 1 worker) dan `frontend/Dockerfile` (Next.js standalone).
- Backend menolak `APP_ENVIRONMENT=production` kalau pipeline masih mode mock.

Belum ada atau belum diuji (wajib sebelum deploy):

1. **PaddleOCR belum masuk image backend.** `backend/requirements-pipeline.lock` tidak memuat `paddlepaddle` dan `paddleocr`, jadi dokumen scan dan foto akan gagal di container. Perlu ditambah, idealnya versi GPU dengan base image CUDA.
2. **Cache model PaddleOCR belum disimpan di volume.** Tanpa volume, model diunduh ulang setiap container dibuat ulang.
3. **Ollama belum ada di Compose.** Sekarang backend memanggil Ollama di host lewat `host.docker.internal`. Pilih: pasang Ollama di host, atau tambahkan service `ollama` dengan akses GPU.
4. **`OLLAMA_HOST` harus berupa URL lengkap** (contoh `http://host.docker.internal:11434`). Nilai seperti `0.0.0.0:11434` membuat pipeline gagal menghubungi Ollama.
5. **Belum ada reverse proxy dan HTTPS** di Compose.
6. **Belum ada skrip backup** untuk database (`pg_dump`) dan folder `storage/`.
7. **Image belum pernah dibangun dan dijalankan di server** (tugas P2-19 dan B-08).
8. **Antrean belum permanen.** Backend memakai 1 worker dan background task. Restart server saat ada dokumen diproses membuat dokumen itu berstatus gagal.

## 7. Urutan deploy

1. Pasang Ubuntu, driver NVIDIA, Docker, NVIDIA Container Toolkit. Cek `nvidia-smi` dan `docker run --gpus all ... nvidia-smi`.
2. Pasang Ollama, jalankan `ollama pull gemma4:e4b`, cek modelnya muat penuh di GPU (`ollama ps`).
3. Ambil kode dari repo, salin `.env.example` menjadi `.env`, isi rahasia baru: `POSTGRES_PASSWORD`, `JWT_SECRET`, `SEED_PASSWORD`. Atur `APP_ENVIRONMENT=production`, `PIPELINE_MODE=real`, `OLLAMA_HOST`, `CORS_ORIGINS` dan `NEXT_PUBLIC_API_URL` sesuai domain.
4. Bereskan poin 1 sampai 5 di Bagian 6.
5. `docker compose up -d --build`, lalu cek migrasi berhasil dan `/health` menjawab.
6. Uji 10 dokumen sintetis campuran (digital, scan, foto, DOCX) sebelum memakai data asli.
7. Buat akun 50 dosen, nonaktifkan akun dummy.
8. Pasang backup harian dan coba pulihkan sekali.
9. Uji coba dengan beberapa dosen dulu, baru dibuka untuk semua.

## 8. Setelah berjalan

- Backup harian: `pg_dump` database dan salinan `storage/`. Simpan minimal 7 hari terakhir.
- Pantau ruang disk, dokumen berstatus gagal, dan waktu proses per dokumen.
- Sebelum restart atau update, pastikan tidak ada dokumen berstatus "diproses".
