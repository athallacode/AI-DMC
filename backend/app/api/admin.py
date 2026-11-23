"""Endpoint laman Admin. Semua hanya untuk akun berperan admin.

Admin mengelola akun dan dokumen gagal, tetapi tetap tidak bisa membuka isi dokumen dosen:
yang ditampilkan hanya nama berkas, pengunggah, waktu, dan keterangan galat.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, Document, User
from ..security import current_user
from ..services import admin
from ..services.admin import Galat
from ..services.pipeline import process_document

router = APIRouter(prefix='/admin', tags=['admin'])
MAKS_CSV = 1024 * 1024


def admin_saja(user: User = Depends(current_user)) -> User:
    if user.peran != 'admin':
        raise HTTPException(403, 'Hanya admin yang dapat membuka laman ini.')
    return user


def pelaku(user: User) -> str:
    return f'{user.nama} ({user.username})'


def galat_400(fungsi):
    """Ubah Galat menjadi respons 400 dengan pesan yang bisa dibaca admin."""
    try:
        return fungsi()
    except Galat as e:
        raise HTTPException(400, str(e)) from None


class AkunBaru(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    nama: str = Field(min_length=1, max_length=200)
    nip: str | None = Field(default=None, max_length=64)
    peran: str = 'dosen'


class Tautan(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    peran: str | None = Field(default=None, max_length=100)


def akun_dari_id(db, user_id) -> User:
    try:
        user = db.get(User, uuid.UUID(user_id))
    except ValueError:
        user = None
    if not user:
        raise HTTPException(404, 'Akun tidak ditemukan.')
    return user


@router.get('/akun')
def daftar_akun(user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    return jsonable_encoder(admin.daftar_akun(db))


@router.post('/akun')
def buat_akun(body: AkunBaru, user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    baru, password = galat_400(lambda: admin.tambah_akun(db, body.username, body.nama, body.nip, body.peran, pelaku(user), via='laman_admin'))
    db.commit()
    return {'username': baru.username, 'nama': baru.nama, 'password': password}


@router.post('/akun/impor')
async def impor_akun(berkas: Annotated[UploadFile, File()], user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    data = await berkas.read(MAKS_CSV + 1)
    if len(data) > MAKS_CSV:
        raise HTTPException(400, 'Berkas CSV terlalu besar. Maksimal 1 MB.')
    try:
        isi = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise HTTPException(400, 'Simpan berkas sebagai CSV UTF-8, lalu unggah lagi.') from None
    hasil, gagal = galat_400(lambda: admin.impor_akun(db, isi, pelaku(user), via='laman_admin'))
    db.commit()
    return {'dibuat': [{'username': u.username, 'nama': u.nama, 'password': p} for u, p in hasil], 'dilewati': gagal}


@router.post('/akun/{user_id}/reset-password')
def reset_password(user_id: str, user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    target = akun_dari_id(db, user_id)
    password = admin.reset_password(db, target, pelaku(user), via='laman_admin')
    db.commit()
    return {'username': target.username, 'password': password}


@router.post('/akun/{user_id}/tutup')
def tutup_akun(user_id: str, user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    target = akun_dari_id(db, user_id)
    if target.id == user.id:
        raise HTTPException(400, 'Akun yang sedang dipakai tidak bisa ditutup sendiri.')
    admin.tutup_akun(db, target, pelaku(user), via='laman_admin')
    db.commit()
    return {'username': target.username, 'ditutup': True}


@router.get('/dokumen-gagal')
def dokumen_gagal(user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    return jsonable_encoder([{
        'id': doc.id, 'nama_berkas': doc.nama_berkas, 'pengunggah': username,
        'created_at': doc.created_at, 'keterangan': (doc.metadata_lain or {}).get('_error'),
    } for doc, username in admin.dokumen_gagal(db)])


@router.get('/dokumen-ditolak')
def dokumen_ditolak(user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    return jsonable_encoder([{
        'id': doc.id, 'nama_berkas': doc.nama_berkas, 'pengunggah': username,
        'created_at': doc.created_at, 'ditolak_at': doc.updated_at,
    } for doc, username in admin.dokumen_berstatus(db, 'ditolak')])


@router.post('/dokumen/{document_id}/kembalikan')
def kembalikan(document_id: str, user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    doc = galat_400(lambda: admin.cari_dokumen(db, document_id))
    galat_400(lambda: admin.kembalikan_ditolak(db, doc, pelaku(user), via='laman_admin'))
    db.commit()
    return {'id': str(doc.id), 'status': doc.status}


@router.get('/dokumen')
def cari_dokumen(cari: str = Query(min_length=3, max_length=100), user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    """Cari dokumen berdasarkan nama berkas, misalnya untuk menautkan SK bersama. Hanya data ringkas."""
    pola = '%' + cari.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
    baris = db.execute(
        select(Document, User.username).join(User, User.id == Document.owner_id)
        .where(Document.nama_berkas.ilike(pola, escape='\\')).order_by(Document.created_at.desc()).limit(20)
    ).all()
    return jsonable_encoder([{
        'id': doc.id, 'nama_berkas': doc.nama_berkas, 'pengunggah': username, 'status': doc.status, 'created_at': doc.created_at,
    } for doc, username in baris])


@router.post('/dokumen/{document_id}/proses-ulang')
def proses_ulang(document_id: str, background: BackgroundTasks, user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    doc = galat_400(lambda: admin.cari_dokumen(db, document_id))
    galat_400(lambda: admin.siapkan_proses_ulang(db, doc, pelaku(user), via='laman_admin'))
    db.commit()
    background.add_task(process_document, doc.id)
    return {'id': str(doc.id), 'status': 'diproses'}


@router.post('/dokumen/{document_id}/tautkan')
def tautkan(document_id: str, body: Tautan, user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    def jalankan():
        admin.tautkan(db, admin.cari_dokumen(db, document_id), admin.cari_akun(db, body.username.strip()), (body.peran or '').strip() or None, pelaku(user), via='laman_admin')
    galat_400(jalankan)
    db.commit()
    return {'id': document_id, 'username': body.username.strip()}


@router.get('/log')
def log_aktivitas(batas: int = Query(100, ge=1, le=500), user: User = Depends(admin_saja), db: Session = Depends(get_db)):
    baris = db.execute(
        select(AuditLog, User.username, User.nama).join(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.created_at.desc()).limit(batas)
    ).all()
    return jsonable_encoder([{
        'created_at': log.created_at, 'username': username, 'nama': nama, 'aksi': log.aksi,
        'document_id': log.document_id, 'oleh': (log.detail or {}).get('oleh'),
    } for log, username, nama in baris])
