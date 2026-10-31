"""Klasifikasi jenis dokumen + ekstraksi metadata dengan LLM lokal (P1-07, P1-10 awal, P1-11, P1-12).

Alur:
1. Teks dipotong (bagian awal + akhir) kalau terlalu panjang.
2. LLM dipanggil N kali (voting). Panggilan pertama suhu 0, sisanya suhu `PIPELINE_TEMPERATURE`.
3. LLM hanya memilih `jenis`; subkategori dan kategori DITURUNKAN dari taksonomi,
   jadi kategori tidak mungkin keluar dari daftar.
4. Skor keyakinan = proporsi panggilan yang memilih jenis mayoritas.
"""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from pipeline.config import Settings
from pipeline.llm import KlienLLM, LLMError
from pipeline.schemas import HasilLLM, skema_json_llm
from pipeline.taxonomy import Taxonomy

PROMPT_DIR = Path(__file__).parent / "prompts"
MAKS_PERCOBAAN = 3  # 1 kali + retry 2 kali kalau JSON rusak


@dataclass
class HasilKlasifikasi:
    kategori: str
    subkategori: str
    jenis: str
    skor_keyakinan: float
    metadata: dict
    ringkasan: str | None
    suara: dict = field(default_factory=dict)  # jenis -> jumlah suara, untuk debugging
    catatan: list[str] = field(default_factory=list)


class KlasifikasiGagal(Exception):
    pass


def potong_teks(teks: str, maks: int) -> tuple[str, bool]:
    """Ambil 2/3 awal + 1/3 akhir. Kop, judul, dan 'MENETAPKAN' biasanya di awal; tanda tangan di akhir."""
    if len(teks) <= maks:
        return teks, False
    awal = int(maks * 2 / 3)
    akhir = maks - awal
    return teks[:awal] + "\n\n[... bagian tengah dokumen dipotong ...]\n\n" + teks[-akhir:], True


def bungkus_dokumen(teks: str) -> str:
    """Bungkus teks dengan tag pembatas. Tag penutup di dalam teks dinetralkan (anti prompt injection)."""
    aman = teks.replace("</dokumen>", "</ dokumen>").replace("<dokumen>", "< dokumen>")
    return f"<dokumen>\n{aman}\n</dokumen>"


def susun_prompt(teks: str, taksonomi: Taxonomy, settings: Settings) -> tuple[str, str, bool]:
    templat = (PROMPT_DIR / "klasifikasi_system.md").read_text(encoding="utf-8")
    system = templat.replace("{taksonomi}", taksonomi.sebagai_teks_prompt())
    terpotong_teks, terpotong = potong_teks(teks, settings.maks_karakter)
    user = "Tentukan jenis dan ekstrak metadata dokumen berikut.\n\n" + bungkus_dokumen(terpotong_teks)
    return system, user, terpotong


def _satu_panggilan(klien: KlienLLM, system: str, user: str, schema: dict, suhu: float) -> HasilLLM:
    galat_terakhir = None
    for _ in range(MAKS_PERCOBAAN):
        try:
            mentah = klien.chat_json(system, user, schema, suhu)
            return HasilLLM.model_validate(json.loads(mentah))
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            galat_terakhir = e
    raise KlasifikasiGagal(f"Output LLM tidak valid setelah {MAKS_PERCOBAAN} percobaan: {galat_terakhir}")


def klasifikasi(teks: str, klien: KlienLLM, taksonomi: Taxonomy, settings: Settings) -> HasilKlasifikasi:
    system, user, terpotong = susun_prompt(teks, taksonomi, settings)
    schema = skema_json_llm(taksonomi.semua_jenis)
    n = max(1, settings.jumlah_voting)

    hasil: list[HasilLLM] = []
    galat: list[str] = []
    for i in range(n):
        suhu = 0.0 if i == 0 else settings.suhu_voting
        try:
            hasil.append(_satu_panggilan(klien, system, user, schema, suhu))
        except KlasifikasiGagal as e:
            galat.append(str(e))
        except LLMError:
            raise  # Ollama mati / tidak terjangkau: biar ditangani main.py

    if not hasil:
        raise KlasifikasiGagal(galat[0] if galat else "LLM tidak memberi hasil.")

    # jenis yang tidak dikenal taksonomi diperlakukan sebagai "Lainnya"
    def jenis_valid(h: HasilLLM) -> str:
        posisi = taksonomi.cari(h.jenis)
        return posisi.jenis if posisi else "Lainnya"

    suara = Counter(jenis_valid(h) for h in hasil)
    jenis_menang, jumlah_menang = suara.most_common(1)[0]
    posisi = taksonomi.cari(jenis_menang)

    catatan: list[str] = []
    if n == 1:
        skor = 0.5
        catatan.append("Voting 1 kali: skor diset 0,5 supaya dokumen tetap dicek dosen.")
    else:
        skor = jumlah_menang / n  # panggilan gagal dihitung sebagai tidak setuju

    if jenis_menang == "Lainnya":
        skor = min(skor, 0.5)
        catatan.append("Jenis tidak cocok dengan taksonomi.")
    if len(teks.strip()) < 80:
        skor = min(skor, 0.6)
        catatan.append("Teks dokumen sangat pendek, hasil kurang bisa dipercaya.")
    if terpotong:
        catatan.append("Teks dipotong sebelum dikirim ke LLM (dokumen panjang).")
    if galat:
        catatan.append(f"{len(galat)} dari {n} panggilan LLM gagal.")

    # metadata diambil dari panggilan pertama yang memilih jenis pemenang (panggilan suhu 0 diutamakan)
    terpilih = next(h for h in hasil if jenis_valid(h) == jenis_menang)
    metadata = {
        "judul": terpilih.judul,
        "nomor_dokumen": terpilih.nomor_dokumen,
        "tanggal_terbit": terpilih.tanggal_terbit,
        "periode": terpilih.periode,
        "dosen_terkait": [d.model_dump() for d in terpilih.dosen_terkait[:10]],
        "mitra_penerbit": terpilih.mitra_penerbit,
        "sumber_dana": terpilih.sumber_dana,
        "identifier": terpilih.identifier,
    }

    return HasilKlasifikasi(
        kategori=posisi.kategori,
        subkategori=posisi.subkategori,
        jenis=posisi.jenis,
        skor_keyakinan=round(skor, 2),
        metadata=metadata,
        ringkasan=terpilih.ringkasan,
        suara=dict(suara),
        catatan=catatan,
    )
