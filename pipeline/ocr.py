"""OCR dengan PaddleOCR (P1-06).

PaddleOCR di-import hanya saat dibutuhkan, karena berat dan butuh framework PaddlePaddle.
Model dimuat sekali lalu dipakai ulang.

API PaddleOCR 3.x (`.predict()`, hasil berisi `rec_texts`) dan 2.x (`.ocr()`, hasil list)
sama-sama ditangani.

Catatan Windows: di PaddlePaddle 3.3 + PP-OCRv6, akselerasi CPU oneDNN (MKLDNN) memicu
`NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support ...`. Karena itu oneDNN
dimatikan secara default (OCR_ENABLE_MKLDNN=0). Nyalakan hanya kalau sudah dites jalan.
"""

import io
import os
import threading

from pipeline.config import Settings

_model = None
_kunci = threading.Lock()


class OcrTidakTersedia(Exception):
    pass


def _mkldnn_aktif() -> bool:
    return os.getenv("OCR_ENABLE_MKLDNN", "0").strip().lower() in {"1", "true", "ya", "yes"}


def _muat_model(settings: Settings):
    global _model
    with _kunci:
        if _model is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as e:
                raise OcrTidakTersedia(
                    "PaddleOCR belum terpasang. Jalankan: pip install paddlepaddle paddleocr"
                ) from e
            try:
                _model = _buat_model(PaddleOCR, settings.ocr_lang)
            except Exception as e:
                if settings.ocr_lang != "latin":
                    # bahasa tidak dikenali versi PaddleOCR ini: pakai model huruf Latin
                    try:
                        _model = _buat_model(PaddleOCR, "latin")
                    except Exception:
                        pass
                if _model is None:
                    raise OcrTidakTersedia(
                        "Model PaddleOCR gagal dimuat. Saat pertama dipakai, PaddleOCR perlu internet untuk "
                        f"mengunduh model (HuggingFace / ModelScope / BOS). Detail: {str(e)[:200]}"
                    ) from e
    return _model


def _buat_model(PaddleOCR, lang: str):
    mkldnn = _mkldnn_aktif()
    try:  # PaddleOCR 3.x
        return PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=True,  # SK sering ter-scan miring / terbalik
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=mkldnn,
        )
    except TypeError:  # PaddleOCR 2.x
        return PaddleOCR(lang=lang, use_angle_cls=True, show_log=False, enable_mkldnn=mkldnn)


def _ke_array(gambar_bytes: bytes):
    import numpy as np
    from PIL import Image, ImageOps

    img = Image.open(io.BytesIO(gambar_bytes))
    img = ImageOps.exif_transpose(img).convert("RGB")  # foto HP sering punya rotasi EXIF
    # perkecil gambar yang terlalu besar (foto kamera 12MP) supaya OCR tidak lambat
    maks = 2500
    if max(img.size) > maks:
        img.thumbnail((maks, maks))
    return np.array(img)[:, :, ::-1]  # RGB -> BGR seperti format OpenCV


def _ambil_teks(hasil) -> list[str]:
    baris: list[str] = []
    for item in hasil or []:
        if item is None:
            continue
        # PaddleOCR 3.x: objek mirip dict dengan kunci rec_texts
        teks = None
        try:
            teks = item["rec_texts"]
        except (TypeError, KeyError, IndexError):
            teks = getattr(item, "rec_texts", None)
        if teks is not None:
            baris.extend(str(t) for t in teks)
            continue
        # PaddleOCR 2.x: [[kotak, (teks, skor)], ...]
        if isinstance(item, list):
            for det in item:
                try:
                    baris.append(str(det[1][0]))
                except (TypeError, IndexError):
                    pass
    return baris


def ocr_gambar_bytes(gambar_bytes: bytes, settings: Settings) -> str:
    model = _muat_model(settings)
    arr = _ke_array(gambar_bytes)
    try:
        if hasattr(model, "predict"):
            hasil = model.predict(arr)
        else:
            hasil = model.ocr(arr, cls=True)
    except Exception as e:
        saran = ""
        if "onednn" in str(e).lower() or "mkldnn" in str(e).lower() or "PirAttribute" in str(e):
            saran = " Coba set OCR_ENABLE_MKLDNN=0."
        raise OcrTidakTersedia(f"PaddleOCR gagal membaca gambar: {type(e).__name__}: {str(e)[:200]}.{saran}") from e
    return "\n".join(_ambil_teks(hasil))
