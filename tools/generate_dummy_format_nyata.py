"""Buat dataset sintetis yang meniru format dokumen eviden nyata (SK Dekan berlampiran tabel,
berita acara sidang, daftar nilai) plus dokumen pengecoh yang mirip dari kategori lain.

Semua nama, nomor, dan instansi fiktif; tidak ada isi yang disalin dari dokumen dosen.
Jalankan dari root repo:
    python tools/generate_dummy_format_nyata.py [--per-jenis 8] [--seed 7]

Hasil di data/dummy_nyata/latih dan data/dummy_nyata/uji, masing-masing dengan labels.csv.
Data latih untuk contoh/pelatihan, data uji hanya untuk mengukur akurasi (jangan dicampur).
"""

import argparse
import csv
import io
import json
import random
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "dummy_nyata"

BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
         "September", "Oktober", "November", "Desember"]
DEPAN = ["Arif", "Lina", "Sari", "Rudi", "Dewi", "Bagus", "Rina", "Yoga", "Fitri", "Hendra", "Maya",
         "Dimas", "Nadia", "Rizky", "Putri", "Fajar", "Indah", "Galih", "Ayu", "Bima", "Citra", "Eko"]
BELAKANG = ["Nugroho", "Oktaviani", "Mulyani", "Hartono", "Lestari", "Saputra", "Wulandari", "Pratama",
            "Kurniawan", "Anggraini", "Setiawan", "Rahmawati", "Firmansyah", "Permata", "Hidayat", "Santoso"]
GELAR = ["S.T., M.T.", "S.Kom., M.Kom.", "S.T., M.Sc.", "Dr.", "S.Si., M.T.", "Ph.D."]
UNIV = ["UNIVERSITAS CONTOH NUSANTARA", "UNIVERSITAS TEKNOLOGI FIKTIF", "INSTITUT SAINS CONTOH"]
FAKULTAS = [("FAKULTAS INFORMATIKA", "IF"), ("FAKULTAS TEKNIK ELEKTRO", "TE"),
            ("FAKULTAS REKAYASA INDUSTRI", "RI"), ("FAKULTAS ILMU TERAPAN", "IT")]
PRODI = ["S1 Informatika", "S1 Teknik Komputer", "S1 Sistem Informasi", "S2 Informatika", "S1 Teknik Elektro",
         "S1 Teknik Industri", "D3 Teknologi Komputer"]
MATKUL = ["Basis Data", "Struktur Data", "Kecerdasan Buatan", "Jaringan Komputer", "Pemrograman Web",
          "Sistem Operasi", "Pembelajaran Mesin", "Rekayasa Perangkat Lunak", "Statistika", "Kalkulus",
          "Interaksi Manusia dan Komputer", "Keamanan Informasi", "Algoritma Pemrograman", "Data Mining"]
JUDUL_TA = ["Klasifikasi Citra Daun dengan CNN", "Sistem Rekomendasi Buku Berbasis Konten",
            "Deteksi Anomali Jaringan dengan Autoencoder", "Aplikasi Presensi Berbasis Pengenalan Wajah",
            "Analisis Sentimen Ulasan Aplikasi", "Optimasi Rute Kurir dengan Algoritma Genetika",
            "Chatbot Layanan Akademik", "Prediksi Kelulusan Mahasiswa dengan Random Forest"]
KEGIATAN = ["Seminar Nasional Informatika", "Dies Natalis Fakultas", "Wisuda Periode II",
            "Lomba Inovasi Mahasiswa", "Konferensi Internasional Teknologi Cerdas", "Penerimaan Mahasiswa Baru"]


def nama(r: random.Random, gelar=True) -> str:
    n = f"{r.choice(DEPAN)} {r.choice(BELAKANG)}"
    return f"{n}, {r.choice(GELAR)}" if gelar else n


def tgl(r: random.Random, tahun: int) -> tuple[str, str]:
    b, h = r.randint(1, 12), r.randint(1, 28)
    return f"{tahun}-{b:02d}-{h:02d}", f"{h} {BULAN[b - 1]} {tahun}"


