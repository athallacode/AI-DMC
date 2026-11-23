"""Perintah pengelola AI-DMC lewat terminal server. Fungsi yang sama tersedia di laman Admin.

Jalankan dari folder backend (atau lewat perintah `kelola` di server):
    python -m app.kelola --help

Setiap perintah yang mengubah data wajib menyebut --oleh (nama pengelola) dan dicatat di log audit.
Kolom user_id di log audit berisi akun yang terdampak; nama pengelola ada di detail.oleh.
Logikanya ada di app/services/admin.py, dipakai bersama dengan laman Admin.
"""
import argparse
import sys
from pathlib import Path

from .database import SessionLocal
from .models import Document
from .services import admin, pipeline
from .services.admin import Galat

PERAN = admin.PERAN


# ---------- perintah akun ----------

def akun_daftar(args):
    with SessionLocal() as db:
        akun = admin.daftar_akun(db)
    print(f'{"USERNAME":<20} {"PERAN":<6} {"NIP":<22} NAMA')
    for a in akun:
        tanda = '  (ditutup)' if a['ditutup'] else ''
        print(f'{a["username"]:<20} {a["peran"]:<6} {(a["nip"] or "-"):<22} {a["nama"]}{tanda}')
    print(f'\n{len(akun)} akun.')


def akun_buat(args):
    with SessionLocal() as db:
        _, password = admin.tambah_akun(db, args.username, args.nama, args.nip, args.peran, args.oleh, via='perintah')
        db.commit()
    print(f'Akun "{args.username}" dibuat. Password awal (hanya tampil sekali): {password}')
    print('Sampaikan langsung ke pemilik akun, jangan lewat grup chat.')


def akun_impor(args):
    sumber = Path(args.berkas)
    keluar = Path(args.keluar)
    if keluar.exists():
        raise Galat(f'{keluar} sudah ada. Pilih nama berkas lain supaya tidak tertimpa.')
    isi = sumber.read_text(encoding='utf-8-sig')
    with SessionLocal() as db:
        hasil, gagal = admin.impor_akun(db, isi, args.oleh, via='perintah')
        db.commit()
    import csv
    with keluar.open('w', encoding='utf-8-sig', newline='') as f:
        tulis = csv.writer(f)
        tulis.writerow(['username', 'nama', 'password_awal'])
        tulis.writerows((u.username, u.nama, p) for u, p in hasil)
    print(f'{len(hasil)} akun dibuat. Password awal ditulis ke {keluar}.')
    print('Hapus berkas itu setelah password dibagikan.')
    if gagal:
        print(f'{len(gagal)} baris dilewati:')
        for g in gagal:
            print('  ' + g)


def akun_reset_password(args):
    with SessionLocal() as db:
        password = admin.reset_password(db, admin.cari_akun(db, args.username), args.oleh, via='perintah')
        db.commit()
    print(f'Password "{args.username}" diganti. Password baru (hanya tampil sekali): {password}')


def akun_tutup(args):
    with SessionLocal() as db:
        admin.tutup_akun(db, admin.cari_akun(db, args.username), args.oleh, via='perintah')
        db.commit()
    print(f'Akun "{args.username}" ditutup. Dokumennya tetap tersimpan.')
    print('Sesi yang sedang terbuka tetap berlaku sampai habis (paling lama 60 menit).')
    print('Untuk membuka lagi, pakai reset-password.')


# ---------- perintah dokumen ----------

def dokumen_gagal(args):
    with SessionLocal() as db:
        docs = admin.dokumen_gagal(db)
        for doc, username in docs:
            galat = (doc.metadata_lain or {}).get('_error') or '-'
            print(f'{doc.id}  {doc.created_at:%Y-%m-%d %H:%M}  {username:<15} {doc.nama_berkas}')
            print(f'    {galat}')
        print(f'\n{len(docs)} dokumen gagal.')


def dokumen_proses_ulang(args):
    with SessionLocal() as db:
        doc = admin.cari_dokumen(db, args.kode)
        admin.siapkan_proses_ulang(db, doc, args.oleh, via='perintah')
        db.commit()
        doc_id = doc.id
    print('Memproses ulang. Bisa makan beberapa menit untuk dokumen scan...')
    pipeline.process_document(doc_id)
    with SessionLocal() as db:
        doc = db.get(Document, doc_id)
        print(f'Selesai. Status sekarang: {doc.status}')
        if doc.status == 'gagal':
            print('Masih gagal. Cek log backend untuk penyebabnya.')


def dokumen_tautkan(args):
    with SessionLocal() as db:
        admin.tautkan(db, admin.cari_dokumen(db, args.kode), admin.cari_akun(db, args.username), args.peran, args.oleh, via='perintah')
        db.commit()
    print(f'"{args.username}" sekarang tertaut ke dokumen {args.kode} dan bisa melihatnya.')


def susun_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='python -m app.kelola', description='Perintah pengelola AI-DMC.')
    utama = p.add_subparsers(dest='kelompok', required=True)

    def oleh(sp):
        sp.add_argument('--oleh', required=True, help='Nama pengelola yang menjalankan perintah (dicatat di log audit).')

    akun = utama.add_parser('akun', help='Kelola akun').add_subparsers(dest='perintah', required=True)
    akun.add_parser('daftar', help='Tampilkan semua akun').set_defaults(fungsi=akun_daftar)
    sp = akun.add_parser('buat', help='Buat satu akun')
    sp.add_argument('--username', required=True)
    sp.add_argument('--nama', required=True)
    sp.add_argument('--nip')
    sp.add_argument('--peran', default='dosen', choices=PERAN)
    oleh(sp); sp.set_defaults(fungsi=akun_buat)
    sp = akun.add_parser('impor', help='Buat banyak akun dari CSV (kolom: username, nama, nip, peran)')
    sp.add_argument('berkas')
    sp.add_argument('--keluar', required=True, help='Berkas CSV untuk menampung password awal')
    oleh(sp); sp.set_defaults(fungsi=akun_impor)
    sp = akun.add_parser('reset-password', help='Buat password baru')
    sp.add_argument('username')
    oleh(sp); sp.set_defaults(fungsi=akun_reset_password)
    sp = akun.add_parser('tutup', help='Tutup akun (tidak bisa masuk lagi)')
    sp.add_argument('username')
    oleh(sp); sp.set_defaults(fungsi=akun_tutup)

    dok = utama.add_parser('dokumen', help='Kelola dokumen').add_subparsers(dest='perintah', required=True)
    dok.add_parser('gagal', help='Tampilkan dokumen berstatus gagal').set_defaults(fungsi=dokumen_gagal)
    sp = dok.add_parser('proses-ulang', help='Proses ulang dokumen gagal')
    sp.add_argument('kode', help='Kode dokumen (lihat perintah gagal)')
    oleh(sp); sp.set_defaults(fungsi=dokumen_proses_ulang)
    sp = dok.add_parser('tautkan', help='Tautkan dosen lain ke dokumen (misal SK bersama)')
    sp.add_argument('kode')
    sp.add_argument('username')
    sp.add_argument('--peran', help='Peran dosen di dokumen, misal Anggota atau Pengajar')
    oleh(sp); sp.set_defaults(fungsi=dokumen_tautkan)
    return p


def main(argv=None) -> int:
    args = susun_parser().parse_args(argv)
    if hasattr(args, 'oleh') and not args.oleh.strip():
        print('Galat: --oleh tidak boleh kosong.', file=sys.stderr)
        return 1
    try:
        args.fungsi(args)
    except Galat as e:
        print(f'Galat: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
