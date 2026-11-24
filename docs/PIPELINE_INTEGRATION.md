# Integrasi pipeline ke aplikasi

Sumber: https://github.com/athallacode/AI-DMC/tree/ca20becec2d5159f8955dfecbff16fa6a13ad112/pipeline

Folder `pipeline/` disalin persis dari commit tersebut. Kode AI, prompt, dan taksonomi tetap milik Orang 1; perubahan aplikasi berada di backend dan konfigurasi deployment.

## Pemetaan sebelum implementasi

- Output pipeline dan endpoint aplikasi tidak berubah.
- Taksonomi sumber memakai kunci `kategori`; adapter menyajikannya sebagai `categories` untuk kontrak frontend yang sudah ada.
- Hasil gagal sumber berisi tiga field klasifikasi bernilai null. Validator backend menerima bentuk gagal tersebut tanpa melonggarkan validasi hasil sukses.
- Adapter meneruskan konfigurasi Ollama dari settings aplikasi, termasuk `.env`, ke settings pipeline. Tidak ada fallback diam-diam ke mock.
- Docker menyertakan snapshot pipeline dan dependensi ekstraksi. OCR PaddleOCR opsional dan perlu dipasang serta diuji terpisah.

## Menjalankan pengujian

Branch `Test#2` dibuat langsung dari `main` repo tim agar perubahan dapat dibandingkan dan ditinjau melalui Pull Request. `main` tetap tidak berubah sampai proses review dan merge dilakukan oleh tim.

Untuk lokal, pasang `backend/requirements.lock` dan `backend/requirements-pipeline.lock` ke venv backend. Dari folder backend, tambahkan root repo ke `PYTHONPATH` (`$env:PYTHONPATH=(Resolve-Path ..).Path` di PowerShell). Gunakan database dan storage pengujian sendiri.

Atur `.env`: `PIPELINE_MODE=real`, `PIPELINE_IMPORT=app.integrations.real:process_document`, `TAXONOMY_PATH=../pipeline/config/taxonomy.json`, `OLLAMA_HOST=http://localhost:11434`, dan `OLLAMA_MODEL` sesuai model yang tersedia. Jalankan Ollama secara lokal dan backend seperti biasa. Untuk Docker gunakan path dan host dari `.env.example`; jalankan `docker compose up --build` setelah mengatur password dan secret.

PDF digital dan DOCX membutuhkan Ollama serta dependensi inti. Scan dan gambar juga membutuhkan `paddlepaddle` dan `paddleocr>=3` sesuai panduan sumber `pipeline/README.md`; image Docker inti belum menyertakan OCR. Mode `mock` tetap tersedia sebagai demo yang ditandai di UI.

`/health` menunjukkan mode konfigurasi, bukan bukti bahwa model/OCR sudah siap. Gunakan dokumen sintetis untuk uji awal. Hasil gagal tidak otomatis menjadi terverifikasi.

## Menjalankan AI asli di host Windows

Backend berjalan di host, bukan di container, karena image Docker belum menyertakan OCR. PostgreSQL tetap lewat Compose.

1. Buat venv Python 3.12 di root repo, lalu pasang `backend/requirements.lock`, `backend/requirements-pipeline.lock`, `paddlepaddle`, dan `paddleocr>=3`.
2. Salin `.env.example` ke `.env`, lalu atur `PIPELINE_MODE=real`, `STORAGE_DIR=../storage`, `TAXONOMY_PATH=../pipeline/config/taxonomy.json`, `OLLAMA_HOST=http://localhost:11434`, dan `OLLAMA_MODEL` sesuai `ollama list`.
3. Tulis host `DATABASE_URL` sebagai `127.0.0.1`, bukan `localhost`. Port database hanya terbuka di IPv4, dan koneksi `psycopg` lewat `localhost` menggantung di Windows.
4. Jalankan `docker compose up -d db`, lalu `backend/run-local.ps1` (migrasi, seed, Uvicorn), lalu `npm --prefix frontend run dev`.

Variabel sistem mengalahkan `.env`. Kalau `OLLAMA_HOST` sistem berisi alamat bind server seperti `0.0.0.0:11434`, panggilan ke Ollama gagal; `run-local.ps1` menimpanya untuk proses backend saja.

## Hasil uji AI asli 4 November 2026

Uji ujung ke ujung dengan enam dokumen sintetis lewat API, PostgreSQL 17, Ollama `qwen3:8b`, dan PaddleOCR 3.7.0 di CPU, pada laptop RTX 3050 6 GB. Enam dokumen ini bukan pengukuran akurasi.

