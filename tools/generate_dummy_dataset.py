"""Buat dataset uji sintetis berlabel di data/dummy untuk pipeline/eval/run_eval.py.

Semua nama, nomor, dan instansi fiktif. Jalankan dari root repo:
    python tools/generate_dummy_dataset.py

Format: pdf (digital), docx, foto (png miring + blur + bintik), scan (pdf berisi gambar saja).
"""

import csv
import io
import json
from pathlib import Path

import docx
import numpy as np
import pymupdf
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "dummy"
UNIV = "UNIVERSITAS CONTOH NUSANTARA"

# (nama, format, jenis, nomor_dokumen, tanggal_terbit, periode, teks)
DOKUMEN = [
    ("sk_mengajar", "pdf", "SK mengajar", "101/AKD/FIF/2026", "2026-08-14", "Ganjil 2026/2027",
     f"KEPUTUSAN DEKAN FAKULTAS INFORMATIKA\n{UNIV}\nNOMOR: 101/AKD/FIF/2026\n\nTENTANG\nPENUGASAN MENGAJAR DOSEN SEMESTER GANJIL TAHUN AKADEMIK 2026/2027\n\nMenimbang: bahwa perlu menetapkan beban mengajar dosen.\nMEMUTUSKAN\nMENETAPKAN: Menugaskan Arif Nugroho, M.Kom. mengajar mata kuliah Basis Data dan Struktur Data.\n\nDitetapkan di Bandung pada tanggal 14 Agustus 2026\nDekan, Hendra Kusuma"),
    ("surat_tugas_mengajar", "docx", "Surat tugas mengajar", "55/ST/AKD/2026", "2026-02-02", "Genap 2025/2026",
     "SURAT TUGAS\nNomor: 55/ST/AKD/2026\n\nKetua Program Studi Informatika menugaskan kepada:\nNama: Lina Oktaviani, M.T.\nuntuk mengajar mata kuliah Jaringan Komputer kelas IF-3A pada Semester Genap 2025/2026.\n\nDemikian surat tugas ini dibuat untuk dilaksanakan.\nBandung, 2 Februari 2026"),
    ("rps_basis_data", "docx", "RPS", "", "", "Ganjil 2026/2027",
     "RENCANA PEMBELAJARAN SEMESTER\nMata Kuliah: Basis Data\nKode: IF2201, 3 SKS\nSemester: Ganjil 2026/2027\nDosen Pengampu: Arif Nugroho\n\nCPL: mampu merancang sistem informasi.\nCPMK: mahasiswa mampu merancang skema relasional.\nMinggu 1: pengantar basis data. Minggu 2: model ER. Minggu 3: normalisasi. Minggu 4: SQL dasar."),
    ("kontrak_kuliah", "pdf", "Kontrak perkuliahan", "", "", "Ganjil 2026/2027",
     "KONTRAK PERKULIAHAN\nMata Kuliah: Kecerdasan Buatan\nSemester Ganjil 2026/2027\nDosen: Sari Mulyani\n\nDosen dan mahasiswa menyepakati hal berikut:\n1. Kehadiran minimal 75 persen.\n2. Keterlambatan lebih dari 15 menit dihitung tidak hadir.\n3. Tugas dikumpulkan tepat waktu melalui LMS.\nKesepakatan ini berlaku selama satu semester."),
    ("rubrik_tugas", "docx", "Rubrik penilaian", "", "", "",
     "RUBRIK PENILAIAN TUGAS BESAR\nMata Kuliah: Rekayasa Perangkat Lunak\n\nKriteria dan bobot:\nKelengkapan fitur: 40 persen. Sangat baik 4, baik 3, cukup 2, kurang 1.\nKualitas kode: 30 persen.\nPresentasi: 20 persen.\nDokumentasi: 10 persen."),
    ("daftar_nilai", "pdf", "Daftar nilai akhir", "", "", "Genap 2025/2026",
     "DAFTAR NILAI AKHIR MAHASISWA\nMata Kuliah: Struktur Data, Kelas IF-2B\nSemester Genap 2025/2026\n\nNIM Nama Nilai Angka Nilai Huruf\n1301001 Bagas Pratama 85 A\n1301002 Cindy Rahma 72 B\n1301003 Dimas Yoga 64 C\n1301004 Elsa Fitri 90 A\n\nDosen Pengampu: Lina Oktaviani"),
    ("edom", "pdf", "Nilai EDOM", "", "", "Ganjil 2025/2026",
     "LAPORAN EVALUASI DOSEN OLEH MAHASISWA (EDOM)\nSemester Ganjil 2025/2026\nNama Dosen: Sari Mulyani\n\nAspek penilaian dan skor rata-rata (skala 4):\nPenguasaan materi 3,72\nKetepatan waktu 3,65\nKejelasan penyampaian 3,58\nSkor rata-rata keseluruhan 3,65\nJumlah responden: 48 mahasiswa"),
    ("sk_pembimbing", "scan", "SK pembimbing TA/tesis", "210/TA/FIF/2026", "2026-03-09", "Genap 2025/2026",
     f"KEPUTUSAN DEKAN FAKULTAS INFORMATIKA\n{UNIV}\nNOMOR: 210/TA/FIF/2026\n\nTENTANG\nPENETAPAN DOSEN PEMBIMBING TUGAS AKHIR MAHASISWA SEMESTER GENAP 2025/2026\n\nMEMUTUSKAN\nMENETAPKAN: Arif Nugroho sebagai Pembimbing I dan Sari Mulyani sebagai Pembimbing II tugas akhir mahasiswa Bagas Pratama.\n\nDitetapkan di Bandung pada tanggal 9 Maret 2026\nDekan, Hendra Kusuma"),
    ("sk_penguji", "pdf", "SK penguji TA/tesis", "244/TA/FIF/2026", "2026-06-11", "Genap 2025/2026",
     f"KEPUTUSAN DEKAN FAKULTAS INFORMATIKA\n{UNIV}\nNOMOR: 244/TA/FIF/2026\n\nTENTANG\nPENETAPAN DOSEN PENGUJI SIDANG TUGAS AKHIR SEMESTER GENAP 2025/2026\n\nMEMUTUSKAN\nMENETAPKAN: Lina Oktaviani sebagai Ketua Penguji dan Rudi Hartono sebagai Anggota Penguji.\n\nDitetapkan di Bandung pada tanggal 11 Juni 2026\nDekan, Hendra Kusuma"),
    ("berita_acara_sidang", "foto", "Berita acara sidang", "", "2026-06-20", "",
     "BERITA ACARA SIDANG TUGAS AKHIR\n\nPada hari Sabtu tanggal 20 Juni 2026 telah dilaksanakan sidang tugas akhir mahasiswa:\nNama: Cindy Rahma, NIM 1301002\nJudul: Klasifikasi Citra Daun dengan CNN\nHasil sidang: LULUS dengan nilai A\n\nKetua Penguji: Lina Oktaviani\nAnggota Penguji: Rudi Hartono"),
    ("bahan_ajar", "pdf", "Bahan ajar", "", "", "",
     "MODUL PRAKTIKUM DAN SLIDE KULIAH\nPertemuan 3: Pohon Biner\nDisusun oleh Arif Nugroho untuk mata kuliah Struktur Data\n\nTujuan pembelajaran: mahasiswa memahami traversal pohon.\nMateri: definisi pohon biner, preorder, inorder, postorder.\nLatihan: buat fungsi traversal rekursif.\nBacaan tambahan: bab 5 buku referensi."),
    ("sk_pembina", "pdf", "SK pembina kegiatan mahasiswa", "88/KMS/2026", "2026-01-15", "",
     f"KEPUTUSAN REKTOR {UNIV}\nNOMOR: 88/KMS/2026\n\nTENTANG\nPENGANGKATAN DOSEN PEMBINA UNIT KEGIATAN MAHASISWA ROBOTIKA\n\nMEMUTUSKAN\nMENETAPKAN: Rudi Hartono sebagai Pembina Unit Kegiatan Mahasiswa Robotika.\n\nDitetapkan di Bandung pada tanggal 15 Januari 2026\nRektor, Bambang Setiawan"),
    ("sk_penelitian", "pdf", "SK penelitian", "301/LPPM/2026", "2026-03-02", "",
     f"KEPUTUSAN KETUA LPPM {UNIV}\nNOMOR: 301/LPPM/2026\n\nTENTANG\nPENETAPAN PENERIMA HIBAH PENELITIAN INTERNAL TAHUN 2026\n\nMEMUTUSKAN\nMENETAPKAN: Sari Mulyani sebagai ketua peneliti hibah penelitian berjudul Deteksi Hoaks Berbahasa Indonesia.\n\nDitetapkan di Bandung pada tanggal 2 Maret 2026\nKetua LPPM, Yuni Astuti"),
    ("kontrak_hibah", "scan", "Kontrak hibah penelitian", "45/KTR-PEN/2026", "2026-03-16", "",
     "KONTRAK PELAKSANAAN HIBAH PENELITIAN\nNomor: 45/KTR-PEN/2026\n\nPada tanggal 16 Maret 2026, PIHAK PERTAMA Yuni Astuti selaku Ketua LPPM dan PIHAK KEDUA Sari Mulyani selaku ketua peneliti sepakat melaksanakan penelitian dengan dana Rp 30.000.000.\nPasal 1: Pihak kedua wajib menyerahkan laporan akhir.\nPasal 2: Dana dibayarkan dalam dua tahap."),
    ("surat_tugas_penelitian", "pdf", "Surat tugas penelitian", "12/ST-LPPM/2026", "2026-04-06", "",
     "SURAT TUGAS\nNomor: 12/ST-LPPM/2026\n\nKetua LPPM menugaskan Rudi Hartono untuk melakukan pengambilan data penelitian ke Laboratorium Sensor di Yogyakarta pada 13 sampai 15 April 2026 dalam rangka penelitian Pemantauan Kualitas Udara.\n\nBandung, 6 April 2026\nKetua LPPM, Yuni Astuti"),
    ("proposal_penelitian", "docx", "Proposal penelitian", "", "", "",
     "USULAN PENELITIAN HIBAH INTERNAL\nJudul: Model Bahasa Ringan untuk Klasifikasi Dokumen Akademik\nTim Pengusul: Sari Mulyani (ketua), Arif Nugroho (anggota)\nSkema: Penelitian Dasar\n\nLatar belakang: arsip dokumen akademik terus bertambah.\nMetode: eksperimen pada korpus dokumen.\nRencana anggaran biaya: Rp 25.000.000 untuk bahan, perjalanan, dan publikasi."),
    ("laporan_kemajuan", "pdf", "Laporan kemajuan penelitian", "", "", "",
     "LAPORAN KEMAJUAN PENELITIAN\nJudul: Deteksi Hoaks Berbahasa Indonesia\nKetua Peneliti: Sari Mulyani\n\nCapaian sampai bulan ke-6: pengumpulan data selesai 80 persen, model awal sudah dilatih.\nKendala: anotasi data lebih lama dari rencana.\nRencana semester berikutnya: menyelesaikan evaluasi dan menulis artikel."),
    ("laporan_akhir_penelitian", "pdf", "Laporan akhir penelitian", "", "", "",
     "LAPORAN AKHIR PENELITIAN\nJudul: Pemantauan Kualitas Udara Berbasis Sensor Murah\nKetua Peneliti: Rudi Hartono\n\nRingkasan: penelitian telah selesai dilaksanakan sesuai kontrak.\nHasil: kalibrasi sensor menurunkan galat 35 persen.\nKesimpulan: sensor murah layak untuk pemantauan kota.\nLuaran: satu artikel jurnal dan satu prototipe."),
    ("pks_riset", "pdf", "Perjanjian kerja sama riset", "PKS/77/2026", "2026-05-18", "",
     f"PERJANJIAN KERJA SAMA RISET\nANTARA {UNIV} DENGAN PT SINAR TEKNO FIKTIF\nNomor: PKS/77/2026\n\nPada tanggal 18 Mei 2026 para pihak sepakat melakukan riset bersama di bidang visi komputer.\nPasal 1: Ruang lingkup riset.\nPasal 2: Hak kekayaan intelektual dimiliki bersama.\nPasal 3: Jangka waktu dua tahun."),
    ("sk_abdimas", "scan", "SK abdimas", "412/PPM/2026", "2026-04-20", "",
     f"KEPUTUSAN KETUA LPPM {UNIV}\nNOMOR: 412/PPM/2026\n\nTENTANG\nPENETAPAN PELAKSANA PENGABDIAN KEPADA MASYARAKAT TAHUN 2026\n\nMEMUTUSKAN\nMENETAPKAN: Lina Oktaviani sebagai ketua pelaksana pengabdian kepada masyarakat di Desa Sukamaju.\n\nDitetapkan di Bandung pada tanggal 20 April 2026\nKetua LPPM, Yuni Astuti"),
    ("proposal_abdimas", "pdf", "Proposal abdimas", "", "", "",
     "USULAN PENGABDIAN KEPADA MASYARAKAT\nJudul: Pelatihan Pemasaran Digital bagi UMKM Desa Sukamaju\nTim Pengusul: Lina Oktaviani (ketua), Bagas Pratama (mahasiswa)\nMitra sasaran: Kelompok UMKM Sukamaju\n\nPermasalahan mitra: penjualan masih manual.\nSolusi: pelatihan dan pendampingan.\nRencana anggaran biaya: Rp 10.000.000."),
    ("surat_kesediaan_mitra", "foto", "Surat kesediaan mitra", "", "2026-02-25", "",
     "SURAT PERNYATAAN KESEDIAAN KERJA SAMA\n\nYang bertanda tangan di bawah ini:\nNama: Suparman\nJabatan: Ketua Kelompok UMKM Sukamaju\n\nMenyatakan bersedia menjadi mitra dalam kegiatan pengabdian kepada masyarakat yang dilaksanakan oleh Lina Oktaviani.\n\nSukamaju, 25 Februari 2026"),
    ("laporan_akhir_abdimas", "pdf", "Laporan akhir abdimas", "", "", "",
     "LAPORAN AKHIR PENGABDIAN KEPADA MASYARAKAT\nJudul: Pelatihan Pemasaran Digital bagi UMKM Desa Sukamaju\nKetua Pelaksana: Lina Oktaviani\n\nKegiatan telah selesai dilaksanakan bersama 25 pelaku UMKM.\nHasil: 18 peserta sudah berjualan melalui lokapasar.\nEvaluasi: mitra meminta pendampingan lanjutan."),
    ("loa_jurnal", "pdf", "LoA jurnal", "", "2026-07-03", "",
     "LETTER OF ACCEPTANCE\nJurnal Informatika Fiktif\n\nDear Sari Mulyani,\nWe are pleased to inform you that your manuscript entitled Hoax Detection for Indonesian Text has been accepted for publication in Volume 12 Number 2.\n\n3 July 2026\nEditor in Chief, Agus Prasetyo"),
    ("artikel_jurnal", "pdf", "Naskah artikel jurnal terbit", "", "", "",
     "Jurnal Informatika Fiktif, Vol. 12 No. 2, 2026, hlm. 101-112\nISSN 1234-5678\n\nHoax Detection for Indonesian Text Using Lightweight Transformers\nSari Mulyani, Arif Nugroho\n\nAbstract: This paper proposes a lightweight transformer for hoax detection.\nKeywords: hoax, transformer, Indonesian\n1. Introduction\n2. Method\n3. Results\nReferences"),
    ("sertifikat_presenter", "foto", "Sertifikat presenter konferensi", "", "2026-09-12", "",
     "CERTIFICATE OF PRESENTATION\n\nThis certificate is awarded to\nArif Nugroho\n\nfor presenting the paper Efficient Schema Matching\nat the International Conference on Fictional Computing\nheld on 12 September 2026 in Yogyakarta\n\nConference Chair, Maya Salim"),
    ("sertifikat_hki", "scan", "Sertifikat HKI", "EC00202612345", "2026-05-05", "",
     "SURAT PENCATATAN CIPTAAN\nNomor Pencatatan: EC00202612345\n\nPencipta: Rudi Hartono\nJenis Ciptaan: Program Komputer\nJudul Ciptaan: Aplikasi Pemantau Udara\nTanggal diumumkan: 5 Mei 2026\n\nDirektur Hak Cipta, Tri Wahyuni"),
    ("sertifikat_paten", "pdf", "Sertifikat paten", "IDS000123456", "2026-08-01", "",
     "SERTIFIKAT PATEN SEDERHANA\nNomor Paten: IDS000123456\n\nNama Invensi: Alat Sensor Debu Portabel\nInventor: Rudi Hartono\nPemegang Paten: Universitas Contoh Nusantara\nTanggal pemberian: 1 Agustus 2026\n\nDirektur Paten, Tri Wahyuni"),
    ("sk_kepanitiaan", "pdf", "SK kepanitiaan", "520/PAN/FIF/2026", "2026-07-20", "",
     f"KEPUTUSAN DEKAN FAKULTAS INFORMATIKA\n{UNIV}\nNOMOR: 520/PAN/FIF/2026\n\nTENTANG\nPEMBENTUKAN PANITIA SEMINAR NASIONAL INFORMATIKA 2026\n\nMEMUTUSKAN\nMENETAPKAN: Sari Mulyani sebagai Ketua Panitia dan Arif Nugroho sebagai Sekretaris.\n\nDitetapkan di Bandung pada tanggal 20 Juli 2026\nDekan, Hendra Kusuma"),
    ("sertifikat_narasumber", "foto", "Sertifikat narasumber", "78/SERT/2026", "2026-05-22", "",
     "SERTIFIKAT\nNomor: 78/SERT/2026\n\nDiberikan kepada\nLina Oktaviani\n\nsebagai NARASUMBER\npada Webinar Keamanan Data Kampus\n22 Mei 2026\n\nKetua Panitia, Maya Salim"),
    ("surat_tugas_reviewer", "pdf", "Surat tugas reviewer", "33/ST-REV/2026", "2026-06-01", "",
     "SURAT TUGAS\nNomor: 33/ST-REV/2026\n\nKetua LPPM menugaskan Arif Nugroho sebagai reviewer proposal hibah internal tahun 2026 untuk menilai usulan yang masuk.\n\nBandung, 1 Juni 2026\nKetua LPPM, Yuni Astuti"),
    ("sk_jabatan_fungsional", "scan", "SK jabatan fungsional", "71/JAFUNG/2026", "2026-04-01", "",
     "KEPUTUSAN MENTERI PENDIDIKAN FIKTIF\nNOMOR: 71/JAFUNG/2026\n\nTENTANG\nKENAIKAN JABATAN AKADEMIK DOSEN\n\nMEMUTUSKAN\nMENETAPKAN: Sari Mulyani diangkat dalam jabatan fungsional Lektor Kepala dengan angka kredit 420.\n\nDitetapkan di Jakarta pada tanggal 1 April 2026\nMenteri, Wira Atmaja"),
    ("sk_pangkat", "pdf", "SK pangkat", "92/KP/2026", "2026-04-10", "",
     f"KEPUTUSAN REKTOR {UNIV}\nNOMOR: 92/KP/2026\n\nTENTANG\nKENAIKAN PANGKAT DAN GOLONGAN PEGAWAI\n\nMEMUTUSKAN\nMENETAPKAN: Rudi Hartono naik pangkat menjadi Penata Tingkat I golongan III/d.\n\nDitetapkan di Bandung pada tanggal 10 April 2026\nRektor, Bambang Setiawan"),
    ("ijazah", "foto", "Ijazah", "IJZ-2019-00412", "2019-10-26", "",
     f"IJAZAH\n{UNIV}\nNomor: IJZ-2019-00412\n\nDengan ini menyatakan bahwa\nArif Nugroho\ntelah menyelesaikan program Magister Ilmu Komputer dan berhak memakai gelar M.Kom.\n\nDiberikan di Bandung pada tanggal 26 Oktober 2019\nRektor, Bambang Setiawan"),
    ("transkrip", "pdf", "Transkrip nilai", "TR-2019-00412", "2019-10-26", "",
     f"TRANSKRIP AKADEMIK\n{UNIV}\nNomor: TR-2019-00412\nNama: Arif Nugroho\nProgram: Magister Ilmu Komputer\n\nKode Mata Kuliah SKS Nilai\nMK501 Pembelajaran Mesin 3 A\nMK502 Metode Penelitian 2 A\nMK503 Sistem Terdistribusi 3 B\nIPK: 3,82\n\nBandung, 26 Oktober 2019"),
    ("sertifikat_kompetensi", "pdf", "Sertifikat kompetensi", "BNSP-KOM-55821", "2026-02-14", "",
     "SERTIFIKAT KOMPETENSI\nNomor: BNSP-KOM-55821\n\nDiberikan kepada\nLina Oktaviani\n\nyang telah dinyatakan kompeten pada skema Administrator Jaringan\nBerlaku tiga tahun sejak 14 Februari 2026\n\nLembaga Sertifikasi Profesi Fiktif"),
    ("laporan_bkd", "docx", "Laporan BKD", "", "", "Ganjil 2025/2026",
     "LAPORAN BEBAN KERJA DOSEN (BKD)\nNama: Sari Mulyani\nSemester Ganjil 2025/2026\n\nBidang pendidikan: 12 SKS\nBidang penelitian: 3 SKS\nBidang pengabdian: 1 SKS\nBidang penunjang: 1 SKS\nKesimpulan asesor: memenuhi syarat."),
    ("undangan_rapat", "pdf", "Lainnya", "19/UND/2026", "2026-03-30", "",
     "UNDANGAN\nNomor: 19/UND/2026\n\nDengan hormat, kami mengundang Bapak dan Ibu untuk hadir pada acara syukuran gedung baru dan makan siang bersama.\nTempat: Aula Timur\nPakaian: batik\n\nBandung, 30 Maret 2026\nKepala Bagian Umum, Dedi Rukmana"),
]


