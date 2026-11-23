# Panduan Instalasi dan Operasional AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Versi uji coba, November 2026

Panduan ini untuk pengembang dan pengelola server. Isinya cara memasang, menjalankan, memperbarui, mencadangkan, dan memulihkan AI-DMC.

Ada dua jalur instalasi dengan tingkat kesiapan yang berbeda:

| Jalur | Untuk | Status |
|---|---|---|
| Bagian 3: laptop pengembang (Windows) | Pengembangan, demo, evaluasi akurasi | **Sudah dipakai dan teruji** |
| Bagian 4: server Ubuntu | Pemakaian 1 prodi | **Sebagian teruji** (lihat Bagian 9). Belum pernah dijalankan di server sungguhan |

Susunan server sama dengan laptop pengembang, hanya Windows diganti Ubuntu: PostgreSQL dan frontend di Docker, sedangkan backend, Ollama, dan Caddy dipasang langsung di Ubuntu supaya PaddleOCR dan Ollama memakai GPU tanpa lapisan tambahan.

Jangan memakai data dosen asli di server sebelum Bagian 4 langkah 9 selesai.

## 1. Gambaran komponen

| Komponen | Isi | Port (hanya di mesin itu) |
|---|---|---|
| Frontend | Next.js 15, tampilan untuk dosen. Di server: container Docker | 3000 |
| Backend | FastAPI (Python 3.12), API, antrean proses, pipeline AI. Di server: layanan systemd `ai-dmc-backend` | 8000 |
| Pipeline AI | PyMuPDF dan python-docx (teks), PaddleOCR (scan dan foto), dijalankan di dalam backend | - |
| Ollama | LLM lokal `gemma4:e4b` untuk klasifikasi dan metadata. Di server: layanan systemd `ollama` | 11434 |
| PostgreSQL 17 | Akun, metadata dokumen, riwayat koreksi, log audit. Di server: container Docker | 5432 |
| Folder `storage/` | Berkas asli dokumen dosen | - |

Alur singkat: dosen mengunggah lewat frontend, backend menyimpan berkas ke `storage/` dan mencatatnya di database, lalu pipeline membaca teks, memanggil Ollama tiga kali (voting), dan menyimpan hasilnya. Dokumen yang ketiga suaranya sepakat (skor 1,00, ambang 0,85) langsung masuk arsip; sisanya masuk Kotak Verifikasi dosen.

Rincian arsitektur ada di dokumen Arsitektur AI-DMC.

## 2. Berkas konfigurasi `.env`

Semua komponen membaca `.env` di akar repo. Salin dari `.env.example`, lalu isi. **`.env` tidak boleh di-commit** dan hanya boleh dibaca admin server.

| Variabel | Laptop pengembang | Server |
|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER` | `ai_dmc` | `ai_dmc` |
| `POSTGRES_PASSWORD` | Bebas | **Acak, minimal 24 karakter** |
| `DATABASE_URL` | `postgresql+psycopg://ai_dmc:<password>@127.0.0.1:5432/ai_dmc` | sama |
| `JWT_SECRET` | Acak, minimal 32 karakter | **Acak baru, minimal 32 karakter** |
| `JWT_EXPIRE_MINUTES` | 60 | 60 |
| `APP_ENVIRONMENT` | `development` | `production` |
| `PIPELINE_MODE` | `real` (atau `mock` untuk UI saja) | `real` (production menolak `mock`) |
| `PIPELINE_IMPORT` | `app.integrations.real:process_document` | sama |
| `STORAGE_DIR` | `../storage` | `/opt/ai-dmc/storage` |
| `TAXONOMY_PATH` | `../pipeline/config/taxonomy.json` | `/opt/ai-dmc/pipeline/config/taxonomy.json` |
| `OLLAMA_HOST` | `http://localhost:11434` | `http://127.0.0.1:11434` |
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
- Di server, path di `.env` wajib absolut dan nilainya tidak boleh berisi spasi atau tanda `$`, karena perintah `kelola` membaca `.env` sebagai skrip shell. Nilai dari perintah pembuat nilai acak di atas aman.

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

