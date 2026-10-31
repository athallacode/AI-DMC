import uuid
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, or_, select
from ..models import AuditLog, Document, DocumentLecturer, User


def access_clause(user):
    linked = select(DocumentLecturer.document_id).where(DocumentLecturer.user_id == user.id)
    return or_(Document.owner_id == user.id, and_(Document.tingkat_akses != 'rahasia', Document.id.in_(linked)))


def accessible(db, document_id, user, lock=False):
    query = select(Document).where(Document.id == document_id, access_clause(user))
    if lock:
        query = query.with_for_update()
    document = db.scalar(query)
    if not document:
        raise HTTPException(404, 'Dokumen tidak ditemukan.')
    return document


def audit(db, user_id, action, document_id=None, detail=None):
    db.add(AuditLog(user_id=user_id, aksi=action, document_id=document_id, detail=detail or {}))


def serialize(db, doc, detail=True):
    fields = ['id', 'owner_id', 'nama_berkas', 'jenis_berkas', 'kategori', 'subkategori', 'jenis', 'judul', 'nomor_dokumen', 'tanggal_terbit', 'periode', 'metadata_lain', 'skor_keyakinan', 'ringkasan', 'model_dipakai', 'status', 'tingkat_akses', 'versi', 'created_at', 'updated_at']
    value = {key: getattr(doc, key) for key in fields}
    value['error'] = (doc.metadata_lain or {}).get('_error')
    value['is_mock'] = doc.model_dipakai == 'mock-development-only'
    if detail:
        value['teks'] = doc.teks
        lecturers = db.scalars(select(DocumentLecturer).where(DocumentLecturer.document_id == doc.id)).all()
        value['dosen_terkait'] = [{key: getattr(item, key) for key in ['id', 'user_id', 'nama', 'nip', 'peran', 'dikonfirmasi']} for item in lecturers]
    return jsonable_encoder(value)


def replace_lecturers(db, doc, values, confirmed=False):
    # Delete/recreate associations inside the same transaction as correction.
    for item in db.scalars(select(DocumentLecturer).where(DocumentLecturer.document_id == doc.id)).all():
        db.delete(item)
    db.flush()
    owner = db.get(User, doc.owner_id)
    owner_linked = False
    for value in values:
        person = value.model_dump() if hasattr(value, 'model_dump') else value
        matched = db.scalar(select(User).where(User.nip == person['nip'])) if person.get('nip') else None
        if matched and matched.id == owner.id:
            owner_linked = True
        db.add(DocumentLecturer(document_id=doc.id, user_id=matched.id if matched else None, nama=person['nama'], nip=person.get('nip'), peran=person.get('peran'), dikonfirmasi=confirmed))
    if not owner_linked:
        db.add(DocumentLecturer(document_id=doc.id, user_id=owner.id, nama=owner.nama, nip=owner.nip, peran='Pengunggah', dikonfirmasi=confirmed))


def ensure_reviewable(doc):
    if doc.status not in {'menunggu_verifikasi', 'terverifikasi'}:
        raise HTTPException(409, 'Dokumen belum dapat diverifikasi atau sudah ditolak.')
