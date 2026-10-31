"""Mock pipeline untuk Orang 2 (P1-01).

`process_document()` di sini punya tanda tangan dan bentuk output yang SAMA dengan pipeline asli
(kontrak `docs/PEMBAGIAN_PERAN.md` Bagian 4.1), tapi tidak memanggil OCR atau LLM.

Variasi output ditentukan dari nama berkas supaya bisa dites dengan sengaja:
- nama mengandung "gagal"  -> status gagal
- nama mengandung "ragu"   -> skor rendah (masuk Kotak Verifikasi)
- nama mengandung "yakin"  -> skor tinggi (langsung terverifikasi)
- selain itu               -> dipilih tetap berdasarkan hash nama berkas

Cara pakai di backend:
    from pipeline.mock import process_document
Nanti saat pipeline asli siap, cukup ganti jadi:
    from pipeline.main import process_document
"""

import hashlib
import time
from copy import deepcopy
from pathlib import Path

_SKOR_TINGGI = {
    "status": "sukses",
    "jenis_berkas": "pdf_digital",
    "teks": "KEPUTUSAN DEKAN FAKULTAS INFORMATIKA UNIVERSITAS TELKOM NOMOR 123/AKD/FIF/2026 "
    "TENTANG PENUGASAN MENGAJAR DOSEN SEMESTER GANJIL TAHUN AKADEMIK 2026/2027 ...",
    "klasifikasi": {
        "kategori": "PND",
        "subkategori": "SK mengajar dan beban kerja",
        "jenis": "SK mengajar",
    },
    "skor_keyakinan": 0.93,
    "metadata": {
        "judul": "SK Penugasan Mengajar Semester Ganjil 2026/2027",
        "nomor_dokumen": "123/AKD/FIF/2026",
        "tanggal_terbit": "2026-08-15",
        "periode": "Ganjil 2026/2027",
        "dosen_terkait": [{"nama": "Dosen Contoh", "nip": None, "peran": "Pengajar"}],
        "mitra_penerbit": None,
        "sumber_dana": None,
        "identifier": None,
    },
    "ringkasan": "SK penugasan mengajar dosen untuk semester ganjil 2026/2027.",
    "model_dipakai": "mock",
    "waktu_proses_detik": 0.0,
    "error": None,
}

_SKOR_RENDAH = {
    "status": "sukses",
    "jenis_berkas": "gambar",
    "teks": "SERTIFIKAT diberikan kepada ... sebagai narasumber pada kegiatan pelatihan ...",
    "klasifikasi": {
        "kategori": "PNJ",
        "subkategori": "Narasumber dan penugasan",
        "jenis": "Sertifikat narasumber",
    },
    "skor_keyakinan": 0.67,
    "metadata": {
        "judul": "Sertifikat Narasumber Pelatihan Literasi Digital",
        "nomor_dokumen": None,
        "tanggal_terbit": "2026-05-20",
        "periode": None,
        "dosen_terkait": [{"nama": "Dosen Contoh", "nip": None, "peran": "Narasumber"}],
        "mitra_penerbit": "Desa Contoh",
        "sumber_dana": None,
        "identifier": None,
    },
    "ringkasan": "Sertifikat narasumber kegiatan pelatihan. Bisa juga termasuk luaran abdimas.",
    "model_dipakai": "mock",
    "waktu_proses_detik": 0.0,
    "error": None,
}

_GAGAL = {
    "status": "gagal",
    "jenis_berkas": "pdf_scan",
    "teks": "",
    "klasifikasi": {"kategori": None, "subkategori": None, "jenis": None},
    "skor_keyakinan": 0.0,
    "metadata": {
        "judul": None,
        "nomor_dokumen": None,
        "tanggal_terbit": None,
        "periode": None,
        "dosen_terkait": [],
        "mitra_penerbit": None,
        "sumber_dana": None,
        "identifier": None,
    },
    "ringkasan": None,
    "model_dipakai": "mock",
    "waktu_proses_detik": 0.0,
    "error": "Teks dokumen tidak terbaca (mock).",
}


def process_document(file_path: str, jeda_detik: float = 0.0) -> dict:
    """Kembalikan hasil palsu sesuai kontrak. `jeda_detik` bisa diisi untuk meniru waktu proses."""
    nama = Path(file_path).name.lower()
    if "gagal" in nama:
        hasil = _GAGAL
    elif "ragu" in nama:
        hasil = _SKOR_RENDAH
    elif "yakin" in nama:
        hasil = _SKOR_TINGGI
    else:
        pilihan = int(hashlib.sha256(nama.encode()).hexdigest(), 16) % 3
        hasil = (_SKOR_TINGGI, _SKOR_RENDAH, _GAGAL)[pilihan]

    if jeda_detik:
        time.sleep(jeda_detik)
    keluaran = deepcopy(hasil)
    keluaran["waktu_proses_detik"] = round(jeda_detik, 2)
    return keluaran
