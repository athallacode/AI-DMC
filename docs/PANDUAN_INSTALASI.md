# Panduan Instalasi dan Operasional AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Versi uji coba, November 2026

Panduan ini untuk pengembang dan pengelola server. Isinya cara memasang, menjalankan, memperbarui, mencadangkan, dan memulihkan AI-DMC.

Ada dua jalur instalasi dengan tingkat kesiapan yang berbeda:

| Jalur | Untuk | Status |
|---|---|---|
| Bagian 3: laptop pengembang (Windows) | Pengembangan, demo, evaluasi akurasi | **Sudah dipakai dan teruji** |
| Bagian 4: server (Ubuntu + Docker) | Pemakaian 1 prodi | **Belum pernah dijalankan.** Beberapa langkah menunggu perbaikan kode (Bagian 9) |

Langkah yang belum teruji ditandai **(belum diuji)**. Jangan memakai data dosen asli di server sebelum Bagian 4 langkah 9 selesai.

## 1. Gambaran komponen

| Komponen | Isi | Port (hanya di mesin itu) |
|---|---|---|
| Frontend | Next.js 15, tampilan untuk dosen | 3000 |
| Backend | FastAPI (Python 3.12), API, antrean proses, pipeline AI | 8000 |
| Pipeline AI | PyMuPDF dan python-docx (teks), PaddleOCR (scan dan foto), dijalankan di dalam backend | - |
| Ollama | LLM lokal `gemma4:e4b` untuk klasifikasi dan metadata | 11434 |
| PostgreSQL 17 | Akun, metadata dokumen, riwayat koreksi, log audit | 5432 |
| Folder `storage/` | Berkas asli dokumen dosen | - |

Alur singkat: dosen mengunggah lewat frontend, backend menyimpan berkas ke `storage/` dan mencatatnya di database, lalu pipeline membaca teks, memanggil Ollama tiga kali (voting), dan menyimpan hasilnya. Dokumen yang ketiga suaranya sepakat (skor 1,00, ambang 0,85) langsung masuk arsip; sisanya masuk Kotak Verifikasi dosen.

Rincian arsitektur ada di dokumen Arsitektur AI-DMC.

## 2. Berkas konfigurasi `.env`

Semua komponen membaca `.env` di akar repo. Salin dari `.env.example`, lalu isi. **`.env` tidak boleh di-commit** dan hanya boleh dibaca admin server.

| Variabel | Laptop pengembang | Server |
|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER` | `ai_dmc` | `ai_dmc` |
| `POSTGRES_PASSWORD` | Bebas | **Acak, minimal 24 karakter** |
| `DATABASE_URL` | `postgresql+psycopg://ai_dmc:<password>@127.0.0.1:5432/ai_dmc` | `postgresql+psycopg://ai_dmc:<password>@db:5432/ai_dmc` |
| `JWT_SECRET` | Acak, minimal 32 karakter | **Acak baru, minimal 32 karakter** |
| `JWT_EXPIRE_MINUTES` | 60 | 60 |
| `APP_ENVIRONMENT` | `development` | `production` |
| `PIPELINE_MODE` | `real` (atau `mock` untuk UI saja) | `real` (production menolak `mock`) |
| `PIPELINE_IMPORT` | `app.integrations.real:process_document` | sama |
| `STORAGE_DIR` | `../storage` | `/app/storage` |
| `TAXONOMY_PATH` | `../pipeline/config/taxonomy.json` | `/app/pipeline/config/taxonomy.json` |
| `OLLAMA_HOST` | `http://localhost:11434` | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | `gemma4:e4b` | `gemma4:e4b` |
| `OLLAMA_TIMEOUT` | 180 | 180 |
| `PIPELINE_VOTES` | 3 | 3 |
| `CONFIDENCE_THRESHOLD` | 0.85 | 0.85 |
| `CORS_ORIGINS` | `http://localhost:3000` | `https://<domain-aplikasi>` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | `https://<domain-aplikasi>/api` |
| `SEED_PASSWORD` | Minimal 12 karakter | Kosongkan (seed ditolak di production) |

