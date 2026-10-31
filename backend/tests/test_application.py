"""Integration tests with a migrated SQLite DB; PostgreSQL remains deployment gate."""
import os
import uuid
from io import BytesIO
from zipfile import ZipFile

os.environ['JWT_SECRET'] = 'test-secret-only-' + 'x' * 40
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['PIPELINE_MODE'] = 'mock'

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.database import get_db, make_engine
from app.main import app
from app.models import AuditLog, Correction, Document, DocumentLecturer, User
from app.security import create_token, hash_password
import app.main as main_module
import app.services.pipeline as pipeline


@pytest.fixture
def context(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'database_url', f'sqlite:///{(tmp_path / "test.db").as_posix()}')
    monkeypatch.setattr(settings, 'storage_dir', tmp_path / 'storage')
    monkeypatch.setattr(settings, 'confidence_threshold', 0.85)
    config = Config('alembic.ini')
    command.upgrade(config, 'head')
    engine = make_engine(settings.database_url)
    sessions = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(pipeline, 'SessionLocal', sessions)
    monkeypatch.setattr(main_module, 'SessionLocal', sessions)
    def override_db():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    users = []
    with sessions() as db:
        for username, role in [('dosen1', 'dosen'), ('dosen2', 'dosen'), ('admin', 'admin')]:
            user = User(username=username, nama=username, peran=role, nip=username, password_hash=hash_password('test-password'))
            db.add(user)
            users.append(user)
        db.commit()
    with TestClient(app) as client:
        yield client, sessions, users
    app.dependency_overrides.clear()
    engine.dispose()


def headers(user):
    return {'Authorization': 'Bearer ' + create_token(user)}


def upload(client, user, name='sk-low.pdf', content=b'%PDF-1.4\nsynthetic fixture'):
    response = client.post('/documents', headers=headers(user), files=[('files', (name, content, 'application/pdf'))])
    assert response.status_code == 200, response.text
    return response.json()


def test_login_health_and_authorization(context):
    client, _, users = context
    assert client.get('/health').json() == {'status': 'ok', 'pipeline_mode': 'mock', 'confidence_threshold': 0.85}
    assert client.get('/documents').status_code == 401
    assert client.post('/auth/login', json={'username': 'dosen1', 'password': 'wrong'}).status_code == 401
    response = client.post('/auth/login', json={'username': 'dosen1', 'password': 'test-password'})
    assert response.status_code == 200
    assert response.json()['user']['username'] == 'dosen1'
    assert client.get('/auth/me', headers={'Authorization': 'Bearer ' + response.json()['access_token']}).json()['id'] == str(users[0].id)


def test_pipeline_outcomes_filters_and_duplicate_privacy(context):
    client, _, users = context
    ids = []
    for name, status in [('high.pdf', 'terverifikasi'), ('low.pdf', 'menunggu_verifikasi'), ('gagal.pdf', 'gagal')]:
        result = upload(client, users[0], name, b'%PDF-1.4\n' + name.encode())
        identifier = result['documents'][0]['id']
        ids.append(identifier)
        detail = client.get('/documents/' + identifier, headers=headers(users[0])).json()
        assert detail['status'] == status
        assert detail['dosen_terkait'][0]['user_id'] == str(users[0].id)
    duplicate = upload(client, users[0], 'copy.pdf', b'%PDF-1.4\nhigh.pdf')['duplicates'][0]
    assert duplicate['document_id'] == ids[0]
    private_duplicate = upload(client, users[1], 'copy.pdf', b'%PDF-1.4\nhigh.pdf')['duplicates'][0]
    assert 'document_id' not in private_duplicate
    assert len(client.get('/documents?status=terverifikasi&kategori=PND', headers=headers(users[0])).json()) == 1
    assert client.get('/documents', headers=headers(users[1])).json() == []


def test_file_access_linked_lecturer_and_confidential(context):
    client, sessions, users = context
    identifier = upload(client, users[0])['documents'][0]['id']
    path = '/documents/' + identifier
    for suffix in ['', '/file']:
        assert client.get(path + suffix, headers=headers(users[1])).status_code == 404
        assert client.get(path + suffix, headers=headers(users[2])).status_code == 404
    assert client.get(path + '/file', headers=headers(users[0])).content.startswith(b'%PDF-')
    with sessions() as db:
        db.add(DocumentLecturer(document_id=uuid.UUID(identifier), user_id=users[1].id, nama='dosen2', peran='Anggota'))
        db.commit()
    assert client.get(path, headers=headers(users[1])).status_code == 200
    with sessions() as db:
        db.get(Document, uuid.UUID(identifier)).tingkat_akses = 'rahasia'
        db.commit()
    assert client.get(path, headers=headers(users[1])).status_code == 404