## 4. Instalasi di server Ubuntu

Kebutuhan perangkat keras dan daftar yang perlu diminta ke CoE ada di dokumen Kebutuhan Server. Ringkasnya: satu PC dengan GPU NVIDIA 12 GB, RAM 32 GB, SSD 512 GB, UPS, dan disk cadangan terpisah.

Berkas pendukung ada di folder `deploy/`:

| Berkas | Fungsi |
|---|---|
| `pasang-backend.sh` | Memasang atau memperbarui backend: paket sistem, akun layanan `aidmc`, venv Python, PaddleOCR, layanan systemd, dan perintah `kelola` |
| `ai-dmc-backend.service` | Layanan systemd backend (dipasang oleh skrip di atas) |
| `kelola` | Perintah pengelola di server, dipakai sebagai `sudo kelola ...` |
| `Caddyfile.contoh` | Konfigurasi HTTPS dengan Caddy |
| `cadangan.sh` | Cadangan harian database dan `storage/` |

### Langkah

1. Pasang Ubuntu Server 24.04 LTS, driver NVIDIA, dan Docker Engine dengan plugin Compose. Masukkan akun admin ke grup `docker`. Periksa GPU terbaca:

   ```
   nvidia-smi
   ```

   Catat angka **CUDA Version** di pojok kanan atas, dipakai di langkah 5.

2. Pasang Ollama, unduh model, dan pastikan model termuat penuh di GPU:

   ```
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull gemma4:e4b
   ollama run gemma4:e4b "tes" && ollama ps
   ```

   Kolom PROCESSOR di `ollama ps` harus `100% GPU`. Biarkan Ollama mendengar di `127.0.0.1` (bawaan), karena backend berjalan di mesin yang sama.

3. Ambil kode dan siapkan `.env` sesuai kolom "Server" di Bagian 2:

   ```
   sudo mkdir -p /opt/ai-dmc && sudo chown $USER /opt/ai-dmc
   git clone <alamat-repo> /opt/ai-dmc
   cd /opt/ai-dmc
   cp .env.example .env
   nano .env
   ```

4. Nyalakan PostgreSQL dan frontend di Docker. Frontend dibangun dengan `NEXT_PUBLIC_API_URL` dari `.env`:

   ```
   docker compose up -d --build
   docker compose ps
   ```

   Keduanya harus berstatus running, dan `db` berstatus healthy. Backend sengaja tidak ikut di sini.

5. Pasang backend. Pilih paket PaddlePaddle sesuai CUDA Version dari langkah 1 (`cu118`, `cu126`, atau `cu129`; cek daftar terbaru di situs PaddlePaddle). Skrip memakai `cu126` kalau tidak diisi:

   ```
   sudo CUDA=cu126 sh deploy/pasang-backend.sh
   curl http://127.0.0.1:8000/health
   ```

   Skrip ini menjalankan uji bawaan PaddlePaddle; pastikan hasilnya menyebut GPU, bukan CPU. `/health` harus menjawab `"status":"ok"` dan `"pipeline_mode":"real"`. Migrasi database berjalan otomatis setiap backend start. Saat dokumen scan pertama diproses, PaddleOCR mengunduh modelnya (sekitar 140 MB) ke `/var/lib/ai-dmc`.

6. Pasang Caddy untuk HTTPS (ikuti cara pasang di situs Caddy untuk Ubuntu), lalu pakai contoh konfigurasi:

   ```
   sudo cp deploy/Caddyfile.contoh /etc/caddy/Caddyfile
   sudo nano /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   ```

   Ganti nama domain, dan tambahkan baris `tls` kalau memakai sertifikat dari kampus. Pastikan `NEXT_PUBLIC_API_URL=https://<domain>/api` dan `CORS_ORIGINS=https://<domain>` di `.env`. Kalau salah satunya baru diubah, jalankan `docker compose up -d --build frontend` dan `sudo systemctl restart ai-dmc-backend`.