def periode(r: random.Random) -> tuple[str, int]:
    t = r.choice([2024, 2025, 2026])
    sem = r.choice(["Ganjil", "Genap"])
    return f"{sem} {t}/{t + 1}", (t if sem == "Ganjil" else t + 1)


def kop(r, fak, univ):
    return f"{univ}\n{fak[0]}\nJl. Contoh Raya No. {r.randint(1, 99)}, Kota Fiktif"


def keputusan(r, judul_pejabat, kode_unit, kode, tentang, menimbang, memutuskan, tanggal_teks, ttd, univ, fak):
    no = f"{r.randint(10, 999)}/{kode}/{kode_unit}/{tanggal_teks.split()[-1]}"
    gaya = r.randint(0, 2)
    kepala = ["KEPUTUSAN", "SURAT KEPUTUSAN", "KEPUTUSAN"][gaya]
    teks = (f"{kop(r, fak, univ)}\n\n{kepala} {judul_pejabat}\nNOMOR: {no}\n\nTENTANG\n{tentang}\n\n"
            f"{judul_pejabat},\nMenimbang : a. {menimbang}\n            b. bahwa untuk itu perlu ditetapkan dengan keputusan.\n"
            f"Mengingat : 1. Statuta {univ.title()}.\n            2. Peraturan Akademik yang berlaku.\n\n"
            f"MEMUTUSKAN\nMenetapkan :\nKESATU : {memutuskan}\nKEDUA : Keputusan ini berlaku sejak tanggal ditetapkan.\n\n"
            f"Ditetapkan di Kota Fiktif\npada tanggal {tanggal_teks}\n{judul_pejabat.title()},\n\n\n{ttd}")
    return no, teks


# Setiap pembuat mengembalikan (nomor, tanggal_iso, periode, teks halaman-halaman)
def sk_mengajar(r):
    per, th = periode(r); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no, hal1 = keputusan(r, f"DEKAN {fak[0]}", f"{fak[1]}-DEK", r.choice(["AKD", "AKD6", "SDM"]),
                         f"PENUGASAN MENGAJAR DOSEN SEMESTER {per.upper()}",
                         "bahwa dalam rangka kelancaran perkuliahan perlu menetapkan beban mengajar dosen",
                         "Menugaskan dosen yang namanya tercantum dalam lampiran untuk mengajar mata kuliah sesuai lampiran.",
                         teks_t, nama(r), univ, fak)
    baris = "\n".join(f"{i}. {nama(r)}  {r.choice(MATKUL)}  {r.randint(2, 4)} SKS  Kelas {r.choice('ABCD')}{r.randint(1, 5)}"
                      for i in range(1, r.randint(8, 16)))
    lamp = f"LAMPIRAN KEPUTUSAN DEKAN\nNOMOR: {no}\nDAFTAR DOSEN PENGAMPU MATA KULIAH {r.choice(PRODI).upper()}\nSEMESTER {per.upper()}\n\nNo Nama Dosen Mata Kuliah SKS Kelas\n{baris}"
    return no, iso, per, [hal1, lamp]


def surat_tugas_mengajar(r):
    per, th = periode(r); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no = f"{r.randint(10, 300)}/ST/{fak[1]}/{th}"
    teks = (f"{kop(r, fak, univ)}\n\nSURAT TUGAS\nNomor: {no}\n\nKetua Program Studi {r.choice(PRODI)} menugaskan kepada:\n"
            f"Nama : {nama(r)}\nuntuk mengajar mata kuliah {r.choice(MATKUL)} pada Semester {per}.\n\n"
            f"Demikian surat tugas ini dibuat untuk dilaksanakan dengan penuh tanggung jawab.\n\nKota Fiktif, {teks_t}\nKetua Program Studi,\n\n{nama(r)}")
    return no, iso, per, [teks]


