# Pipeline AI AI-DMC

Bagian Orang 1: dari berkas masuk sampai keluar JSON hasil AI, sesuai kontrak `docs/PEMBAGIAN_PERAN.md` Bagian 4.1.

```
berkas → extract.py ──(PDF digital, DOCX)──────────────→ teks
                    └─(PDF scan, gambar)→ ocr.py ──────→ teks
teks → classify.py (Ollama, voting N kali) → jenis + metadata + skor
     → main.py: process_document() → dict sesuai kontrak
```

## Setup

```bash
# dari root repo
python -m venv .venv && source .venv/bin/activate
pip install -r pipeline/requirements.txt

# OCR (opsional di laptop, wajib di server)
pip install paddlepaddle paddleocr

# LLM lokal
# 1. install Ollama: https://ollama.com
# 2. unduh model
ollama pull gemma4:e4b        # atau: ollama pull qwen3:8b
```

## Pakai

```python
from pipeline.main import process_document   # asli
from pipeline.mock import process_document   # mock, tanpa OCR/LLM (untuk Orang 2)

hasil = process_document("storage/abc.pdf")
```

Coba dari terminal:

```bash
python -m pipeline.main data/dummy/sk_mengajar.pdf
```

`process_document()` tidak pernah melempar exception. Kalau gagal, `status` = `"gagal"`, `error` berisi pesan yang bisa ditampilkan ke dosen, dan `klasifikasi` berisi `null`.

## Konfigurasi (environment)

| Variabel | Default | Fungsi |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Alamat Ollama |
| `OLLAMA_MODEL` | `gemma4:e4b` | Nama model. Ganti model cukup di sini |
| `OLLAMA_TIMEOUT` | `180` | Batas waktu per panggilan (detik) |
| `PIPELINE_VOTES` | `3` | Jumlah panggilan LLM per dokumen (lihat Skor keyakinan) |
| `PIPELINE_TEMPERATURE` | `0.4` | Suhu panggilan ke-2 dan seterusnya |
| `PIPELINE_MAX_CHARS` | `12000` | Batas karakter teks yang dikirim ke LLM |
| `OCR_LANG` | `id` | Bahasa PaddleOCR |
| `OCR_DPI` | `200` | Resolusi render halaman PDF scan |
| `OCR_MAX_PAGES` | `5` | Maksimal halaman yang di-OCR per dokumen |
| `OCR_ENABLE_MKLDNN` | `0` | Akselerasi CPU oneDNN. Biarkan 0 di Windows (bug PaddlePaddle 3.3) |
| `PDF_MIN_CHARS_PER_PAGE` | `30` | Halaman dengan teks di bawah ini dianggap scan |

## Cara kerja penting

### Klasifikasi
- LLM hanya memilih **jenis** dari daftar di `config/taxonomy.json`. Daftar ini dipaksa lewat JSON Schema (structured output Ollama), jadi model tidak bisa mengarang jenis baru.
- **Subkategori dan kategori diturunkan dari jenis**, bukan ditebak LLM. Konsekuensinya: nama jenis wajib unik di seluruh taksonomi (dicek otomatis saat dimuat).
- Jenis yang tetap tidak dikenal diperlakukan sebagai `Lainnya`.

### Skor keyakinan (versi awal P1-10)
- LLM dipanggil `PIPELINE_VOTES` kali. Panggilan pertama suhu 0, sisanya suhu `PIPELINE_TEMPERATURE`.
- Skor = jumlah panggilan yang memilih jenis mayoritas ÷ total panggilan. Panggilan gagal dihitung tidak setuju.
- Contoh dengan 3 panggilan: 3 sepakat = 1,00; 2 sepakat = 0,67; semua beda = 0,33.
- Pembatas: jenis `Lainnya` maksimal 0,5; teks sangat pendek maksimal 0,6.
- `PIPELINE_VOTES=1` lebih cepat, tapi skor selalu 0,5 sehingga semua dokumen masuk Kotak Verifikasi.
- Dengan 3 panggilan, skor hanya bisa 0,33 / 0,67 / 1,0. Jadi ambang 0,85 artinya "semua panggilan harus sepakat". Kalau mau skor lebih halus, naikkan voting ke 5 (lebih lambat) atau ganti metode di P1-10.

### Metadata
- Diambil dari panggilan pertama yang memilih jenis pemenang.
- Isian kosong versi LLM (`"null"`, `"-"`, `"tidak ada"`) dibersihkan jadi `null`.
- Tanggal yang tidak berformat `YYYY-MM-DD` atau tidak valid dibuang (jadi `null`), bukan ditebak.
- NIP dibersihkan jadi angka saja.

### Keamanan
- Semua pemrosesan lokal. Tidak ada panggilan ke API AI publik.
- Teks dokumen dibungkus tag `<dokumen>`, tag di dalam teks dinetralkan, dan prompt menegaskan isi dokumen adalah data (P1-11).
- Dokumen panjang dipotong: 2/3 awal + 1/3 akhir (P1-12 versi awal).

## Tes

```bash
python -m pytest pipeline/tests -q
```

Tes memakai LLM dan OCR palsu, jadi bisa jalan tanpa Ollama dan PaddleOCR.

## Evaluasi akurasi (P1-09)

1. Taruh dokumen uji di `data/dummy/` (folder `data/` tidak di-commit).
2. Isi `data/dummy/labels.csv` dengan format `pipeline/eval/labels_template.csv`.
3. Jalankan (Ollama harus hidup):

```bash
python -m pipeline.eval.run_eval --data data/dummy --labels data/dummy/labels.csv
```

Laporan ada di `pipeline/eval/hasil/<waktu>/laporan.md`, termasuk persen dokumen yang lolos ambang dan akurasi di antara yang lolos (bahan kalibrasi P1-18). Folder `hasil/` juga tidak di-commit karena bisa memuat metadata dosen.

## Status

| Tugas | Status |
|---|---|
| P1-01 Mock | selesai |
| P1-04 Taksonomi | draf, perlu dikonfirmasi admin CoE |
| P1-05 Ekstraksi teks | selesai, teruji |
| P1-06 OCR | kode selesai, **belum diuji dengan PaddleOCR asli** |
| P1-07 Klasifikasi | kode selesai, teruji dengan LLM palsu, **belum diuji dengan Ollama asli** |
| P1-08 `process_document()` | selesai, teruji |
| P1-09 Script evaluasi | selesai, menunggu dataset dummy |
| P1-10 / P1-11 / P1-12 | versi awal sudah masuk |
