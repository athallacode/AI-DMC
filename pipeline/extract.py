"""Deteksi jenis berkas dan ekstraksi teks (P1-05).

- PDF digital  -> teks diambil langsung dengan PyMuPDF.
- PDF scan     -> halaman yang teksnya hampir kosong dirender jadi gambar lalu di-OCR.
- DOCX         -> paragraf dan isi tabel dengan python-docx.
- Gambar       -> langsung di-OCR.
"""

from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import Settings, get_settings

EKSTENSI_PDF = {".pdf"}
EKSTENSI_DOCX = {".docx"}
EKSTENSI_GAMBAR = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


class BerkasTidakDidukung(Exception):
    pass


@dataclass
class HasilEkstraksi:
    teks: str
    jenis_berkas: str  # pdf_digital | pdf_scan | docx | gambar
    jumlah_halaman: int = 1
    halaman_di_ocr: list[int] = field(default_factory=list)
    catatan: list[str] = field(default_factory=list)


def deteksi_jenis(path: Path) -> str:
    """Tentukan jenis dasar dari isi berkas (magic bytes), ekstensi hanya sebagai cadangan."""
    with open(path, "rb") as f:
        kepala = f.read(8)
    if kepala.startswith(b"%PDF"):
        return "pdf"
    if kepala.startswith(b"PK"):  # DOCX adalah arsip ZIP
        return "docx" if path.suffix.lower() in EKSTENSI_DOCX else "zip"
    if kepala.startswith(b"\xff\xd8") or kepala.startswith(b"\x89PNG") or path.suffix.lower() in EKSTENSI_GAMBAR:
        return "gambar"
    raise BerkasTidakDidukung(
        f"Format berkas '{path.suffix or 'tanpa ekstensi'}' tidak didukung. Gunakan PDF, DOCX, JPG, atau PNG."
    )


def _rapikan(teks: str) -> str:
    baris = [b.strip() for b in teks.replace("\x00", "").splitlines()]
    hasil, kosong = [], 0
    for b in baris:
        if not b:
            kosong += 1
            if kosong > 1:
                continue
        else:
            kosong = 0
        hasil.append(b)
    return "\n".join(hasil).strip()


def ekstrak_docx(path: Path) -> HasilEkstraksi:
    import docx  # python-docx

    from docx.table import Table
    from docx.text.paragraph import Paragraph

    dokumen = docx.Document(str(path))
    bagian: list[str] = []
    # Baca paragraf dan tabel sesuai URUTAN ASLI di dokumen. Tabel identitas (mata kuliah,
    # semester, dosen) biasanya tepat di bawah judul, jadi jangan dipindah ke akhir teks.
    for elemen in dokumen.element.body.iterchildren():
        tag = elemen.tag.rsplit("}", 1)[-1]
        if tag == "p":
            bagian.append(Paragraph(elemen, dokumen).text)
        elif tag == "tbl":
            for baris in Table(elemen, dokumen).rows:
                sel = []
                for c in baris.cells:
                    t = c.text.strip()
                    if t and (not sel or sel[-1] != t):  # sel gabungan muncul berulang
                        sel.append(t)
                if sel:
                    bagian.append(" | ".join(sel))
    return HasilEkstraksi(teks=_rapikan("\n".join(bagian)), jenis_berkas="docx")


def ekstrak_pdf(path: Path, settings: Settings, ocr_fn=None) -> HasilEkstraksi:
    import pymupdf as fitz

    teks_halaman: list[str] = []
    perlu_ocr: list[int] = []
    with fitz.open(str(path)) as pdf:
        if pdf.needs_pass:
            raise BerkasTidakDidukung("PDF terkunci kata sandi. Buka kuncinya dulu lalu unggah ulang.")
        jumlah = pdf.page_count
        for i, halaman in enumerate(pdf):
            t = halaman.get_text("text") or ""
            teks_halaman.append(t)
            if len(t.strip()) < settings.min_karakter_halaman:
                perlu_ocr.append(i)

        catatan = []
        di_ocr: list[int] = []
        if perlu_ocr:
            if ocr_fn is None:
                from pipeline.ocr import ocr_gambar_bytes as ocr_fn
            target = perlu_ocr[: settings.ocr_maks_halaman]
            if len(perlu_ocr) > len(target):
                catatan.append(
                    f"Hanya {len(target)} dari {len(perlu_ocr)} halaman scan yang di-OCR (batas OCR_MAX_PAGES)."
                )
            for i in target:
                pix = pdf[i].get_pixmap(dpi=settings.ocr_dpi)
                teks_halaman[i] = ocr_fn(pix.tobytes("png"), settings)
                di_ocr.append(i)

    # Dianggap scan kalau lebih dari separuh halaman tidak punya lapisan teks
    jenis = "pdf_scan" if len(perlu_ocr) > jumlah / 2 else "pdf_digital"
    gabungan = "\n\n".join(f"[Halaman {i + 1}]\n{t.strip()}" for i, t in enumerate(teks_halaman) if t.strip())
    return HasilEkstraksi(
        teks=_rapikan(gabungan),
        jenis_berkas=jenis,
        jumlah_halaman=jumlah,
        halaman_di_ocr=di_ocr,
        catatan=catatan,
    )


def ekstrak_gambar(path: Path, settings: Settings, ocr_fn=None) -> HasilEkstraksi:
    if ocr_fn is None:
        from pipeline.ocr import ocr_gambar_bytes as ocr_fn
    teks = ocr_fn(path.read_bytes(), settings)
    return HasilEkstraksi(teks=_rapikan(teks), jenis_berkas="gambar", halaman_di_ocr=[0])


def ekstrak_teks(file_path: str | Path, settings: Settings | None = None, ocr_fn=None) -> HasilEkstraksi:
    """Titik masuk ekstraksi. `ocr_fn(bytes_gambar, settings) -> str` bisa diganti untuk pengujian."""
    settings = settings or get_settings()
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Berkas tidak ditemukan: {path}")

    jenis = deteksi_jenis(path)
    if jenis == "pdf":
        return ekstrak_pdf(path, settings, ocr_fn)
    if jenis == "docx":
        return ekstrak_docx(path)
    if jenis == "gambar":
        return ekstrak_gambar(path, settings, ocr_fn)
    raise BerkasTidakDidukung("Format berkas tidak didukung. Gunakan PDF, DOCX, JPG, atau PNG.")