def daftar_nilai(r):
    per, _ = periode(r); univ = r.choice(UNIV)
    judul = r.choice(["DAFTAR NILAI AKHIR", "DAFTAR NILAI AKHIR MAHASISWA", "REKAPITULASI NILAI AKHIR", "DAFTAR PESERTA DAN NILAI AKHIR"])
    baris = "\n".join(f"{i} 13{r.randint(10, 99)}{r.randint(1000, 9999)} {nama(r, False)} {r.randint(50, 98)} {r.choice(['A', 'AB', 'B', 'BC', 'C'])}"
                      for i in range(1, r.randint(15, 35)))
    teks = (f"{univ}\n{judul}\nTahun Akademik / Semester : {per}\nMata Kuliah : {r.choice(MATKUL)}\nKelas : {r.choice(PRODI)}-{r.randint(1, 4)}\n"
            f"Dosen : {nama(r)}\n\nNo NIM Nama Mahasiswa Nilai Angka Indeks\n{baris}\n\nDicetak dari sistem informasi akademik.")
    return "", "", per, [teks]


def nilai_edom(r):
    per, _ = periode(r); univ = r.choice(UNIV)
    teks = (f"{univ}\nLAPORAN HASIL EVALUASI DOSEN OLEH MAHASISWA (EDOM)\nSemester {per}\nNama Dosen : {nama(r)}\n\n"
            + "\n".join(f"{a} {r.uniform(3.1, 3.95):.2f}" for a in ["Kesiapan mengajar", "Penguasaan materi", "Ketepatan waktu", "Kejelasan penyampaian", "Umpan balik tugas"])
            + f"\nRata-rata keseluruhan {r.uniform(3.3, 3.9):.2f}\nJumlah responden {r.randint(20, 120)} mahasiswa")
    return "", "", per, [teks]


def sk_pembimbing(r):
    per, th = periode(r); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    jenjang = r.choice(["TUGAS AKHIR", "SKRIPSI", "TESIS"])
    no, hal1 = keputusan(r, f"DEKAN {fak[0]}", f"{fak[1]}-DEK", r.choice(["TA", "AKD", "AKD6"]),
                         f"PENETAPAN DOSEN PEMBIMBING {jenjang} MAHASISWA PROGRAM STUDI {r.choice(PRODI).upper()} SEMESTER {per.upper()}",
                         f"bahwa untuk kelancaran penyusunan {jenjang.lower()} perlu ditetapkan dosen pembimbing",
                         f"Menetapkan dosen yang namanya tercantum dalam lampiran sebagai Pembimbing I dan Pembimbing II {jenjang.lower()}.",
                         teks_t, nama(r), univ, fak)
    baris = "\n".join(f"{i}. {r.randint(1300000000, 1309999999)} {nama(r, False)}  {r.choice(JUDUL_TA)}  Pembimbing I: {nama(r)}  Pembimbing II: {nama(r)}"
                      for i in range(1, r.randint(6, 14)))
    return no, iso, per, [hal1, f"LAMPIRAN KEPUTUSAN DEKAN\nNOMOR: {no}\nDAFTAR MAHASISWA DAN DOSEN PEMBIMBING\n\nNo NIM Nama Judul Pembimbing\n{baris}"]


def sk_penguji(r):
    per, th = periode(r); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    jenjang = r.choice(["TUGAS AKHIR", "SKRIPSI", "TESIS"])
    no, hal1 = keputusan(r, f"DEKAN {fak[0]}", f"{fak[1]}-DEK", r.choice(["TA", "AKD"]),
                         f"PENETAPAN DOSEN PENGUJI SIDANG {jenjang} SEMESTER {per.upper()}",
                         f"bahwa untuk pelaksanaan sidang {jenjang.lower()} perlu ditetapkan dosen penguji",
                         "Menetapkan dosen yang namanya tercantum dalam lampiran sebagai Ketua Penguji dan Anggota Penguji.",
                         teks_t, nama(r), univ, fak)
    baris = "\n".join(f"{i}. {nama(r, False)}  Penguji I: {nama(r)}  Penguji II: {nama(r)}" for i in range(1, r.randint(5, 12)))
    return no, iso, per, [hal1, f"LAMPIRAN\nNOMOR: {no}\nDAFTAR PENGUJI SIDANG\n{baris}"]


