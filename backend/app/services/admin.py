"""Logika pengelolaan akun dan dokumen, dipakai bersama oleh perintah `app.kelola` dan laman Admin.

Setiap perubahan dicatat di log audit dengan aksi `kelola_...`. Kolom user_id berisi akun yang
terdampak; nama pengelola ada di detail.oleh, dan detail.via menunjukkan asalnya (perintah atau laman).
"""
import csv
import io
import secrets
import uuid

from sqlalchemy import func, select

from ..models import AuditLog, Document, DocumentLecturer, User
from ..security import hash_password

PERAN = ('dosen', 'admin')
AKSI_STATUS_AKUN = ('kelola_buat_akun', 'kelola_reset_password', 'kelola_tutup_akun')


class Galat(Exception):
    """Kesalahan yang aman ditampilkan ke pengelola."""


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
        doc = db.get(Document, uuid.UUID(str(identifier)))
    except ValueError:
        raise Galat(f'Kode dokumen "{identifier}" tidak valid.') from None
    if not doc:
        raise Galat(f'Dokumen {identifier} tidak ditemukan.')
    return doc


def tambah_akun(db, username, nama, nip, peran, oleh, **detail) -> tuple[User, str]:
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
    catat(db, user.id, 'buat_akun', oleh, peran=peran, **detail)
    return user, password


def impor_akun(db, isi_csv: str, oleh, **detail) -> tuple[list[tuple[User, str]], list[str]]:
    """Buat akun dari CSV (kolom username, nama, nip, peran). Baris bermasalah dilewati, sisanya tetap dibuat."""
    baris = list(csv.DictReader(io.StringIO(isi_csv)))
    if not baris:
        raise Galat('Berkas CSV kosong.')
    kolom = {k.strip().lower() for k in baris[0].keys() if k}
    if not {'username', 'nama'} <= kolom:
        raise Galat('CSV wajib punya kolom username dan nama. Kolom nip dan peran boleh ada.')
    hasil, gagal = [], []
    for nomor, row in enumerate(baris, start=2):
        row = {(k or '').strip().lower(): (v or '').strip() for k, v in row.items()}
        try:
            with db.begin_nested():
                hasil.append(tambah_akun(db, row.get('username'), row.get('nama'), row.get('nip'), row.get('peran') or 'dosen', oleh, **detail))
        except Galat as e:
            gagal.append(f'baris {nomor}: {e}')
    return hasil, gagal


def reset_password(db, user: User, oleh, **detail) -> str:
    password = buat_password()
    user.password_hash = hash_password(password)
    catat(db, user.id, 'reset_password', oleh, **detail)
    return password


def tutup_akun(db, user: User, oleh, **detail):
    # Password acak yang tidak pernah ditampilkan: akun tidak bisa dipakai masuk lagi.
    user.password_hash = hash_password(secrets.token_urlsafe(48))
    catat(db, user.id, 'tutup_akun', oleh, **detail)


def daftar_akun(db) -> list[dict]:
    """Semua akun dengan jumlah dokumen dan status. Akun berstatus ditutup kalau aksi pengelolaan
    terakhirnya adalah tutup akun (tidak ada kolom status di skema)."""
    users = db.scalars(select(User).order_by(User.peran, User.nama)).all()
    jumlah = dict(db.execute(select(Document.owner_id, func.count()).group_by(Document.owner_id)).all())
    terakhir = {}
    for user_id, aksi in db.execute(
        select(AuditLog.user_id, AuditLog.aksi).where(AuditLog.aksi.in_(AKSI_STATUS_AKUN)).order_by(AuditLog.created_at)
    ):
        terakhir[user_id] = aksi
    return [{
        'id': str(u.id), 'username': u.username, 'nama': u.nama, 'nip': u.nip, 'peran': u.peran,
        'jumlah_dokumen': jumlah.get(u.id, 0), 'ditutup': terakhir.get(u.id) == 'kelola_tutup_akun',
        'created_at': u.created_at,
    } for u in users]


def dokumen_gagal(db) -> list[tuple[Document, str]]:
    return db.execute(
        select(Document, User.username).join(User, User.id == Document.owner_id)
        .where(Document.status == 'gagal').order_by(Document.created_at)
    ).all()


def siapkan_proses_ulang(db, doc: Document, oleh, **detail):
    if doc.status != 'gagal':
        raise Galat(f'Status dokumen {doc.status}. Hanya dokumen gagal yang bisa diproses ulang.')
    doc.status = 'diproses'
    doc.metadata_lain = {}
    catat(db, doc.owner_id, 'proses_ulang', oleh, doc.id, **detail)


def tautkan(db, doc: Document, user: User, peran, oleh, **detail):
    if user.id == doc.owner_id:
        raise Galat('Akun itu adalah pengunggah dokumen ini.')
    tautan = db.scalar(select(DocumentLecturer).where(DocumentLecturer.document_id == doc.id, DocumentLecturer.user_id == user.id))
    if tautan:
        tautan.dikonfirmasi = True
        if peran:
            tautan.peran = peran
    else:
        db.add(DocumentLecturer(document_id=doc.id, user_id=user.id, nama=user.nama, nip=user.nip, peran=peran, dikonfirmasi=True))
    catat(db, user.id, 'tautkan', oleh, doc.id, peran=peran, **detail)
