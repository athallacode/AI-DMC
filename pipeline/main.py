"""Titik masuk pipeline (P1-08).

    from pipeline.main import process_document
    hasil = process_document("storage/abc.pdf")

Output selalu dict sesuai kontrak 4.1 (docs/PEMBAGIAN_PERAN.md).
Fungsi ini TIDAK PERNAH melempar exception: semua kegagalan jadi status "gagal" dengan pesan di "error".

Bisa juga dijalankan dari terminal untuk mencoba satu berkas:
    python -m pipeline.main path/ke/dokumen.pdf
"""

import json
import logging
import sys
import time

from pipeline.classify import KlasifikasiGagal, klasifikasi
from pipeline.config import Settings, get_settings
from pipeline.extract import BerkasTidakDidukung, ekstrak_teks
from pipeline.llm import KlienLLM, KlienOllama, LLMError
from pipeline.ocr import OcrTidakTersedia
from pipeline.schemas import buat_output
from pipeline.taxonomy import load_taxonomy

log = logging.getLogger("pipeline")

MIN_KARAKTER_TEKS = 20


def process_document(
    file_path: str,
    *,
    settings: Settings | None = None,
    klien: KlienLLM | None = None,
    ocr_fn=None,
) -> dict:
    """Proses satu berkas. Parameter opsional hanya untuk pengujian; backend cukup kirim file_path."""
    mulai = time.perf_counter()
    settings = settings or get_settings()
    nama_model = klien.nama_model if klien else settings.ollama_model
    jenis_berkas = None
    teks = ""

    def gagal(pesan: str) -> dict:
        log.warning("Pipeline gagal untuk %s: %s", file_path, pesan)
        return buat_output(
            status="gagal",
            jenis_berkas=jenis_berkas,
            teks=teks,
            model_dipakai=nama_model,
            waktu_proses_detik=time.perf_counter() - mulai,
            error=pesan,
        )

    try:
        ekstraksi = ekstrak_teks(file_path, settings, ocr_fn)
        jenis_berkas, teks = ekstraksi.jenis_berkas, ekstraksi.teks
        if len(teks.strip()) < MIN_KARAKTER_TEKS:
            return gagal("Teks dokumen tidak terbaca. Pastikan hasil scan atau foto cukup jelas, lalu unggah ulang.")

        klien = klien or KlienOllama(settings)
        hasil = klasifikasi(teks, klien, load_taxonomy(), settings)
        for c in ekstraksi.catatan + hasil.catatan:
            log.info("%s: %s", file_path, c)

        return buat_output(
            status="sukses",
            jenis_berkas=jenis_berkas,
            teks=teks,
            kategori=hasil.kategori,
            subkategori=hasil.subkategori,
            jenis=hasil.jenis,
            skor_keyakinan=hasil.skor_keyakinan,
            metadata=hasil.metadata,
            ringkasan=hasil.ringkasan,
            model_dipakai=klien.nama_model,
            waktu_proses_detik=time.perf_counter() - mulai,
        )
    except FileNotFoundError as e:
        return gagal(str(e))
    except BerkasTidakDidukung as e:
        return gagal(str(e))
    except OcrTidakTersedia as e:
        return gagal(f"OCR tidak tersedia di server: {e}")
    except LLMError as e:
        return gagal(f"Model AI tidak bisa dihubungi: {e}")
    except KlasifikasiGagal as e:
        return gagal(f"Klasifikasi gagal: {e}")
    except Exception as e:  # pengaman terakhir: pipeline tidak boleh membuat backend crash
        log.exception("Error tak terduga di pipeline")
        return gagal(f"Error tak terduga: {type(e).__name__}: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(sys.argv) < 2:
        print("Pemakaian: python -m pipeline.main <berkas> [berkas lain ...]")
        sys.exit(1)
    for p in sys.argv[1:]:
        keluaran = process_document(p)
        keluaran["teks"] = keluaran["teks"][:300] + ("..." if len(keluaran["teks"]) > 300 else "")
        print(json.dumps(keluaran, ensure_ascii=False, indent=2))
