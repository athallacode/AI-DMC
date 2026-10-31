import importlib
import logging
from decimal import Decimal
from sqlalchemy import select
from ..config import get_settings
from ..database import SessionLocal
from ..models import Document
from ..schemas import PipelineResult
from .documents import replace_lecturers
from ..integrations.mock import process_document as mock_process
from .taxonomy import valid_classification

logger = logging.getLogger(__name__)


def process_document(document_id):
    settings = get_settings()
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if not doc or doc.status != 'diproses':
            return
        try:
            if settings.pipeline_mode == 'mock':
                name = doc.nama_berkas.lower()
                scenario = 'fail' if 'gagal' in name or 'fail' in name else 'low' if 'low' in name or 'rendah' in name else 'high'
                raw = mock_process(doc.path_berkas, scenario=scenario, original_name=doc.nama_berkas)
            else:
                module, function = settings.pipeline_import.split(':', 1)
                raw = getattr(importlib.import_module(module), function)(doc.path_berkas)
            result = PipelineResult.model_validate(raw)
            if settings.pipeline_mode == 'mock':
                doc.model_dipakai = 'mock-development-only'
            if result.status == 'gagal':
                doc.status = 'gagal'
                doc.metadata_lain = {'_error': 'Pemrosesan gagal. Hubungi pengelola untuk mencoba kembali.' if settings.pipeline_mode == 'real' else result.error}
            else:
                if not valid_classification(result.klasifikasi.kategori, result.klasifikasi.subkategori, result.klasifikasi.jenis):
                    raise ValueError('Klasifikasi pipeline tidak sesuai taksonomi')
                doc.jenis_berkas = result.jenis_berkas
                doc.teks = result.teks
                for field in ['kategori', 'subkategori', 'jenis']:
                    setattr(doc, field, getattr(result.klasifikasi, field))
                for field in ['judul', 'nomor_dokumen', 'tanggal_terbit', 'periode']:
                    setattr(doc, field, getattr(result.metadata, field))
                doc.metadata_lain = {field: getattr(result.metadata, field) for field in ['mitra_penerbit', 'sumber_dana', 'identifier']}
                # Compare original precision, before NUMERIC(3,2) rounds for storage.
                doc.status = 'terverifikasi' if result.skor_keyakinan >= settings.confidence_threshold else 'menunggu_verifikasi'
                doc.skor_keyakinan = Decimal(str(result.skor_keyakinan))
                doc.ringkasan = result.ringkasan
                doc.model_dipakai = result.model_dipakai
                replace_lecturers(db, doc, result.metadata.dosen_terkait)
            db.commit()
        except Exception:
            logger.exception('Pipeline gagal untuk dokumen %s', document_id)
            db.rollback()
            doc = db.get(Document, document_id)
            if doc:
                doc.status = 'gagal'
                doc.metadata_lain = {'_error': 'Pemrosesan gagal. Hubungi pengelola untuk mencoba kembali.'}
                db.commit()


def mark_interrupted(db):
    for doc in db.scalars(select(Document).where(Document.status == 'diproses')).all():
        doc.status = 'gagal'
        doc.metadata_lain = {'_error': 'Pemrosesan terhenti saat layanan dimulai ulang. Hubungi pengelola.'}
    db.commit()
