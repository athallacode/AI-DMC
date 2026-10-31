"""Evaluasi akurasi pipeline (P1-09).

Pemakaian (dari root repo):
    python -m pipeline.eval.run_eval --data data/dummy --labels data/dummy/labels.csv

labels.csv (lihat pipeline/eval/labels_template.csv):
    nama_berkas,kategori,subkategori,jenis,nomor_dokumen,tanggal_terbit,periode
Kolom metadata boleh dikosongkan kalau memang tidak ada di dokumen.

Hasil disimpan ke pipeline/eval/hasil/<waktu>/ :
    laporan.md  ringkasan akurasi + daftar dokumen yang salah
    detail.json output lengkap per dokumen (tanpa teks penuh)
"""

import argparse
import csv
import json
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from pipeline.config import get_settings
from pipeline.main import process_document

FIELD_METADATA = ["nomor_dokumen", "tanggal_terbit", "periode"]


def normalisasi(v) -> str:
    """Bandingkan tanpa peduli huruf besar, spasi ganda, dan tanda baca di ujung."""
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip().strip(".,;").lower()


def baca_label(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if r.get("nama_berkas", "").strip()]


def evaluasi(data_dir: Path, labels: list[dict], ambang: float) -> tuple[dict, list[dict]]:
    detail = []
    for i, label in enumerate(labels, 1):
        path = data_dir / label["nama_berkas"]
        print(f"[{i}/{len(labels)}] {label['nama_berkas']} ...", flush=True)
        out = process_document(str(path))
        kl = out["klasifikasi"]
        baris = {
            "nama_berkas": label["nama_berkas"],
            "status": out["status"],
            "error": out["error"],
            "jenis_berkas": out["jenis_berkas"],
            "skor": out["skor_keyakinan"],
            "waktu": out["waktu_proses_detik"],
            "label": {k: label.get(k, "") for k in ["kategori", "subkategori", "jenis", *FIELD_METADATA]},
            "prediksi": {
                "kategori": kl["kategori"],
                "subkategori": kl["subkategori"],
                "jenis": kl["jenis"],
                **{k: out["metadata"].get(k) for k in FIELD_METADATA},
            },
        }
        baris["benar"] = {
            k: normalisasi(baris["label"][k]) == normalisasi(baris["prediksi"][k])
            for k in ["kategori", "subkategori", "jenis", *FIELD_METADATA]
        }
        detail.append(baris)

    n = len(detail)
    sukses = [d for d in detail if d["status"] == "sukses"]
    akurasi = {k: sum(d["benar"][k] for d in detail) / n for k in ["kategori", "subkategori", "jenis", *FIELD_METADATA]}
    lolos = [d for d in sukses if d["skor"] >= ambang]
    ringkasan = {
        "jumlah_dokumen": n,
        "gagal": n - len(sukses),
        "akurasi": akurasi,
        "ambang": ambang,
        "persen_lolos_otomatis": len(lolos) / n if n else 0,
        "akurasi_jenis_di_antara_yang_lolos": (sum(d["benar"]["jenis"] for d in lolos) / len(lolos)) if lolos else None,
        "rata_rata_waktu_detik": sum(d["waktu"] for d in detail) / n if n else 0,
    }
    return ringkasan, detail


def tulis_laporan(ringkasan: dict, detail: list[dict], out_dir: Path, model: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "detail.json").write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")

    pct = lambda x: "-" if x is None else f"{x * 100:.1f}%"
    b = [
        f"# Laporan Evaluasi Pipeline AI-DMC",
        "",
        f"- Waktu: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Model: `{model}`",
        f"- Jumlah dokumen: {ringkasan['jumlah_dokumen']} (gagal diproses: {ringkasan['gagal']})",
        f"- Rata-rata waktu per dokumen: {ringkasan['rata_rata_waktu_detik']:.1f} detik",
        "",
        "## Akurasi",
        "",
        "| Field | Akurasi |",
        "|---|---|",
        *[f"| {k} | {pct(v)} |" for k, v in ringkasan["akurasi"].items()],
        "",
        f"## Ambang keyakinan {ringkasan['ambang']}",
        "",
        f"- Dokumen yang lolos otomatis (langsung terverifikasi): {pct(ringkasan['persen_lolos_otomatis'])}",
        f"- Akurasi jenis di antara yang lolos: {pct(ringkasan['akurasi_jenis_di_antara_yang_lolos'])}",
        "",
        "Kalau akurasi di antara yang lolos masih rendah, ambang perlu dinaikkan (P1-18).",
        "",
        "## Dokumen yang salah",
        "",
        "| Berkas | Field salah | Label | Prediksi | Skor |",
        "|---|---|---|---|---|",
    ]
    salah_per_jenis = defaultdict(int)
    for d in detail:
        field_salah = [k for k, v in d["benar"].items() if not v]
        if not field_salah:
            continue
        if not d["benar"]["jenis"]:
            salah_per_jenis[d["label"]["jenis"]] += 1
        for k in field_salah:
            b.append(f"| {d['nama_berkas']} | {k} | {d['label'][k] or '(kosong)'} | {d['prediksi'][k] or '(kosong)'} | {d['skor']} |")
        if d["error"]:
            b.append(f"| {d['nama_berkas']} | error | | {d['error']} | |")
    if salah_per_jenis:
        b += ["", "## Jenis yang paling sering salah", ""]
        b += [f"- {j}: {c} dokumen" for j, c in sorted(salah_per_jenis.items(), key=lambda x: -x[1])]
    b += ["", "## Catatan analisis (diisi manual)", "", "- Dugaan penyebab kesalahan:", "- Perbaikan yang dicoba:"]

    laporan = out_dir / "laporan.md"
    laporan.write_text("\n".join(b), encoding="utf-8")
    return laporan


def main():
    p = argparse.ArgumentParser(description="Evaluasi akurasi pipeline AI-DMC")
    p.add_argument("--data", required=True, type=Path, help="Folder berisi dokumen uji")
    p.add_argument("--labels", required=True, type=Path, help="Path labels.csv")
    p.add_argument("--ambang", type=float, default=0.85)
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "hasil")
    a = p.parse_args()

    labels = baca_label(a.labels)
    mulai = time.time()
    ringkasan, detail = evaluasi(a.data, labels, a.ambang)
    out_dir = a.out / datetime.now().strftime("%Y%m%d-%H%M%S")
    laporan = tulis_laporan(ringkasan, detail, out_dir, get_settings().ollama_model)
    print(json.dumps(ringkasan, ensure_ascii=False, indent=2))
    print(f"\nSelesai dalam {time.time() - mulai:.0f} detik. Laporan: {laporan}")


if __name__ == "__main__":
    main()
