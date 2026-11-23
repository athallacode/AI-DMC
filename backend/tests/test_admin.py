"""Uji endpoint laman Admin dengan SQLite migrasi dan pipeline mock."""
import uuid

from sqlalchemy import select

from test_application import context, headers, upload
from app.models import AuditLog, Document

ENDPOINT_ADMIN = [
    ('get', '/admin/akun'), ('post', '/admin/akun'), ('post', '/admin/akun/impor'),
    ('get', '/admin/dokumen-gagal'), ('get', '/admin/log'), ('get', '/admin/dokumen?cari=sk-'),
]


def login(client, username, password):
    return client.post('/auth/login', json={'username': username, 'password': password})


def test_hanya_admin_yang_boleh(context):
    client, _, users = context
    dosen = users[0]
    for metode, path in ENDPOINT_ADMIN:
        assert getattr(client, metode)(path, headers=headers(dosen)).status_code == 403, path
        assert getattr(client, metode)(path).status_code == 401, path
    assert client.post(f'/admin/akun/{users[1].id}/tutup', headers=headers(dosen)).status_code == 403


def test_siklus_akun(context):
    client, sessions, users = context
    admin = headers(users[2])
    dibuat = client.post('/admin/akun', headers=admin, json={'username': 'dosen3', 'nama': 'Dosen Tiga', 'nip': '1003'})
    assert dibuat.status_code == 200
    awal = dibuat.json()['password']
    assert login(client, 'dosen3', awal).status_code == 200
    duplikat = client.post('/admin/akun', headers=admin, json={'username': 'dosen3', 'nama': 'X'})
    assert duplikat.status_code == 400 and 'sudah dipakai' in duplikat.json()['detail']
    assert client.post('/admin/akun', headers=admin, json={'username': 'x', 'nama': 'X', 'peran': 'rektor'}).status_code == 400

    akun = {a['username']: a for a in client.get('/admin/akun', headers=admin).json()}
    target = akun['dosen3']['id']
    assert akun['dosen3']['ditutup'] is False and 'password_hash' not in akun['dosen3']

    baru = client.post(f'/admin/akun/{target}/reset-password', headers=admin).json()['password']
    assert login(client, 'dosen3', awal).status_code == 401
    assert login(client, 'dosen3', baru).status_code == 200

    assert client.post(f'/admin/akun/{target}/tutup', headers=admin).status_code == 200
    assert login(client, 'dosen3', baru).status_code == 401
    assert {a['username']: a for a in client.get('/admin/akun', headers=admin).json()}['dosen3']['ditutup'] is True
    # Membuka lagi lewat reset password.
    client.post(f'/admin/akun/{target}/reset-password', headers=admin)
    assert {a['username']: a for a in client.get('/admin/akun', headers=admin).json()}['dosen3']['ditutup'] is False

    # Admin tidak bisa menutup akunnya sendiri, dan akun yang tidak ada dijawab 404.
    assert client.post(f'/admin/akun/{users[2].id}/tutup', headers=admin).status_code == 400
    assert client.post(f'/admin/akun/{uuid.uuid4()}/tutup', headers=admin).status_code == 404
    assert client.post('/admin/akun/bukan-kode/tutup', headers=admin).status_code == 404

    with sessions() as db:
        log = db.scalars(select(AuditLog).where(AuditLog.aksi.like('kelola_%'))).all()
        assert {r.detail['via'] for r in log} == {'laman_admin'}
        assert {r.detail['oleh'] for r in log} == {'admin (admin)'}


def test_impor_csv(context):
    client, _, users = context
    admin = headers(users[2])
    isi = 'username,nama,nip,peran\ndosen10,Dosen Sepuluh,2010,\ndosen1,Duplikat,,\ndosen11,Dosen Sebelas,,dosen\n'.encode('utf-8-sig')
    hasil = client.post('/admin/akun/impor', headers=admin, files={'berkas': ('dosen.csv', isi, 'text/csv')}).json()
    assert [a['username'] for a in hasil['dibuat']] == ['dosen10', 'dosen11']
    assert len(hasil['dilewati']) == 1 and 'sudah dipakai' in hasil['dilewati'][0]
    assert login(client, 'dosen10', hasil['dibuat'][0]['password']).status_code == 200
    rusak = client.post('/admin/akun/impor', headers=admin, files={'berkas': ('dosen.csv', 'nama;x\n'.encode('utf-16'), 'text/csv')})
    assert rusak.status_code == 400
    tanpa_kolom = client.post('/admin/akun/impor', headers=admin, files={'berkas': ('dosen.csv', b'nama\nA\n', 'text/csv')})
    assert tanpa_kolom.status_code == 400 and 'username' in tanpa_kolom.json()['detail']


def test_dokumen_gagal_dan_proses_ulang(context):
    client, sessions, users = context
    admin = headers(users[2])
    identifier = upload(client, users[0], 'sk-gagal.pdf')['documents'][0]['id']
    gagal = client.get('/admin/dokumen-gagal', headers=admin).json()
    assert [d['id'] for d in gagal] == [identifier]
    assert gagal[0]['pengunggah'] == 'dosen1' and gagal[0]['keterangan']
    # Admin tidak mendapat isi dokumen, dan tetap tidak bisa membuka dokumen dosen.
    assert 'teks' not in gagal[0]
    assert client.get('/documents/' + identifier, headers=admin).status_code == 404

    lain = upload(client, users[0], 'sk-tinggi.pdf', b'%PDF-1.4\nlain')['documents'][0]['id']
    assert client.post(f'/admin/dokumen/{lain}/proses-ulang', headers=admin).status_code == 400
    with sessions() as db:
        db.get(Document, uuid.UUID(identifier)).nama_berkas = 'sk-perbaikan.pdf'
        db.commit()
    assert client.post(f'/admin/dokumen/{identifier}/proses-ulang', headers=admin).json()['status'] == 'diproses'
    with sessions() as db:
        assert db.get(Document, uuid.UUID(identifier)).status == 'terverifikasi'
    assert client.get('/admin/dokumen-gagal', headers=admin).json() == []


