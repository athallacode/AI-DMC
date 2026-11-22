"""Perintah pengelola AI-DMC (pengganti laman admin yang belum ada).

Jalankan dari folder backend (atau di dalam container backend):
    python -m app.kelola --help

Setiap perintah yang mengubah data wajib menyebut --oleh (nama pengelola) dan dicatat di log audit.
Kolom user_id di log audit berisi akun yang terdampak; nama pengelola ada di detail.oleh.
"""
import argparse
import csv
import secrets
import sys
import uuid
from pathlib import Path

from sqlalchemy import select

from .database import SessionLocal
from .models import AuditLog, Document, DocumentLecturer, User
from .security import hash_password
from .services import pipeline

PERAN = ('dosen', 'admin')


class Galat(Exception):
    """Kesalahan yang ditampilkan ke pengelola tanpa traceback."""


def buat_password() -> str:
    return secrets.token_urlsafe(12)


def catat(db, user_id, aksi, oleh, document_id=None, **detail):
    db.add(AuditLog(user_id=user_id, aksi=f'kelola_{aksi}', document_id=document_id, detail={'oleh': oleh, **detail}))


def cari_akun(db, username) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise Galat(f'Akun "{username}" tidak ditemukan.')
    return user


def cari_dokumen(db, identifier) -> Document:
    try:
        doc = db.get(Document, uuid.UUID(identifier))
    except ValueError:
        raise Galat(f'Kode dokumen "{identifier}" tidak valid.') from None
    if not doc:
        raise Galat(f'Dokumen {identifier} tidak ditemukan.')
    return doc


def _tambah_akun(db, username, nama, nip, peran, oleh) -> str:
    username = (username or '').strip()
    nama = (nama or '').strip()
    nip = (nip or '').strip() or None
    peran = (peran or 'dosen').strip().lower()
    if not username or not nama:
        raise Galat('Username dan nama wajib diisi.')
    if peran not in PERAN:
        raise Galat(f'Peran "{peran}" tidak dikenal. Pilih dosen atau admin.')
    if db.scalar(select(User).where(User.username == username)):
        raise Galat(f'Username "{username}" sudah dipakai.')
    if nip and db.scalar(select(User).where(User.nip == nip)):
        raise Galat(f'NIP {nip} sudah dipakai akun lain.')
    password = buat_password()
    user = User(username=username, nama=nama, nip=nip, peran=peran, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    catat(db, user.id, 'buat_akun', oleh, peran=peran)
    return password


# ---------- perintah akun ----------

def akun_daftar(args):
    with SessionLocal() as db:
        users = db.scalars(select(User).order_by(User.peran, User.username)).all()
        print(f'{"USERNAME":<20} {"PERAN":<6} {"NIP":<22} NAMA')
        for u in users:
            print(f'{u.username:<20} {u.peran:<6} {(u.nip or "-"):<22} {u.nama}')
        print(f'\n{len(users)} akun.')


def akun_buat(args):
    with SessionLocal() as db:
        password = _tambah_akun(db, args.username, args.nama, args.nip, args.peran, args.oleh)
        db.commit()
    print(f'Akun "{args.username}" dibuat. Password awal (hanya tampil sekali): {password}')
    print('Sampaikan langsung ke pemilik akun, jangan lewat grup chat.')


def akun_impor(args):
    sumber = Path(args.berkas)
    keluar = Path(args.keluar)
    if keluar.exists():
        raise Galat(f'{keluar} sudah ada. Pilih nama berkas lain supaya tidak tertimpa.')
    with sumber.open(encoding='utf-8-sig', newline='') as f:
        baris = list(csv.DictReader(f))
    if not baris:
        raise Galat('Berkas CSV kosong.')
    kolom = {k.strip().lower() for k in baris[0].keys() if k}
    if not {'username', 'nama'} <= kolom:
        raise Galat('CSV wajib punya kolom username dan nama. Kolom nip dan peran boleh ada.')
    hasil, gagal = [], []
    with SessionLocal() as db:
        for nomor, row in enumerate(baris, start=2):
            row = {(k or '').strip().lower(): (v or '').strip() for k, v in row.items()}
            try:
                with db.begin_nested():
                    password = _tambah_akun(db, row.get('username'), row.get('nama'), row.get('nip'), row.get('peran') or 'dosen', args.oleh)
                hasil.append((row['username'], row['nama'], password))
            except Galat as e:
                gagal.append(f'baris {nomor}: {e}')
        db.commit()
    with keluar.open('w', encoding='utf-8-sig', newline='') as f:
        tulis = csv.writer(f)
        tulis.writerow(['username', 'nama', 'password_awal'])
        tulis.writerows(hasil)
    print(f'{len(hasil)} akun dibuat. Password awal ditulis ke {keluar}.')
    print('Hapus berkas itu setelah password dibagikan.')
    if gagal:
        print(f'{len(gagal)} baris dilewati:')
        for g in gagal:
            print('  ' + g)


def akun_reset_password(args):
    with SessionLocal() as db:
        user = cari_akun(db, args.username)
        password = buat_password()
        user.password_hash = hash_password(password)
        catat(db, user.id, 'reset_password', args.oleh)
        db.commit()
    print(f'Password "{args.username}" diganti. Password baru (hanya tampil sekali): {password}')


def akun_tutup(args):
    with SessionLocal() as db:
        user = cari_akun(db, args.username)
        # Password acak yang tidak pernah ditampilkan: akun tidak bisa dipakai masuk lagi.
        user.password_hash = hash_password(secrets.token_urlsafe(48))
        catat(db, user.id, 'tutup_akun', args.oleh)
        db.commit()
    print(f'Akun "{args.username}" ditutup. Dokumennya tetap tersimpan.')
    print('Sesi yang sedang terbuka tetap berlaku sampai habis (paling lama 60 menit).')
    print('Untuk membuka lagi, pakai reset-password.')


# ---------- perintah dokumen ----------

def dokumen_gagal(args):
    with SessionLocal() as db:
        docs = db.execute(
            select(Document, User.username).join(User, User.id == Document.owner_id)
            .where(Document.status == 'gagal').order_by(Document.created_at)
        ).all()
        for doc, username in docs:
            galat = (doc.metadata_lain or {}).get('_error') or '-'
            print(f'{doc.id}  {doc.created_at:%Y-%m-%d %H:%M}  {username:<15} {doc.nama_berkas}')
            print(f'    {galat}')
        print(f'\n{len(docs)} dokumen gagal.')


def dokumen_proses_ulang(args):
    with SessionLocal() as db:
        doc = cari_dokumen(db, args.kode)
        if doc.status != 'gagal':
            raise Galat(f'Status dokumen {doc.status}. Hanya dokumen gagal yang bisa diproses ulang.')
        doc.status = 'diproses'
        doc.metadata_lain = {}
        catat(db, doc.owner_id, 'proses_ulang', args.oleh, doc.id)
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
        doc = cari_dokumen(db, args.kode)
        user = cari_akun(db, args.username)
        if user.id == doc.owner_id:
            raise Galat('Akun itu adalah pengunggah dokumen ini.')
        tautan = db.scalar(select(DocumentLecturer).where(DocumentLecturer.document_id == doc.id, DocumentLecturer.user_id == user.id))
        if tautan:
            tautan.dikonfirmasi = True
            if args.peran:
                tautan.peran = args.peran
        else:
            db.add(DocumentLecturer(document_id=doc.id, user_id=user.id, nama=user.nama, nip=user.nip, peran=args.peran, dikonfirmasi=True))
        catat(db, user.id, 'tautkan', args.oleh, doc.id, peran=args.peran)
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