Cara membuat nilai acak:

```
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Catatan:

- `OLLAMA_HOST` harus URL lengkap dengan `http://`. Nilai seperti `0.0.0.0:11434` (alamat bind server Ollama) membuat pipeline gagal menghubungi Ollama.
- Variabel sistem mengalahkan `.env`. Kalau di Windows ada variabel sistem `OLLAMA_HOST`, skrip `run-local.ps1` dan `uji-dokumen.cmd` sudah menimpanya dengan nilai dari `.env`.
- `NEXT_PUBLIC_API_URL` ditanam saat frontend dibangun. Kalau nilainya berubah, frontend harus dibangun ulang.
- Mengubah `JWT_SECRET` membuat semua dosen harus masuk ulang.

## 3. Instalasi di laptop pengembang (Windows)

Teruji di Windows 11 dengan Python 3.12, Node.js 24, Docker Desktop, Ollama 0.40, PaddlePaddle 3.3.1, dan PaddleOCR 3.7.0.

### Kebutuhan

- Docker Desktop (untuk PostgreSQL saja)
- Python 3.12
- Node.js 22 atau lebih baru
- Ollama dari ollama.com
- GPU NVIDIA disarankan. Tanpa GPU tetap jalan, tetapi satu dokumen bisa makan beberapa menit.

### Langkah

1. Ambil kode dan siapkan `.env` sesuai kolom "Laptop pengembang" di Bagian 2.

   ```
   git clone <alamat-repo> AI-DMC
   cd AI-DMC
   copy .env.example .env
   ```

2. Jalankan database:

   ```
   docker compose up -d db
   ```

3. Buat virtual environment di akar repo dan pasang dependensi backend, pipeline, dan OCR:

   ```
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r backend\requirements.lock -r backend\requirements-pipeline.lock
   .venv\Scripts\python.exe -m pip install paddlepaddle==3.3.1 paddleocr==3.7.0 pytest
   ```

4. Unduh model LLM (sekali, sekitar 6,6 GB):

   ```
   ollama pull gemma4:e4b
   ```

5. Jalankan backend. Skrip ini menjalankan migrasi, membuat akun dummy (`dosen1`, `dosen2`, `admin` dengan password `SEED_PASSWORD`), lalu menyalakan API di `http://127.0.0.1:8000`:

   ```
   powershell -ExecutionPolicy Bypass -File backend\run-local.ps1
   ```

   Saat dokumen scan pertama diproses, PaddleOCR mengunduh modelnya (sekitar 140 MB).

6. Di terminal lain, jalankan frontend lalu buka `http://localhost:3000`:

   ```
   cd frontend
   npm ci
   npm run dev
   ```

Pengguna Claude Code bisa memakai konfigurasi `.claude/launch.json` (nama `backend` dan `frontend`) sebagai ganti langkah 5 dan 6.

### Mencoba pipeline tanpa aplikasi

```
uji-dokumen.cmd data\dummy\sk_penguji.pdf
uji-dokumen.cmd --akurasi
```