- PDF digital, DOCX, foto, dan PDF scan terklasifikasi benar dengan skor 1,00 dan langsung `terverifikasi`.
- Dokumen ambigu menjadi `Lainnya` dengan skor 0,50 dan masuk Kotak Verifikasi.
- Prompt injection awalnya berhasil sebagian: judul terisi `DIRETAS`, dan hanya skor 0,33 yang menahannya di Kotak Verifikasi. Setelah penyaring, batas skor, dan pengingat ditambahkan, empat varian (Indonesia, Inggris, tag palsu, dan kalimat halus yang lolos dari pola) tidak lagi mengubah judul atau jenis. Empat varian ini bukan jaminan untuk serangan lain.
- Taksonomi belum punya jenis surat tugas narasumber, jadi surat seperti itu terbaca sebagai `Surat tugas penelitian`.
- Skor hanya mengukur kesepakatan `jenis`, bukan metadata: satu sertifikat lolos dengan nomor sertifikat salah masuk ke `identifier`.
- Waktu proses sekitar 45 sampai 100 detik per dokumen. Model terbagi antara CPU dan GPU karena VRAM tidak cukup.
- Unggahan ulang ditolak sebagai duplikat, dan 32 tes otomatis lulus.

## Uji banding model 4 November 2026

Dataset 38 dokumen sintetis dari `tools/generate_dummy_dataset.py`, voting 3 kali, ambang 0,85, laptop RTX 3050 6 GB. Ini indikasi awal, bukan uji banding 100 sampai 200 dokumen nyata yang diminta rancangan.

| Ukuran | `qwen3:8b` | `gemma3:4b` |
|---|---|---|
| Akurasi kategori (target 90%) | 84,2% | 55,3% |
| Akurasi subkategori | 81,6% | 47,4% |
| Akurasi jenis | 78,9% | 26,3% |
| Nomor dokumen | 97,4% | 100% |
| Tanggal terbit | 78,9% | 71,1% |
| Periode | 100% | 89,5% |
| Lolos otomatis | 31 dari 38 | 31 dari 38 |
| Jenis benar di antara yang lolos | 27 dari 31 | 8 dari 31 |
| Tanggal karangan pada dokumen tanpa tanggal | 7 dari 13 | 9 dari 13 |
| Waktu 6 dokumen campuran, GPU kosong | 362,7 detik | 151,5 detik |

Rata-rata 74 detik per dokumen di laporan Qwen tidak dipakai karena tercampur evaluasi lain, jadi waktu Qwen diukur ulang pada enam dokumen. Prompt saat ini disusun tanpa penyesuaian khusus untuk Gemma.

`gemma4:e4b` (total 8B parameter) diuji dengan dataset yang sama:

| Ukuran | `qwen3:8b` | `gemma4:e4b` |
|---|---|---|
| Akurasi kategori (target 90%) | 84,2% | 92,1% |
| Akurasi subkategori | 81,6% | 89,5% |
| Akurasi jenis | 78,9% | 73,7% |
| Tanggal terbit | 78,9% | 94,7% |
| Tanggal karangan pada dokumen tanpa tanggal | 7 dari 13 | 1 dari 13 |
| Lolos otomatis | 31 dari 38 | 33 dari 38 |
| Jenis benar di antara yang lolos | 27 dari 31 | 25 dari 33 |
| Kategori benar di antara yang lolos | 29 dari 31 | 32 dari 33 |
| Waktu 6 dokumen campuran, GPU kosong | 362,7 detik | 138,9 detik |

Pada evaluasi penuh `gemma4:e4b`, OCR melambat sekitar lima kali dibanding uji 6 dokumen dan pengukuran OCR terpisah. Penyebabnya belum diketahui. Akurasi tidak terpengaruh, tetapi rata-rata waktu dari evaluasi itu tidak dipakai.

Selisih kedua model hanya beberapa dokumen dari 38, jadi pemilihan model final tetap menunggu dokumen nyata. `gemma4:e4b` menjadi model aktif untuk sementara. Sebelum Fase 1 ditutup, perlu perbaikan orientasi OCR, tanggal karangan, dan petunjuk jenis yang sering tertukar.

## Hasil pengujian 31 Oktober 2026

- 32 tes lulus: backend, adapter integrasi, dan tes pipeline sumber. Perintah dari `backend`: `python -m pytest tests ../pipeline/tests -q --basetemp=.test-tmp-integration` dengan `PYTHONPATH` menunjuk root repo.
- Integrasi menguji unggah DOCX sintetis, ekstraksi asli, klasifikasi dengan klien LLM sintetis, penyimpanan hasil, ambang verifikasi, akses dosen lain, kesamaan taksonomi, serta layanan LLM gagal.
- Respons LLM/OCR dalam pengujian otomatis disimulasikan; ini bukan pengukuran akurasi AI atau bukti OCR/model langsung bekerja.
- Ollama pada localhost:11434 tidak terhubung. PaddleOCR langsung belum diuji.
- Docker/PostgreSQL tidak tersedia pada mesin pengujian. Build image, migrasi PostgreSQL, dan uji deployment tetap harus dijalankan di lingkungan yang tersedia; SQLite tidak menggantikannya.
- Frontend tidak diubah dalam integrasi ini; build UI sebelumnya tetap menjadi baseline. Ada satu peringatan deprecation Starlette/httpx pada tes backend.
