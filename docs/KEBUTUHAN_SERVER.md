# Kebutuhan Server AI-DMC (1 prodi, sekitar 50 dosen)

Diperbarui 23 November 2026 dari kode di branch feat/ai-asli-dan-perbaikan-ui.
Daftar persiapan sebelum deploy. Belum dijalankan di server sungguhan.

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
| Docker Engine + Docker Compose | Terbaru stabil | Hanya untuk PostgreSQL dan frontend |
| Python 3.12 | Bawaan Ubuntu 24.04 | Backend dan pipeline AI, dipasang oleh `deploy/pasang-backend.sh` |
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

## 6. Susunan dan kesiapan kode

Susunan server sama dengan laptop pengembang: **PostgreSQL dan frontend di Docker, backend (dengan PaddleOCR), Ollama, dan Caddy langsung di Ubuntu.** Backend tidak dimasukkan ke Docker supaya PaddleOCR dan Ollama memakai GPU host tanpa image CUDA dan NVIDIA Container Toolkit.

Sudah ada:

- `docker-compose.yml`: PostgreSQL 17 dan frontend, port hanya dibuka ke `127.0.0.1`. Service `backend` hanya menyala dengan `--profile backend-docker` dan tidak dipakai di server.
- `deploy/pasang-backend.sh`: memasang backend, PaddlePaddle GPU, PaddleOCR, layanan systemd, dan perintah `kelola`.
- `deploy/cadangan.sh` dan `deploy/Caddyfile.contoh`.
- Backend menolak `APP_ENVIRONMENT=production` kalau pipeline masih mode mock.

Sudah diuji (22 November 2026): pemasangan dependensi di Ubuntu 24.04 (PaddlePaddle versi CPU), serta cadangan dan pemulihan database.

Belum diuji, baru bisa setelah server ada:

1. Layanan systemd dan perintah `kelola` di server sungguhan.
2. PaddlePaddle versi GPU dan OCR dokumen scan di Linux.
3. Caddy dan HTTPS dengan domain kampus.
4. Seluruh alur unggah sampai verifikasi lewat domain.

Dokumen yang sedang diproses saat backend restart dilanjutkan otomatis setelah backend menyala lagi. Dokumen diproses satu per satu.

## 7. Urutan deploy

Langkah lengkap ada di Panduan Instalasi dan Operasional, Bagian 4. Ringkasnya:

1. Pasang Ubuntu, driver NVIDIA, dan Docker. Cek `nvidia-smi`.
2. Pasang Ollama, `ollama pull gemma4:e4b`, cek modelnya muat penuh di GPU (`ollama ps`).
3. Ambil kode ke `/opt/ai-dmc`, salin `.env.example` menjadi `.env`, isi rahasia baru dan nilai untuk server.
4. `docker compose up -d --build` untuk PostgreSQL dan frontend.
5. `sudo sh deploy/pasang-backend.sh` untuk backend, lalu cek `/health`.
6. Pasang Caddy dengan `deploy/Caddyfile.contoh`.
7. Buat akun admin lewat `sudo kelola akun buat --peran admin`.
8. Pasang cadangan harian dan coba pulihkan sekali.
9. Uji 10 dokumen sintetis campuran (digital, scan, foto, DOCX) sebelum memakai data asli.
10. Buat akun dosen dari CSV, uji coba dengan beberapa dosen dulu, baru dibuka untuk semua.

## 8. Setelah berjalan

- Backup harian dengan `deploy/cadangan.sh`: database dan `storage/`, disimpan 7 hari terakhir.
- Pantau ruang disk, dokumen berstatus gagal, dan waktu proses per dokumen.
- Restart dan update sebaiknya di luar jam kerja. Dokumen yang sedang diproses dilanjutkan otomatis setelah backend menyala lagi.