Perintah kedua menjalankan evaluasi akurasi terhadap `data\dummy\labels.csv`. Laporannya ada di `pipeline\eval\hasil\`.

### Menjalankan tes

```
cd backend
set PYTHONPATH=..
..\.venv\Scripts\python.exe -m pytest -q
cd ..
.venv\Scripts\python.exe -m pytest pipeline\tests -q
cd frontend
npm run typecheck
```

Tes backend dan pipeline memakai SQLite, OCR palsu, dan LLM palsu, jadi tidak butuh Ollama atau PostgreSQL.

## 4. Instalasi di server (Ubuntu + Docker)

Kebutuhan perangkat keras dan daftar yang perlu diminta ke CoE ada di dokumen Kebutuhan Server. Ringkasnya: satu PC dengan GPU NVIDIA 12 GB, RAM 32 GB, SSD 512 GB, UPS, dan disk cadangan terpisah.

**Seluruh bagian ini belum diuji.** Langkah 4 dan 6 menunggu perbaikan kode di Bagian 9.

### Langkah

1. Pasang Ubuntu Server 24.04 LTS, driver NVIDIA, Docker Engine dengan Compose, dan NVIDIA Container Toolkit. Periksa:

   ```
   nvidia-smi
   docker run --rm --gpus all ubuntu nvidia-smi
   ```

2. Pasang Ollama di host, unduh model, dan pastikan model termuat penuh di GPU:

   ```
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull gemma4:e4b
   ollama run gemma4:e4b "tes" && ollama ps
   ```

   Kolom PROCESSOR di `ollama ps` harus `100% GPU`. Ollama harus bisa dihubungi dari container: atur `OLLAMA_HOST=0.0.0.0:11434` pada service Ollama di host (`systemctl edit ollama`), lalu tutup port 11434 dari luar dengan firewall.

3. Ambil kode dan siapkan `.env` sesuai kolom "Server" di Bagian 2:

   ```
   sudo mkdir -p /opt/ai-dmc && sudo chown $USER /opt/ai-dmc
   git clone <alamat-repo> /opt/ai-dmc
   cd /opt/ai-dmc
   cp .env.example .env && chmod 600 .env
   nano .env
   ```

4. **(belum diuji, menunggu Bagian 9 poin 1 dan 2)** Pastikan image backend sudah memuat PaddleOCR dan cache modelnya disimpan di volume.

5. Bangun dan jalankan:

   ```
   docker compose up -d --build
   docker compose ps
   docker compose logs backend | tail -20
   curl http://127.0.0.1:8000/health
   ```

   `/health` harus menjawab `"status":"ok"` dan `"pipeline_mode":"real"`. Migrasi database berjalan otomatis setiap backend start.

6. **(belum diuji, menunggu Bagian 9 poin 3)** Pasang reverse proxy HTTPS. Usulan dengan Caddy, satu domain untuk frontend dan backend:

   ```
   ai-dmc.<domain-kampus> {
       handle_path /api/* {
           reverse_proxy 127.0.0.1:8000
       }
       reverse_proxy 127.0.0.1:3000
       request_body {
           max_size 420MB
       }
   }
   ```

   Batas 420 MB menampung 20 berkas x 20 MB per unggahan. Folder `storage/` jangan pernah disajikan langsung oleh proxy.

7. Buat akun admin pertama. Seed akun dummy ditolak di production, jadi pakai perintah pengelola (lihat Panduan Admin):

   ```
   docker compose exec backend python -m app.kelola akun buat --username <admin> --nama "<Nama Admin CoE>" --peran admin --oleh "<Nama Pengelola>"
   ```

8. Pasang cadangan harian (Bagian 6) dan coba pulihkan sekali ke database kosong.
9. Uji 10 dokumen sintetis campuran (PDF digital, PDF scan, foto, DOCX) dari `tools/generate_dummy_format_nyata.py`. Periksa semuanya selesai tanpa status gagal dan waktunya wajar.
10. Buat akun dosen dari CSV (Panduan Admin Bagian 2), uji coba dengan beberapa dosen, baru dibuka untuk semua.

## 5. Operasional sehari-hari

Semua perintah dijalankan dari `/opt/ai-dmc`.

| Keperluan | Perintah |
|---|---|
| Status semua layanan | `docker compose ps` |
| Log backend terbaru | `docker compose logs --tail 100 backend` |
| Log backend terus-menerus | `docker compose logs -f backend` |
| Kesehatan API | `curl http://127.0.0.1:8000/health` |
| Model di GPU | `ollama ps` |
| Pemakaian GPU | `nvidia-smi` |
| Ruang disk | `df -h` dan `du -sh storage` |
| Dokumen gagal | `docker compose exec backend python -m app.kelola dokumen gagal` |

### Menghentikan dan menyalakan

1. Pastikan tidak ada dokumen yang sedang diproses. Dokumen yang terputus saat restart berubah menjadi gagal.

   ```
   docker compose exec db psql -U ai_dmc -d ai_dmc -c "SELECT count(*) FROM documents WHERE status = 'diproses'"
   ```

2. Kalau hasilnya 0:

   ```
   docker compose down
   docker compose up -d
   ```

   `docker compose down` tidak menghapus database dan berkas. **Jangan pakai `docker compose down -v`**, karena `-v` menghapus volume database.

Kalau ada dokumen yang terlanjur gagal karena restart, proses ulang dengan `kelola dokumen proses-ulang` (Panduan Admin Bagian 3).

### Memperbarui aplikasi

1. Cadangkan dulu (Bagian 6).
2. Pastikan tidak ada dokumen diproses (lihat di atas). Lakukan di luar jam kerja.
3. Ambil versi baru, bangun ulang, dan periksa:

   ```
   git fetch && git log --oneline HEAD..origin/main
   git pull
   docker compose up -d --build
   curl http://127.0.0.1:8000/health
   ```

4. Migrasi database berjalan otomatis. Kalau backend gagal start, baca `docker compose logs backend`. Untuk kembali ke versi sebelumnya, `git checkout <commit-lama>` lalu bangun ulang, dan pulihkan database dari cadangan kalau migrasi baru sudah terlanjur berjalan.

### Mengganti model LLM

Ubah `OLLAMA_MODEL` di `.env`, unduh modelnya dengan `ollama pull`, lalu `docker compose up -d backend`. Jalankan evaluasi akurasi (Bagian 3) dengan model baru sebelum dipakai, karena aturan di prompt disetel untuk `gemma4:e4b`.

### Mengubah daftar kategori dan jenis

Daftar ada di `pipeline/config/taxonomy.json`. Nama jenis wajib unik di seluruh taksonomi. Setelah diubah, jalankan `pytest pipeline/tests`, bangun ulang backend, dan jalankan evaluasi akurasi. Dokumen lama tidak ikut berubah.

## 6. Cadangan dan pemulihan

**(belum diuji)** Dua hal yang wajib dicadangkan bersama-sama: database dan folder `storage/`. Salah satu tanpa yang lain tidak bisa dipulihkan dengan utuh.

### Cadangan harian

Contoh skrip `/opt/ai-dmc/cadangan.sh`:

```
#!/bin/sh
set -e
cd /opt/ai-dmc
TUJUAN=/mnt/cadangan/ai-dmc
HARI=$(date +%F)
mkdir -p "$TUJUAN"
docker compose exec -T db pg_dump -U ai_dmc -d ai_dmc -Fc > "$TUJUAN/db_$HARI.dump"
tar czf "$TUJUAN/storage_$HARI.tar.gz" storage
find "$TUJUAN" -name 'db_*.dump' -mtime +7 -delete
find "$TUJUAN" -name 'storage_*.tar.gz' -mtime +7 -delete
```

Jadwalkan pukul 02.00 dengan `crontab -e`:

```
0 2 * * * /opt/ai-dmc/cadangan.sh >> /var/log/ai-dmc-cadangan.log 2>&1
```

- `/mnt/cadangan` adalah disk eksternal atau NAS, bukan disk yang sama dengan server.
- Cadangan berisi data pribadi dosen. Batasi aksesnya sama seperti server.
- Periksa setiap hari bahwa berkas hari itu ada dan ukurannya wajar.

### Memulihkan

Pulihkan ke database kosong, bukan menimpa database yang sedang berjalan:

1. Hentikan aplikasi, simpan data lama, dan buat volume baru:

   ```
   docker compose down
   mv storage storage_lama
   docker volume rm ai-dmc_postgres_data
   docker compose up -d db
   ```

   Nama volume bisa berbeda; cek dengan `docker volume ls`. Pindahkan volume lama ke cadangan dulu kalau masih ragu.

2. Pulihkan database dan berkas:

   ```
   docker compose exec -T db pg_restore -U ai_dmc -d ai_dmc --no-owner < /mnt/cadangan/ai-dmc/db_<tanggal>.dump
   tar xzf /mnt/cadangan/ai-dmc/storage_<tanggal>.tar.gz
   docker compose up -d
   ```

3. Periksa `/health`, masuk dengan satu akun, dan buka beberapa dokumen di Arsip.

Uji pemulihan ini sekali sebelum go-live, lalu setiap 6 bulan.

## 7. Pemecahan masalah

| Gejala | Kemungkinan penyebab | Tindakan |
|---|---|---|
| Semua dokumen baru gagal, keterangan "Model AI tidak bisa dihubungi" | Ollama mati atau tidak terjangkau | `ollama ps`, `systemctl status ollama`, cek `OLLAMA_HOST` berupa URL lengkap |
| Hanya dokumen scan atau foto yang gagal, keterangan "OCR tidak tersedia di server" | PaddleOCR tidak terpasang atau modelnya gagal diunduh | Lihat log backend. Di container, cek Bagian 9 poin 1 |
| Satu dokumen butuh lebih dari 5 menit | Model LLM tidak muat di GPU | `ollama ps`, kolom PROCESSOR harus 100% GPU. Tutup program lain yang memakai GPU |
| Banyak dokumen gagal "terhenti saat layanan dimulai ulang" | Backend di-restart saat memproses | Proses ulang lewat `kelola`. Lain kali cek status diproses sebelum restart |
| Backend tidak mau start: "Mock tidak diizinkan pada production" | `PIPELINE_MODE=mock` dengan `APP_ENVIRONMENT=production` | Ubah ke `PIPELINE_MODE=real` |
| Backend tidak mau start: galat `JWT_SECRET` | Nilai kurang dari 32 karakter | Buat nilai acak baru (Bagian 2) |
| Frontend tampil tetapi gagal masuk dengan pesan jaringan | `NEXT_PUBLIC_API_URL` atau `CORS_ORIGINS` tidak cocok dengan domain | Samakan dengan domain, lalu bangun ulang frontend |
| Unggahan besar ditolak sebelum sampai backend | Batas ukuran di reverse proxy | Naikkan `max_size` (Bagian 4 langkah 6) |
| Disk hampir penuh | Berkas dokumen atau image Docker lama | `du -sh storage`, `docker system df`, lalu `docker image prune` |

Log backend tidak mencatat teks dokumen, tetapi bisa memuat kode dan lokasi berkas. Saat meminta bantuan tim pengembang, kirim potongan log dan kode dokumen, bukan berkas dokumennya.

## 8. Keamanan server

- Hanya port 443 (dan 80 untuk redirect) yang terbuka ke jaringan kampus. Port 3000, 8000, 5432, dan 11434 hanya untuk mesin itu sendiri. Di `docker-compose.yml` port sudah diikat ke `127.0.0.1`.
- SSH hanya dengan kunci, hanya untuk admin server.
- `.env`, folder `storage/`, dan berkas cadangan hanya bisa dibaca admin server.
- Pasang pembaruan keamanan Ubuntu secara rutin (`unattended-upgrades`).
- Aturan lengkap ada di Kebijakan Data dan Keamanan.

## 9. Pekerjaan yang harus selesai sebelum server dipakai

Sumber: Kebutuhan Server Bagian 6. Diulang di sini supaya pengelola tahu langkah mana yang belum bisa dijalankan.

1. **PaddleOCR belum masuk image backend.** `backend/requirements-pipeline.lock` belum memuat `paddlepaddle` dan `paddleocr`. Tanpa itu, dokumen scan dan foto gagal di container.
2. **Cache model PaddleOCR belum disimpan di volume.** Model diunduh ulang setiap container dibuat ulang.
3. **Reverse proxy dan HTTPS belum ada di Compose.** Contoh Caddy di Bagian 4 masih usulan.
4. **Skrip cadangan belum ada di repo.** Contoh di Bagian 6 masih usulan.
5. **Image belum pernah dibangun dan dijalankan.**
6. **Antrean belum permanen.** Restart saat ada dokumen diproses membuat dokumen itu gagal.

Setelah poin 1 sampai 5 selesai dan diuji, tanda "(belum diuji)" di panduan ini perlu diperbarui.