def berita_acara(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); univ = r.choice(UNIV)
    jenjang = r.choice(["TUGAS AKHIR", "SKRIPSI", "TESIS", "PROPOSAL TUGAS AKHIR"])
    hari = r.choice(["Senin", "Selasa", "Rabu", "Kamis", "Jumat"])
    teks = (f"{univ}\n{r.choice(['BERITA ACARA SIDANG', 'BERITA ACARA PELAKSANAAN SIDANG', 'LEMBAR BERITA ACARA SIDANG'])} {jenjang}\n\n"
            f"Pada hari {hari} tanggal {teks_t} telah dilaksanakan sidang {jenjang.lower()} mahasiswa:\n"
            f"Nama : {nama(r, False)}\nNIM : {r.randint(1300000000, 1309999999)}\nProgram Studi : {r.choice(PRODI)}\nJudul : {r.choice(JUDUL_TA)}\n\n"
            f"Dengan susunan penguji:\nPembimbing I : {nama(r)}\nPembimbing II : {nama(r)}\nPenguji I : {nama(r)}\nPenguji II : {nama(r)}\n\n"
            f"Hasil sidang dinyatakan: {r.choice(['LULUS', 'LULUS DENGAN REVISI', 'LULUS TANPA REVISI'])} dengan nilai {r.choice(['A', 'AB', 'B'])}.\n\n"
            "Catatan revisi:\n1. Perbaiki bab metodologi.\n2. Lengkapi daftar pustaka.\n\nTanda tangan para penguji")
    return "", iso, "", [teks]


