from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=1000)


class LecturerInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nama: str = Field(min_length=1, max_length=300)
    nip: str | None = Field(default=None, max_length=100)
    peran: str | None = Field(default=None, max_length=200)


class CorrectionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kategori: Literal['PND', 'PNL', 'PKM', 'PUB', 'PNJ', 'ADM', 'LAINNYA'] | None = None
    subkategori: str | None = Field(default=None, max_length=300)
    jenis: str | None = Field(default=None, max_length=300)
    judul: str | None = Field(default=None, max_length=2000)
    nomor_dokumen: str | None = Field(default=None, max_length=500)
    tanggal_terbit: date | None = None
    periode: str | None = Field(default=None, max_length=300)
    metadata_lain: dict | None = None
    dosen_terkait: list[LecturerInput] | None = Field(default=None, max_length=200)


class PipelineMetadata(BaseModel):
    judul: str | None = None
    nomor_dokumen: str | None = None
    tanggal_terbit: date | None = None
    periode: str | None = None
    dosen_terkait: list[LecturerInput] = Field(default_factory=list)
    mitra_penerbit: str | None = None
    sumber_dana: str | None = None
    identifier: str | None = None


class Classification(BaseModel):
    kategori: Literal['PND', 'PNL', 'PKM', 'PUB', 'PNJ', 'ADM', 'LAINNYA']
    subkategori: str
    jenis: str


class PipelineResult(BaseModel):
    status: Literal['sukses', 'gagal']
    jenis_berkas: Literal['pdf_digital', 'pdf_scan', 'docx', 'gambar'] | None = None
    teks: str | None = None
    klasifikasi: Classification | None = None
    skor_keyakinan: float | None = Field(default=None, ge=0, le=1)
    metadata: PipelineMetadata | None = None
    ringkasan: str | None = None
    model_dipakai: str | None = None
    waktu_proses_detik: float | None = Field(default=None, ge=0)
    error: str | None = None

    @model_validator(mode='before')
    @classmethod
    def normalize_failed_classification(cls, value):
        if isinstance(value, dict) and value.get('status') == 'gagal' and value.get('klasifikasi') == {'kategori': None, 'subkategori': None, 'jenis': None}:
            return {**value, 'klasifikasi': None}
        return value

    @model_validator(mode='after')
    def complete_success(self):
        if self.status == 'sukses' and any(v is None for v in (self.jenis_berkas, self.klasifikasi, self.skor_keyakinan, self.metadata)):
            raise ValueError('Hasil sukses pipeline tidak lengkap')
        return self
