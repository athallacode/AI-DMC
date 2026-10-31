import uuid
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import extract, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..models import Correction, Document, DocumentLecturer, User
from ..schemas import CorrectionRequest
from ..security import current_user
from ..services.documents import accessible, access_clause, audit, ensure_reviewable, replace_lecturers, serialize
from ..services.pipeline import process_document
from ..services.storage import save_upload
from ..services.taxonomy import valid_classification

router = APIRouter(prefix='/documents', tags=['documents'])


@router.post('')
async def upload_documents(background: BackgroundTasks, files: Annotated[list[UploadFile], File()], user: User = Depends(current_user), db: Session = Depends(get_db)):
    if len(files) > 20:
        raise HTTPException(422, 'Unggah maksimal 20 berkas per permintaan.')
    response = {'documents': [], 'duplicates': [], 'errors': []}
    for upload in files:
        try:
            identifier, name, path, digest = await save_upload(upload)
        except ValueError as exc:
            response['errors'].append({'nama_berkas': upload.filename, 'message': str(exc)})
            continue
        existing = db.scalar(select(Document).where(Document.hash_sha256 == digest))
        if existing:
            path.unlink(missing_ok=True)
            item = {'nama_berkas': name, 'message': 'Sudah pernah diunggah'}
            visible = db.scalar(select(Document).where(Document.id == existing.id, access_clause(user)))
            if visible:
                item['document_id'] = str(existing.id)
            response['duplicates'].append(item)
            continue
        doc = Document(id=identifier, owner_id=user.id, nama_berkas=name, path_berkas=str(path), hash_sha256=digest)
        db.add(doc)
        try:
            db.flush()
            db.add(DocumentLecturer(document_id=doc.id, user_id=user.id, nama=user.nama, nip=user.nip, peran='Pengunggah'))
            audit(db, user.id, 'upload', doc.id, {'nama_berkas': name})
            db.commit()
        except IntegrityError:
            db.rollback()
            path.unlink(missing_ok=True)
            # Concurrent duplicate: disclose no identifier without another access check.
            response['duplicates'].append({'nama_berkas': name, 'message': 'Sudah pernah diunggah'})
            continue
        except Exception:
            db.rollback()
            path.unlink(missing_ok=True)
            raise
        response['documents'].append(serialize(db, doc))
        background.add_task(process_document, doc.id)
    return response


@router.get('')
def list_documents(status: str | None = None, kategori: str | None = None, tahun: Annotated[int | None, Query(ge=1900, le=2200)] = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Document).where(access_clause(user))
    if status:
        query = query.where(Document.status == status)
    if kategori:
        query = query.where(Document.kategori == kategori)
    if tahun:
        query = query.where(extract('year', Document.tanggal_terbit) == tahun)
    return [serialize(db, doc, detail=False) for doc in db.scalars(query.order_by(Document.created_at.desc())).all()]


@router.get('/{document_id}')
def detail(document_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return serialize(db, accessible(db, document_id, user))


@router.get('/{document_id}/file')
def original_file(document_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = accessible(db, document_id, user)
    path = Path(doc.path_berkas).resolve()
    root = get_settings().storage_dir.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404, 'Berkas tidak tersedia.')
    audit(db, user.id, 'unduh', doc.id)
    db.commit()
    media = {'.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}[path.suffix.lower()]
    return FileResponse(path, media_type=media, filename=doc.nama_berkas, content_disposition_type='inline' if path.suffix != '.docx' else 'attachment', headers={'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'private, no-store'})


@router.post('/{document_id}/approve')
def approve(document_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = accessible(db, document_id, user, lock=True)
    ensure_reviewable(doc)
    doc.status = 'terverifikasi'
    for lecturer in db.scalars(select(DocumentLecturer).where(DocumentLecturer.document_id == doc.id)).all():
        lecturer.dikonfirmasi = True
    audit(db, user.id, 'approve', doc.id)
    db.commit()
    return serialize(db, doc)


@router.post('/{document_id}/reject')
def reject(document_id: uuid.UUID, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = accessible(db, document_id, user, lock=True)
    ensure_reviewable(doc)
    doc.status = 'ditolak'
    audit(db, user.id, 'reject', doc.id)
    db.commit()
    return serialize(db, doc)


@router.patch('/{document_id}')
def correct(document_id: uuid.UUID, body: CorrectionRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = accessible(db, document_id, user, lock=True)
    ensure_reviewable(doc)
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(422, 'Ubah minimal satu field sebelum menyimpan koreksi.')
    classification = [data.get(field, getattr(doc, field)) for field in ['kategori', 'subkategori', 'jenis']]
    if not valid_classification(*classification):
        raise HTTPException(422, 'Pilih kategori, subkategori, dan jenis yang sesuai taksonomi.')
    before = serialize(db, doc)
    lecturers = data.pop('dosen_terkait', None)
    for key, value in data.items():
        if key == 'metadata_lain' and value is None:
            value = {}
        setattr(doc, key, value)
    if lecturers is not None:
        replace_lecturers(db, doc, lecturers, confirmed=True)
    else:
        for lecturer in db.scalars(select(DocumentLecturer).where(DocumentLecturer.document_id == doc.id)).all():
            lecturer.dikonfirmasi = True
    doc.status = 'terverifikasi'
    db.flush()
    after = serialize(db, doc)
    db.add(Correction(document_id=doc.id, user_id=user.id, sebelum=before, sesudah=after))
    audit(db, user.id, 'koreksi', doc.id, {'fields': list(body.model_fields_set)})
    db.commit()
    return after