def sk_pembina(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    ukm = r.choice(["Robotika", "Paduan Suara", "Pencak Silat", "Kewirausahaan", "Himpunan Mahasiswa Informatika"])
    no, hal1 = keputusan(r, "REKTOR", "REK", "KMS", f"PENGANGKATAN DOSEN PEMBINA UNIT KEGIATAN MAHASISWA {ukm.upper()} TAHUN {th}",
                         "bahwa kegiatan kemahasiswaan perlu dibina oleh dosen", f"Mengangkat {nama(r)} sebagai Pembina UKM {ukm}.",
                         teks_t, nama(r), univ, fak)
    return no, iso, "", [hal1]


def sk_kepanitiaan(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    keg = r.choice(KEGIATAN)
    no, hal1 = keputusan(r, f"DEKAN {fak[0]}", f"{fak[1]}-DEK", "PAN", f"PEMBENTUKAN PANITIA {keg.upper()} TAHUN {th}",
                         f"bahwa untuk kelancaran {keg} perlu dibentuk panitia",
                         "Membentuk panitia dengan susunan sebagaimana tercantum dalam lampiran.", teks_t, nama(r), univ, fak)
    baris = "\n".join(f"{jab} : {nama(r)}" for jab in ["Penanggung jawab", "Ketua", "Sekretaris", "Bendahara", "Koordinator acara", "Koordinator konsumsi", "Anggota", "Anggota"])
    return no, iso, "", [hal1, f"LAMPIRAN\nNOMOR: {no}\nSUSUNAN PANITIA {keg.upper()}\n{baris}"]


def surat_tugas_reviewer(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no = f"{r.randint(10, 200)}/ST-REV/LPPM/{th}"
    teks = (f"{kop(r, fak, univ)}\n\nSURAT TUGAS\nNomor: {no}\n\nKetua LPPM menugaskan {nama(r)} sebagai reviewer "
            f"{r.choice(['proposal hibah penelitian internal', 'artikel Jurnal Teknologi Fiktif', 'proposal pengabdian masyarakat'])} tahun {th}.\n\n"
            f"Kota Fiktif, {teks_t}\nKetua LPPM,\n\n{nama(r)}")
    return no, iso, "", [teks]


def surat_tugas_asesor(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no = f"{r.randint(10, 200)}/ST-ASR/{th}"
    teks = (f"{kop(r, fak, univ)}\n\nSURAT TUGAS\nNomor: {no}\n\nWakil Rektor menugaskan {nama(r)} sebagai asesor "
            f"{r.choice(['Beban Kerja Dosen (BKD)', 'akreditasi program studi', 'sertifikasi dosen'])} periode {th}.\n\n"
            f"Kota Fiktif, {teks_t}\nWakil Rektor,\n\n{nama(r)}")
    return no, iso, "", [teks]


def sertifikat_narasumber(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th)
    no = f"{r.randint(10, 300)}/SERT/{th}"
    teks = (f"SERTIFIKAT\nNomor: {no}\n\nDiberikan kepada\n{nama(r)}\n\nsebagai NARASUMBER\npada "
            f"{r.choice(['Webinar Keamanan Data Kampus', 'Workshop Penulisan Artikel Ilmiah', 'Pelatihan Machine Learning untuk Guru'])}\n"
            f"{teks_t}\n\nKetua Panitia,\n{nama(r)}")
    return no, iso, "", [teks]


def sk_keanggotaan_coe(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no, hal1 = keputusan(r, "REKTOR", "REK", "COE", f"PENETAPAN ANGGOTA CENTER OF EXCELLENCE KECERDASAN BUATAN TAHUN {th}",
                         "bahwa untuk pengembangan riset unggulan perlu ditetapkan anggota CoE",
                         "Menetapkan dosen yang namanya tercantum dalam lampiran sebagai anggota Center of Excellence.",
                         teks_t, nama(r), univ, fak)
    baris = "\n".join(f"{i}. {nama(r)}  {r.choice(['Ketua', 'Anggota', 'Peneliti'])}" for i in range(1, r.randint(5, 10)))
    return no, iso, "", [hal1, f"LAMPIRAN\nNOMOR: {no}\nANGGOTA CENTER OF EXCELLENCE\n{baris}"]


def sk_penelitian(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no, hal1 = keputusan(r, "KETUA LPPM", "LPPM", "PEN", f"PENETAPAN PENERIMA HIBAH PENELITIAN INTERNAL TAHUN {th}",
                         "bahwa telah dilakukan seleksi proposal penelitian",
                         "Menetapkan dosen dalam lampiran sebagai ketua peneliti penerima hibah.", teks_t, nama(r), univ, fak)
    baris = "\n".join(f"{i}. {nama(r)}  {r.choice(JUDUL_TA)}  Rp {r.randint(10, 50)}.000.000" for i in range(1, r.randint(4, 9)))
    return no, iso, "", [hal1, f"LAMPIRAN\nNOMOR: {no}\nDAFTAR PENERIMA HIBAH\n{baris}"]


def sk_abdimas(r):
    th = r.choice([2024, 2025, 2026]); iso, teks_t = tgl(r, th); fak = r.choice(FAKULTAS); univ = r.choice(UNIV)
    no, hal1 = keputusan(r, "KETUA LPPM", "LPPM", "PPM", f"PENETAPAN PELAKSANA PENGABDIAN KEPADA MASYARAKAT TAHUN {th}",
                         "bahwa kegiatan pengabdian masyarakat perlu ditetapkan pelaksananya",
                         f"Menetapkan {nama(r)} sebagai ketua pelaksana pengabdian kepada masyarakat di Desa {r.choice(['Sukamaju', 'Mekarsari', 'Cibiru'])}.",
                         teks_t, nama(r), univ, fak)
    return no, iso, "", [hal1]


PEMBUAT = {
    "SK mengajar": sk_mengajar, "Surat tugas mengajar": surat_tugas_mengajar,
    "Daftar nilai akhir": daftar_nilai, "Nilai EDOM": nilai_edom,
    "SK pembimbing TA/tesis": sk_pembimbing, "SK penguji TA/tesis": sk_penguji, "Berita acara sidang": berita_acara,
    "SK pembina kegiatan mahasiswa": sk_pembina, "SK kepanitiaan": sk_kepanitiaan,
    "Surat tugas reviewer": surat_tugas_reviewer, "Surat tugas asesor": surat_tugas_asesor,
    "Sertifikat narasumber": sertifikat_narasumber, "SK keanggotaan CoE": sk_keanggotaan_coe,
    "SK penelitian": sk_penelitian, "SK abdimas": sk_abdimas,
}


def pdf_digital(halaman: list[str]) -> pymupdf.Document:
    d = pymupdf.open()
    for teks in halaman:
        # Kecilkan huruf sampai seluruh teks muat; insert_textbox tidak menulis apa pun kalau teks kepanjangan.
        for ukuran in (10.5, 9.5, 8.5, 7.5, 6.5):
            p = d.new_page()
            if p.insert_textbox(pymupdf.Rect(45, 45, 555, 805), teks, fontsize=ukuran, fontname="helv") >= 0:
                break
            d.delete_page(-1)
        else:
            raise ValueError("teks terlalu panjang untuk satu halaman")
    return d


def pdf_scan(halaman: list[str], seed: int) -> pymupdf.Document:
    """Render tiap halaman jadi gambar abu-abu, miring sedikit, blur, dan bintik, seperti hasil pindai."""
    asal, keluar = pdf_digital(halaman), pymupdf.open()
    rng = np.random.default_rng(seed)
    for i, hal in enumerate(asal):
        img = Image.open(io.BytesIO(hal.get_pixmap(dpi=150).tobytes("png"))).convert("L")
        img = img.rotate(float(rng.uniform(-1.8, 1.8)), expand=True, fillcolor=235).filter(ImageFilter.GaussianBlur(0.6))
        arr = np.asarray(img, dtype=np.float32)
        arr = np.clip(arr * 0.92 + 8 + rng.normal(0, 10, arr.shape), 0, 255).astype(np.uint8)
        buf = io.BytesIO(); Image.fromarray(arr).save(buf, "PNG")
        keluar.new_page().insert_image(pymupdf.Rect(0, 0, 595, 842), stream=buf.getvalue())
    return keluar


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-jenis", type=int, default=8)
    ap.add_argument("--uji", type=int, default=3, help="jumlah dokumen per jenis untuk data uji")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    t = json.loads((ROOT / "pipeline" / "config" / "taxonomy.json").read_text(encoding="utf-8"))
    posisi = {j: (k["kode"], s["nama"]) for k in t["kategori"] for s in k["subkategori"] for j in s["jenis"]}
    r = random.Random(a.seed)
    label = {"latih": [], "uji": []}
    for bagian in label:
        (OUT / bagian).mkdir(parents=True, exist_ok=True)
    for jenis, buat in PEMBUAT.items():
        kategori, sub = posisi[jenis]
        for i in range(a.per_jenis):
            bagian = "uji" if i < a.uji else "latih"
            no, iso, per, halaman = buat(r)
            scan = r.random() < 0.35  # sekitar sepertiga hasil pindai, seperti data nyata
            berkas = f"{jenis.replace('/', '-').replace(' ', '_').lower()}_{i + 1:02d}{'_scan' if scan else ''}.pdf"
            (pdf_scan(halaman, a.seed * 1000 + len(label[bagian]) + i) if scan else pdf_digital(halaman)).save(OUT / bagian / berkas)
            label[bagian].append([berkas, kategori, sub, jenis, no, iso, per])
    for bagian, baris in label.items():
        with open(OUT / bagian / "labels.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["nama_berkas", "kategori", "subkategori", "jenis", "nomor_dokumen", "tanggal_terbit", "periode"])
            w.writerows(baris)
        print(f"{bagian}: {len(baris)} dokumen di {OUT / bagian}")


if __name__ == "__main__":
    main()
