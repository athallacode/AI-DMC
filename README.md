# AI-DMC: AI Document Management Center

Repositori dokumen dosen CoE AIIS Telkom University. Dosen mengunggah dokumen eviden (SK, sertifikat, RPS, nilai), AI lokal membaca, mengklasifikasikan, dan mengekstrak metadatanya, lalu dosen cukup menyetujui atau mengoreksi.

Semua pemrosesan AI berjalan di server lokal. Tidak ada dokumen yang dikirim ke layanan AI publik.

## Mulai dari sini

| Dokumen | Isi |
|---|---|
| [docs/PEMBAGIAN_PERAN.md](docs/PEMBAGIAN_PERAN.md) | Ruang lingkup MVP, pembagian peran, **kontrak antarmuka** (JSON pipeline, API, skema database) |
| [docs/RINCIAN_TUGAS.md](docs/RINCIAN_TUGAS.md) | Daftar tugas ber-ID, jadwal, titik serah terima |
| [pipeline/README.md](pipeline/README.md) | Cara setup dan menjalankan pipeline AI |
| [docs/PIPELINE_INTEGRATION.md](docs/PIPELINE_INTEGRATION.md) | Cara menghubungkan pipeline ke aplikasi dan batas pengujiannya |
| [docs/PANDUAN_DOSEN.md](docs/PANDUAN_DOSEN.md) | Panduan penggunaan aplikasi untuk dosen |
| [AGENTS.md](AGENTS.md) | Aturan untuk AI coding agent (Codex, Claude Code) |
| `.agents/skills/ai-dmc-apple-glass-ui/` | Panduan desain UI (Apple light + glass) |

## Struktur

```
pipeline/   Orang 1: ekstraksi teks, OCR, klasifikasi LLM, evaluasi
backend/    Orang 2: FastAPI + PostgreSQL
frontend/   Orang 2: Next.js
docs/       Dokumen tim dan laporan mingguan
```

## Status singkat

- Pipeline AI: berjalan untuk PDF digital, PDF scan, DOCX, dan foto. Akurasi 5/5 pada dokumen dummy (belum diuji di dokumen asli CoE).
- Aplikasi: backend dan frontend tersedia; mode mock tetap menjadi default pengembangan dan ditandai pada UI.
- Integrasi: adapter pipeline asli tersedia melalui `app.integrations.real:process_document`. Aktifkan `PIPELINE_MODE=real` setelah Ollama dan dependensi runtime siap.

## Penting

Folder `data/` dan `storage/` tidak boleh di-commit. Dokumen dosen berisi data pribadi.
