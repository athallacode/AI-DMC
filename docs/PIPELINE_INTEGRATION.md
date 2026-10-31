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

## Hasil pengujian 31 Oktober 2026

- 32 tes lulus: backend, adapter integrasi, dan tes pipeline sumber. Perintah dari `backend`: `python -m pytest tests ../pipeline/tests -q --basetemp=.test-tmp-integration` dengan `PYTHONPATH` menunjuk root repo.
- Integrasi menguji unggah DOCX sintetis, ekstraksi asli, klasifikasi dengan klien LLM sintetis, penyimpanan hasil, ambang verifikasi, akses dosen lain, kesamaan taksonomi, serta layanan LLM gagal.
- Respons LLM/OCR dalam pengujian otomatis disimulasikan; ini bukan pengukuran akurasi AI atau bukti OCR/model langsung bekerja.
- Ollama pada localhost:11434 tidak terhubung. PaddleOCR langsung belum diuji.
- Docker/PostgreSQL tidak tersedia pada mesin pengujian. Build image, migrasi PostgreSQL, dan uji deployment tetap harus dijalankan di lingkungan yang tersedia; SQLite tidak menggantikannya.
- Frontend tidak diubah dalam integrasi ini; build UI sebelumnya tetap menjadi baseline. Ada satu peringatan deprecation Starlette/httpx pada tes backend.
