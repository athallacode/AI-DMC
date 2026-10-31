"""Skema data pipeline.

- `HasilLLM`  : bentuk JSON yang diminta dari LLM, divalidasi ketat.
- `buat_output`: menyusun dict akhir sesuai kontrak 4.1 di docs/PEMBAGIAN_PERAN.md.
"""

import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

_POLA_TANGGAL = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_KOSONG = {"", "-", "null", "none", "n/a", "na", "tidak ada", "tidak ditemukan", "tidak diketahui"}


def _kosongkan(v):
    """Ubah isian 'kosong' versi LLM (string 'null', '-', dll) jadi None."""
    if isinstance(v, str):
        v = v.strip()
        if v.lower() in _KOSONG:
            return None
    return v


class DosenTerkait(BaseModel):
    nama: str
    nip: str | None = None
    peran: str | None = None

    @field_validator("nip", "peran", mode="before")
    @classmethod
    def _bersihkan(cls, v):
        return _kosongkan(v)

    @field_validator("nip")
    @classmethod
    def _nip_angka(cls, v):
        if v is None:
            return None
        angka = re.sub(r"\D", "", v)
        return angka or None


class HasilLLM(BaseModel):
    jenis: str
    judul: str | None = None
    nomor_dokumen: str | None = None
    tanggal_terbit: str | None = None
    periode: str | None = None
    dosen_terkait: list[DosenTerkait] = Field(default_factory=list)
    mitra_penerbit: str | None = None
    sumber_dana: str | None = None
    identifier: str | None = None
    ringkasan: str | None = None
    alasan_jenis: str | None = None  # hanya untuk membantu model berpikir, tidak masuk output

    @field_validator(
        "judul", "nomor_dokumen", "tanggal_terbit", "periode",
        "mitra_penerbit", "sumber_dana", "identifier", "ringkasan",
        mode="before",
    )
    @classmethod
    def _bersihkan(cls, v):
        return _kosongkan(v)

    @field_validator("tanggal_terbit")
    @classmethod
    def _tanggal_valid(cls, v):
        """Tanggal yang tidak berformat YYYY-MM-DD atau tidak valid dibuang, bukan ditebak."""
        if v is None or not _POLA_TANGGAL.match(v):
            return None
        try:
            date.fromisoformat(v)
        except ValueError:
            return None
        return v

    @field_validator("dosen_terkait", mode="before")
    @classmethod
    def _dosen_list(cls, v):
        if v is None:
            return []
        return [d for d in v if isinstance(d, dict) and _kosongkan(d.get("nama"))]


def skema_json_llm(semua_jenis: list[str]) -> dict:
    """JSON Schema untuk structured output Ollama. `jenis` dibatasi ke daftar taksonomi.

    URUTAN FIELD PENTING: model menulis JSON dari atas ke bawah. `jenis` sengaja ditaruh PALING
    AKHIR, setelah ringkasan dan alasan, supaya model memahami isi dokumen dulu sebelum memilih.
    Saat `jenis` di urutan pertama, gemma4:e4b salah mengklasifikasi SK mengajar sebagai proposal.
    """
    teks_opsional = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {
            "judul": teks_opsional,
            "nomor_dokumen": teks_opsional,
            "tanggal_terbit": {"type": ["string", "null"], "description": "Format YYYY-MM-DD"},
            "periode": teks_opsional,
            "dosen_terkait": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"nama": {"type": "string"}, "nip": teks_opsional, "peran": teks_opsional},
                    "required": ["nama", "nip", "peran"],
                },
            },
            "mitra_penerbit": teks_opsional,
            "sumber_dana": teks_opsional,
            "identifier": teks_opsional,
            "ringkasan": teks_opsional,
            "alasan_jenis": {"type": "string"},
            "jenis": {"type": "string", "enum": semua_jenis},
        },
        "required": [
            "judul", "nomor_dokumen", "tanggal_terbit", "periode", "dosen_terkait",
            "mitra_penerbit", "sumber_dana", "identifier", "ringkasan", "alasan_jenis", "jenis",
        ],
    }


def metadata_kosong() -> dict:
    return {
        "judul": None,
        "nomor_dokumen": None,
        "tanggal_terbit": None,
        "periode": None,
        "dosen_terkait": [],
        "mitra_penerbit": None,
        "sumber_dana": None,
        "identifier": None,
    }


def buat_output(
    *,
    status: str,
    jenis_berkas: str | None,
    teks: str,
    kategori: str | None = None,
    subkategori: str | None = None,
    jenis: str | None = None,
    skor_keyakinan: float = 0.0,
    metadata: dict | None = None,
    ringkasan: str | None = None,
    model_dipakai: str | None = None,
    waktu_proses_detik: float = 0.0,
    error: str | None = None,
) -> dict:
    return {
        "status": status,
        "jenis_berkas": jenis_berkas,
        "teks": teks,
        "klasifikasi": {"kategori": kategori, "subkategori": subkategori, "jenis": jenis},
        "skor_keyakinan": round(float(skor_keyakinan), 2),
        "metadata": metadata or metadata_kosong(),
        "ringkasan": ringkasan,
        "model_dipakai": model_dipakai,
        "waktu_proses_detik": round(float(waktu_proses_detik), 2),
        "error": error,
    }