7. Buat akun admin pertama. Seed akun dummy ditolak di production, jadi pakai perintah pengelola (lihat Panduan Admin):

   ```
   sudo kelola akun buat --username <admin> --nama "<Nama Admin CoE>" --peran admin --oleh "<Nama Pengelola>"
   ```

8. Pasang cadangan harian (Bagian 6) dan coba pulihkan sekali.
9. Uji 10 dokumen sintetis campuran (PDF digital, PDF scan, foto, DOCX) dari `tools/generate_dummy_format_nyata.py`. Periksa semuanya selesai tanpa status gagal, dan waktu per dokumen wajar (di bawah 1 menit dengan GPU).
10. Buat akun dosen dari CSV (Panduan Admin Bagian 2), uji coba dengan beberapa dosen, baru dibuka untuk semua.

## 5. Operasional sehari-hari

Semua perintah dijalankan dari `/opt/ai-dmc`.

| Keperluan | Perintah |
|---|---|
| Status backend | `systemctl status ai-dmc-backend` |
| Status database dan frontend | `docker compose ps` |
| Log backend terbaru | `journalctl -u ai-dmc-backend -n 100` |
| Log backend terus-menerus | `journalctl -u ai-dmc-backend -f` |
| Log frontend | `docker compose logs --tail 100 frontend` |
| Kesehatan API | `curl http://127.0.0.1:8000/health` |
| Model di GPU | `ollama ps` |
| Pemakaian GPU | `nvidia-smi` |
| Ruang disk | `df -h` dan `sudo du -sh storage` |
| Dokumen gagal | `sudo kelola dokumen gagal` |

Semua layanan menyala sendiri saat server dinyalakan ulang: backend dan Ollama lewat systemd, database dan frontend lewat `restart: unless-stopped` di Docker.

### Menghentikan dan menyalakan

1. Dokumen yang sedang diproses saat backend berhenti akan dilanjutkan otomatis setelah backend menyala lagi. Untuk melihat jumlahnya:

   ```
   docker compose exec db psql -U ai_dmc -d ai_dmc -c "SELECT count(*) FROM documents WHERE status = 'diproses'"
   ```

2. Hentikan backend dulu, baru yang lain. Nyalakan dengan urutan terbalik:

   ```
   sudo systemctl stop ai-dmc-backend
   docker compose down
   docker compose up -d
   sudo systemctl start ai-dmc-backend
   ```

   `docker compose down` tidak menghapus database dan berkas. **Jangan pakai `docker compose down -v`**, karena `-v` menghapus volume database.

Dokumen yang tiga kali terputus ditandai gagal. Proses ulang dengan `sudo kelola dokumen proses-ulang` (Panduan Admin Bagian 3).

### Memperbarui aplikasi

1. Cadangkan dulu (Bagian 6).
2. Lakukan di luar jam kerja. Dokumen yang sedang diproses dilanjutkan setelah backend menyala lagi.
3. Ambil versi baru, pasang ulang backend, bangun ulang frontend, lalu periksa:

   ```
   git fetch && git log --oneline HEAD..origin/main
   git pull
   sudo CUDA=cu126 sh deploy/pasang-backend.sh
   docker compose up -d --build
   curl http://127.0.0.1:8000/health
   ```

4. Migrasi database berjalan otomatis saat backend start. Kalau backend gagal start, baca `journalctl -u ai-dmc-backend -n 100`. Untuk kembali ke versi sebelumnya, `git checkout <commit-lama>` lalu ulangi langkah 3, dan pulihkan database dari cadangan kalau migrasi baru sudah terlanjur berjalan.

### Mengganti model LLM

Ubah `OLLAMA_MODEL` di `.env`, unduh modelnya dengan `ollama pull`, lalu `sudo systemctl restart ai-dmc-backend`. Jalankan evaluasi akurasi (Bagian 3) dengan model baru sebelum dipakai, karena aturan di prompt disetel untuk `gemma4:e4b`.

### Mengubah daftar kategori dan jenis