def pdf_teks(teks: str) -> pymupdf.Document:
    d = pymupdf.open()
    p = d.new_page()
    p.insert_textbox(pymupdf.Rect(60, 60, 540, 780), teks, fontsize=12, fontname="helv")
    return d


def kotori(d: pymupdf.Document, indeks: int) -> Image.Image:
    """Tiru hasil foto atau scan: abu-abu, sedikit miring, blur, dan bintik."""
    pix = d[0].get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
    sudut = (-2.0, 1.5, -1.0, 2.5)[indeks % 4]
    img = img.rotate(sudut, expand=True, fillcolor=235).filter(ImageFilter.GaussianBlur(0.7))
    arr = np.asarray(img, dtype=np.float32)
    bintik = np.random.default_rng(indeks).normal(0, 12, arr.shape)
    return Image.fromarray(np.clip(arr * 0.92 + 8 + bintik, 0, 255).astype(np.uint8))


def tulis_docx(teks: str, path: Path) -> None:
    w = docx.Document()
    for baris in teks.split("\n"):
        w.add_paragraph(baris)
    w.save(path)


def posisi_jenis() -> dict:
    t = json.loads((ROOT / "pipeline" / "config" / "taxonomy.json").read_text(encoding="utf-8"))
    return {j: (k["kode"], s["nama"]) for k in t["kategori"] for s in k["subkategori"] for j in s["jenis"]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    posisi = posisi_jenis()
    baris = []
    for i, (nama, fmt, jenis, nomor, tanggal, periode, teks) in enumerate(DOKUMEN):
        if fmt == "docx":
            berkas = f"{nama}.docx"
            tulis_docx(teks, OUT / berkas)
        elif fmt == "pdf":
            berkas = f"{nama}.pdf"
            pdf_teks(teks).save(OUT / berkas)
        elif fmt == "foto":
            berkas = f"{nama}.png"
            kotori(pdf_teks(teks), i).save(OUT / berkas)
        else:
            berkas = f"{nama}.pdf"
            buffer = io.BytesIO()
            kotori(pdf_teks(teks), i).save(buffer, "PNG")
            s = pymupdf.open()
            s.new_page().insert_image(pymupdf.Rect(0, 0, 595, 842), stream=buffer.getvalue())
            s.save(OUT / berkas)
        kategori, subkategori = posisi[jenis]
        baris.append([berkas, kategori, subkategori, jenis, nomor, tanggal, periode])
    with open(OUT / "labels.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nama_berkas", "kategori", "subkategori", "jenis", "nomor_dokumen", "tanggal_terbit", "periode"])
        w.writerows(baris)
    print(f"{len(baris)} dokumen dibuat di {OUT}")


if __name__ == "__main__":
    main()