def test_correction_approval_and_audit(context):
    client, sessions, users = context
    identifier = upload(client, users[0])['documents'][0]['id']
    response = client.patch('/documents/' + identifier, headers=headers(users[0]), json={'judul': 'Judul hasil koreksi', 'tanggal_terbit': '2026-10-31', 'dosen_terkait': [{'nama': 'Dosen Dua', 'nip': 'dosen2', 'peran': 'Pengajar'}]})
    assert response.status_code == 200, response.text
    assert response.json()['status'] == 'terverifikasi'
    assert all(item['dikonfirmasi'] for item in response.json()['dosen_terkait'])
    assert len(client.get('/documents?tahun=2026', headers=headers(users[0])).json()) == 1
    assert client.get('/documents?tahun=2025', headers=headers(users[0])).json() == []
    with sessions() as db:
        correction = db.scalar(select(Correction))
        assert correction.sebelum['judul'] != correction.sesudah['judul']
        assert correction.sesudah['judul'] == 'Judul hasil koreksi'
        assert {row.aksi for row in db.scalars(select(AuditLog)).all()} == {'upload', 'koreksi'}
    assert client.get('/admin/koreksi/export', headers=headers(users[0])).status_code == 403
    assert len(client.get('/admin/koreksi/export', headers=headers(users[2])).json()) == 1


def test_approve_reject_state_and_validation(context):
    client, _, users = context
    identifier = upload(client, users[0])['documents'][0]['id']
    path = '/documents/' + identifier
    assert client.patch(path, headers=headers(users[0]), json={'kategori': 'PUB'}).status_code == 422
    assert client.post(path + '/approve', headers=headers(users[1])).status_code == 404
    approved = client.post(path + '/approve', headers=headers(users[0]))
    assert approved.status_code == 200
    assert approved.json()['dosen_terkait'][0]['dikonfirmasi'] is True
    assert client.post(path + '/reject', headers=headers(users[0])).json()['status'] == 'ditolak'
    assert client.post(path + '/approve', headers=headers(users[0])).status_code == 409


def test_upload_validation_and_mixed_batch(context, monkeypatch):
    client, _, users = context
    import app.services.storage as storage
    monkeypatch.setattr(storage, 'MAX_BYTES', 40)
    response = client.post('/documents', headers=headers(users[0]), files=[
        ('files', ('wrong.pdf', b'not a PDF', 'application/pdf')),
        ('files', ('file.exe', b'executable', 'application/octet-stream')),
        ('files', ('large.pdf', b'%PDF-' + b'x' * 100, 'application/pdf')),
        ('files', ('ok.pdf', b'%PDF-1.4\nfixture', 'application/pdf')),
    ])
    assert len(response.json()['errors']) == 3
    assert len(response.json()['documents']) == 1
    assert len(list(get_settings().storage_dir.iterdir())) == 1


def test_docx_png_jpg_acceptance(context):
    client, _, users = context
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('word/document.xml', '<document/>')
    for name, data in [('example.docx', buffer.getvalue()), ('photo.png', b'\x89PNG\r\n\x1a\nfixture'), ('photo.jpg', b'\xff\xd8\xfffixture')]:
        assert len(upload(client, users[0], name, data)['documents']) == 1


def test_threshold_compares_before_rounding(context, monkeypatch):
    client, _, users = context
    original = pipeline.mock_process
    def scored(*args, **kwargs):
        value = original(*args, **kwargs)
        value['skor_keyakinan'] = 0.849
        return value
    monkeypatch.setattr(pipeline, 'mock_process', scored)
    identifier = upload(client, users[0])['documents'][0]['id']
    assert client.get('/documents/' + identifier, headers=headers(users[0])).json()['status'] == 'menunggu_verifikasi'
    monkeypatch.setattr(get_settings(), 'confidence_threshold', 0.849)
    identifier = upload(client, users[0], 'equal.pdf', b'%PDF-1.4\nequal')['documents'][0]['id']
    assert client.get('/documents/' + identifier, headers=headers(users[0])).json()['status'] == 'terverifikasi'


def test_audit_database_append_only(context):
    client, sessions, users = context
    upload(client, users[0])
    for sql in ["UPDATE audit_log SET aksi='changed'", 'DELETE FROM audit_log']:
        with sessions() as db:
            with pytest.raises(DatabaseError):
                db.execute(text(sql))
                db.commit()
            db.rollback()


def test_restart_marks_interrupted_documents_failed(context):
    client, sessions, users = context
    identifier = upload(client, users[0])['documents'][0]['id']
    with sessions() as db:
        db.get(Document, uuid.UUID(identifier)).status = 'diproses'
        db.commit()
        pipeline.mark_interrupted(db)
        assert db.get(Document, uuid.UUID(identifier)).status == 'gagal'


def test_malformed_pipeline_and_invalid_taxonomy_fail_safely(context, monkeypatch):
    client, _, users = context
    def malformed(*args, **kwargs):
        return {'status': 'sukses', 'skor_keyakinan': 1.5}
    monkeypatch.setattr(pipeline, 'mock_process', malformed)
    identifier = upload(client, users[0])['documents'][0]['id']
    detail = client.get('/documents/' + identifier, headers=headers(users[0])).json()
    assert detail['status'] == 'gagal'
    assert 'ValidationError' not in detail['error']
    from app.integrations.mock import process_document
    def wrong_classification(*args, **kwargs):
        value = process_document(*args, **kwargs)
        value['klasifikasi']['jenis'] = 'Tidak ada pada taksonomi'
        return value
    monkeypatch.setattr(pipeline, 'mock_process', wrong_classification)
    identifier = upload(client, users[0], 'invalid.pdf', b'%PDF-1.4\ninvalid')['documents'][0]['id']
    assert client.get('/documents/' + identifier, headers=headers(users[0])).json()['status'] == 'gagal'