Daftar ada di `pipeline/config/taxonomy.json`. Nama jenis wajib unik di seluruh taksonomi. Setelah diubah, jalankan tes pipeline, `sudo systemctl restart ai-dmc-backend`, dan jalankan evaluasi akurasi. Dokumen lama tidak ikut berubah.

## 6. Cadangan dan pemulihan

Database dan folder `storage/` wajib dicadangkan bersama. Salah satu tanpa yang lain tidak bisa dipulihkan dengan utuh.

### Cadangan harian

Skrip `deploy/cadangan.sh` membuat `db_<tanggal>.dump` (pg_dump) dan `storage_<tanggal>.tar.gz`, lalu menghapus cadangan yang lebih tua dari 7 hari. Tujuan bawaannya `/mnt/cadangan/ai-dmc`, yaitu disk eksternal atau NAS, bukan disk yang sama dengan server.

Coba sekali dengan tangan, lalu jadwalkan pukul 02.00 lewat `sudo crontab -e`:

```
sudo /opt/ai-dmc/deploy/cadangan.sh
0 2 * * * /opt/ai-dmc/deploy/cadangan.sh >> /var/log/ai-dmc-cadangan.log 2>&1
```

- Ganti tujuan dengan `TUJUAN=/lokasi/lain` di depan perintah, dan lama simpan dengan `SIMPAN_HARI=14`.
- Skrip berhenti dengan pesan GAGAL kalau disk cadangan tidak terpasang.
- Cadangan berisi data pribadi dosen dan hanya bisa dibaca root.
- Periksa `/var/log/ai-dmc-cadangan.log` setiap hari: harus ada baris OK untuk hari itu.

### Memulihkan

Pulihkan ke database kosong, bukan menimpa database yang sedang berjalan:

1. Hentikan aplikasi dan simpan data lama:

   ```
   sudo systemctl stop ai-dmc-backend
   docker compose down
   sudo mv storage storage_lama
   docker volume ls
   docker volume rm ai-dmc_postgres_data
   docker compose up -d db
   ```

   Nama volume bisa berbeda; pakai nama dari `docker volume ls` yang berakhiran `postgres_data`.

2. Pulihkan database dan berkas:

   ```
   docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner' < /mnt/cadangan/ai-dmc/db_<tanggal>.dump
   sudo tar xzf /mnt/cadangan/ai-dmc/storage_<tanggal>.tar.gz
   sudo chown -R aidmc:aidmc storage
   docker compose up -d
   sudo systemctl start ai-dmc-backend
   ```

3. Periksa `/health`, masuk dengan satu akun, dan buka beberapa dokumen di Arsip. Setelah yakin, hapus `storage_lama`.

Uji pemulihan ini sekali sebelum go-live, lalu setiap 6 bulan.

## 7. Pemecahan masalah

