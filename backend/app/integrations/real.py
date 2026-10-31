"""Penghubung konfigurasi aplikasi ke snapshot pipeline Orang 1."""
from ..config import get_settings


def process_document(file_path: str) -> dict:
    from pipeline.config import Settings
    from pipeline.main import process_document as run_pipeline

    app = get_settings()
    settings = Settings(
        ollama_host=app.ollama_host, ollama_model=app.ollama_model,
        ollama_timeout=app.ollama_timeout, jumlah_voting=app.pipeline_votes,
        suhu_voting=app.pipeline_temperature, maks_karakter=app.pipeline_max_chars,
        ocr_lang=app.ocr_lang, ocr_dpi=app.ocr_dpi,
        ocr_maks_halaman=app.ocr_max_pages,
        min_karakter_halaman=app.pdf_min_chars_per_page,
    )
    return run_pipeline(file_path, settings=settings)