def test_tautkan_dokumen(context):
    client, _, users = context
    admin = headers(users[2])
    identifier = upload(client, users[0])['documents'][0]['id']
    path = '/documents/' + identifier
    assert client.get(path, headers=headers(users[1])).status_code == 404
    hasil = client.post(f'/admin/dokumen/{identifier}/tautkan', headers=admin, json={'username': 'dosen2', 'peran': 'Anggota'})
    assert hasil.status_code == 200
    assert client.get(path, headers=headers(users[1])).status_code == 200
    assert client.post(path + '/approve', headers=headers(users[1])).status_code == 403
    assert client.post(f'/admin/dokumen/{identifier}/tautkan', headers=admin, json={'username': 'dosen1'}).status_code == 400
    assert client.post(f'/admin/dokumen/{identifier}/tautkan', headers=admin, json={'username': 'tidak-ada'}).status_code == 400
    assert client.post('/admin/dokumen/bukan-kode/tautkan', headers=admin, json={'username': 'dosen2'}).status_code == 400


def test_log_aktivitas(context):
    client, _, users = context
    admin = headers(users[2])
    upload(client, users[0], 'rahasia-pribadi.pdf', b'%PDF-1.4\nlog')
    client.post('/admin/akun', headers=admin, json={'username': 'dosen4', 'nama': 'Dosen Empat'})
    log = client.get('/admin/log?batas=10', headers=admin).json()
    assert log[0]['aksi'] == 'kelola_buat_akun' and log[0]['username'] == 'dosen4' and log[0]['oleh'] == 'admin (admin)'
    assert any(r['aksi'] == 'upload' and r['username'] == 'dosen1' for r in log)
    # Detail audit (misalnya nama berkas) tidak dikirim ke laman.
    assert 'rahasia-pribadi' not in str(log)


def test_cari_dokumen_berdasarkan_nama(context):
    client, _, users = context
    admin = headers(users[2])
    identifier = upload(client, users[0], 'SK_Pengajaran_2026.pdf', b'%PDF-1.4\ncari')['documents'][0]['id']
    upload(client, users[1], 'sertifikat.pdf', b'%PDF-1.4\nlain')
    hasil = client.get('/admin/dokumen?cari=pengajaran', headers=admin).json()
    assert [(d['id'], d['pengunggah']) for d in hasil] == [(identifier, 'dosen1')]
    assert set(hasil[0]) == {'id', 'nama_berkas', 'pengunggah', 'status', 'created_at'}
    # Karakter wildcard SQL diperlakukan sebagai huruf biasa.
    assert client.get('/admin/dokumen?cari=%25%25%25', headers=admin).json() == []
    assert client.get('/admin/dokumen?cari=sk', headers=admin).status_code == 422


def test_kembalikan_dokumen_ditolak(context):
    client, sessions, users = context
    admin = headers(users[2])
    dosen1, dosen2 = headers(users[0]), headers(users[1])
    identifier = upload(client, users[0], 'sk-tinggi.pdf')['documents'][0]['id']
    path = '/documents/' + identifier
    # SK bersama yang sudah bisa dilihat dosen2, lalu ditolak dosen1 karena salah tekan.
    client.post(f'/admin/dokumen/{identifier}/tautkan', headers=admin, json={'username': 'dosen2'})
    assert client.get(path, headers=dosen2).status_code == 200
    assert client.post(path + '/reject', headers=dosen1).status_code == 200
    assert client.post(path + '/approve', headers=dosen1).status_code == 409

    assert client.get('/admin/dokumen-ditolak', headers=dosen1).status_code == 403
    assert client.post(f'/admin/dokumen/{identifier}/kembalikan', headers=dosen1).status_code == 403
    ditolak = client.get('/admin/dokumen-ditolak', headers=admin).json()
    assert [d['id'] for d in ditolak] == [identifier] and ditolak[0]['pengunggah'] == 'dosen1'

    hasil = client.post(f'/admin/dokumen/{identifier}/kembalikan', headers=admin)
    assert hasil.status_code == 200 and hasil.json()['status'] == 'menunggu_verifikasi'
    assert client.get('/admin/dokumen-ditolak', headers=admin).json() == []
    # Muncul lagi di Kotak Verifikasi pengunggah.
    menunggu = client.get('/documents?status=menunggu_verifikasi', headers=dosen1).json()
    assert identifier in [d['id'] for d in menunggu]
    # Dosen tertaut baru bisa melihat lagi setelah pengunggah menyetujui ulang.
    assert client.get(path, headers=dosen2).status_code == 404
    assert client.post(path + '/approve', headers=dosen1).status_code == 200
    assert client.get(path, headers=dosen2).status_code == 200
    # Dokumen yang tidak berstatus ditolak tidak bisa dikembalikan.
    tolak_lagi = client.post(f'/admin/dokumen/{identifier}/kembalikan', headers=admin)
    assert tolak_lagi.status_code == 400 and 'Hanya dokumen ditolak' in tolak_lagi.json()['detail']
    with sessions() as db:
        log = db.scalar(select(AuditLog).where(AuditLog.aksi == 'kelola_batal_tolak'))
        assert str(log.document_id) == identifier and log.detail['oleh'] == 'admin (admin)'
