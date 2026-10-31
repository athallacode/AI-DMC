"""Konfigurasi pipeline. Semua nilai dibaca dari environment supaya bisa diubah tanpa mengubah kode."""

import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path(__file__).parent
TAXONOMY_PATH = CONFIG_DIR / "taxonomy.json"


def _env(name: str, default):
    """Baca env saat Settings dibuat (bukan saat modul di-import), lalu ubah ke tipe default."""
    return field(default_factory=lambda: type(default)(os.getenv(name, default)))


@dataclass(frozen=True)
class Settings:
    ollama_host: str = _env("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = _env("OLLAMA_MODEL", "gemma4:e4b")
    ollama_timeout: float = _env("OLLAMA_TIMEOUT", 180.0)
    # Jumlah pemanggilan LLM per dokumen untuk skor keyakinan (voting).
    # 1 = paling cepat, tapi skor selalu 0,5 sehingga semua dokumen masuk Kotak Verifikasi.
    jumlah_voting: int = _env("PIPELINE_VOTES", 3)
    suhu_voting: float = _env("PIPELINE_TEMPERATURE", 0.4)
    # Batas karakter teks yang dikirim ke LLM (bagian awal + akhir dokumen).
    maks_karakter: int = _env("PIPELINE_MAX_CHARS", 12000)
    # OCR
    ocr_lang: str = _env("OCR_LANG", "id")
    ocr_dpi: int = _env("OCR_DPI", 200)
    ocr_maks_halaman: int = _env("OCR_MAX_PAGES", 5)
    # Halaman PDF dengan karakter di bawah batas ini dianggap hasil scan.
    min_karakter_halaman: int = _env("PDF_MIN_CHARS_PER_PAGE", 30)


def get_settings() -> Settings:
    return Settings()
