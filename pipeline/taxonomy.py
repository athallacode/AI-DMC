"""Memuat taksonomi dan menyediakan pencarian jenis -> subkategori -> kategori."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pipeline.config import TAXONOMY_PATH


@dataclass(frozen=True)
class PosisiJenis:
    kategori: str
    subkategori: str
    jenis: str


class Taxonomy:
    def __init__(self, data: dict):
        self.data = data
        self.peta: dict[str, PosisiJenis] = {}
        for kat in data["kategori"]:
            for sub in kat["subkategori"]:
                for jenis in sub["jenis"]:
                    if jenis in self.peta:
                        raise ValueError(f"Nama jenis tidak unik di taksonomi: {jenis!r}")
                    self.peta[jenis] = PosisiJenis(kat["kode"], sub["nama"], jenis)

    @property
    def semua_jenis(self) -> list[str]:
        return list(self.peta)

    @property
    def kode_kategori(self) -> list[str]:
        return [k["kode"] for k in self.data["kategori"]]

    def cari(self, jenis: str | None) -> PosisiJenis | None:
        if not jenis:
            return None
        if jenis in self.peta:
            return self.peta[jenis]
        # toleransi beda huruf besar kecil / spasi
        norm = jenis.strip().lower()
        for nama, posisi in self.peta.items():
            if nama.lower() == norm:
                return posisi
        return None

    def sebagai_teks_prompt(self) -> str:
        """Daftar taksonomi ringkas untuk dimasukkan ke prompt."""
        baris = []
        for kat in self.data["kategori"]:
            baris.append(f"{kat['kode']} ({kat['nama']})")
            for sub in kat["subkategori"]:
                baris.append(f"  - {sub['nama']}: " + "; ".join(sub["jenis"]))
        return "\n".join(baris)


@lru_cache(maxsize=4)
def load_taxonomy(path: str | Path = TAXONOMY_PATH) -> Taxonomy:
    with open(path, encoding="utf-8") as f:
        return Taxonomy(json.load(f))