| Gejala | Kemungkinan penyebab | Tindakan |
|---|---|---|
| Semua dokumen baru gagal, keterangan "Model AI tidak bisa dihubungi" | Ollama mati atau tidak terjangkau | `ollama ps`, `systemctl status ollama`, cek `OLLAMA_HOST` berupa URL lengkap |
| Hanya dokumen scan atau foto yang gagal, keterangan "OCR tidak tersedia di server" | PaddleOCR tidak terpasang, kurang pustaka sistem, atau model gagal diunduh | `journalctl -u ai-dmc-backend -n 200`, lalu jalankan ulang `pasang-backend.sh` |
| Satu dokumen butuh lebih dari 5 menit | Model LLM tidak muat di GPU, atau PaddlePaddle terpasang versi CPU | `ollama ps` harus 100% GPU. Ulangi `pasang-backend.sh` dengan `CUDA=` yang benar dan pastikan uji PaddlePaddle menyebut GPU |
| Dokumen gagal "terhenti beberapa kali saat layanan dimulai ulang" | Dokumen tiga kali terputus restart, atau membuat backend berhenti | Proses ulang sekali lewat `kelola`. Kalau gagal lagi, kirim potongan log ke tim pengembang |
| Dosen melapor "Terlalu banyak percobaan masuk yang gagal" | 5 kali salah password dalam 15 menit | Tunggu 15 menit, atau reset password (Panduan Admin) |
| Backend tidak mau start | Database belum siap, `.env` salah, atau `JWT_SECRET` kurang dari 32 karakter | `journalctl -u ai-dmc-backend -n 100`. Backend mencoba ulang sendiri setiap 10 detik |
| Galat "Mock tidak diizinkan pada production" | `PIPELINE_MODE=mock` dengan `APP_ENVIRONMENT=production` | Ubah ke `PIPELINE_MODE=real` |
| Frontend tampil tetapi gagal masuk dengan pesan jaringan | `NEXT_PUBLIC_API_URL` atau `CORS_ORIGINS` tidak cocok dengan domain | Samakan dengan domain, bangun ulang frontend, restart backend |
| Unggahan besar ditolak sebelum sampai backend | Batas ukuran di Caddy | Naikkan `max_size` di `/etc/caddy/Caddyfile` |
| `kelola` gagal membaca pengaturan | Nilai di `.env` berisi spasi atau `$` | Buat ulang nilai itu dengan perintah pembuat nilai acak (Bagian 2) |
| Disk hampir penuh | Berkas dokumen atau image Docker lama | `sudo du -sh storage`, `docker system df`, lalu `docker image prune` |

Log backend tidak mencatat teks dokumen, tetapi bisa memuat kode dan lokasi berkas. Saat meminta bantuan tim pengembang, kirim potongan log dan kode dokumen, bukan berkas dokumennya.

## 8. Keamanan server

- Hanya port 443 (dan 80 untuk redirect) yang terbuka ke jaringan kampus. Port 3000, 8000, 5432, dan 11434 hanya untuk mesin itu sendiri: Docker mengikatnya ke `127.0.0.1`, backend dan Ollama juga mendengar di `127.0.0.1`.
- Backend berjalan sebagai akun `aidmc` tanpa hak login, dengan pembatasan systemd (tidak bisa menulis ke folder sistem atau membaca folder home).
- `.env` hanya bisa dibaca admin server (pemiliknya), root, dan `aidmc`. Folder `storage/` hanya bisa dibaca `aidmc` dan root. Berkas cadangan hanya bisa dibaca root.
- SSH hanya dengan kunci, hanya untuk admin server.
- Pasang pembaruan keamanan Ubuntu secara rutin (`unattended-upgrades`).
- Aturan lengkap ada di Kebijakan Data dan Keamanan.

## 9. Yang sudah dan belum teruji

Sudah diuji, 22 November 2026:

- **Pemasangan dependensi di Ubuntu 24.04** (container bersih, PaddlePaddle versi CPU): semua paket terpasang tanpa konflik, uji bawaan PaddlePaddle lulus, dan backend, perintah `kelola`, serta pipeline bisa dimuat. Dari uji ini ditemukan pustaka `libgomp1` yang wajib ada; sudah masuk skrip.
- **Cadangan dan pemulihan**: `cadangan.sh` dijalankan terhadap database pengembangan, lalu dump dipulihkan ke PostgreSQL 17 kosong. Jumlah baris semua tabel sama, dan pelindung log audit ikut pulih.
- **Konfigurasi Compose**: tanpa profil hanya menyalakan `db` dan `frontend`.

Belum diuji, baru bisa setelah server tersedia:

1. Layanan systemd backend dan perintah `kelola` di server sungguhan.
2. PaddlePaddle versi GPU dan OCR di Linux dengan dokumen scan.
3. Caddy dan HTTPS dengan domain kampus.
4. Seluruh alur dari unggah sampai verifikasi lewat domain.

Batasan yang tetap ada:

- **Backend di Docker belum lengkap.** Service `backend` di `docker-compose.yml` hanya menyala dengan `--profile backend-docker` dan image-nya belum memuat PaddleOCR. Jalur ini tidak dipakai untuk server.

Setelah butir "Belum diuji" selesai di server, perbarui bagian ini.
