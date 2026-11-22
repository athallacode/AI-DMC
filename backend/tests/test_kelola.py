"""Uji perintah pengelola (app.kelola) dengan SQLite migrasi dan pipeline mock."""
import csv
import uuid

import pytest
from sqlalchemy import select

from test_application import context, headers, upload
from app import kelola
from app.models import AuditLog, Document, User


@pytest.fixture
def k(context, monkeypatch):
    client, sessions, users = context
    monkeypatch.setattr(kelola, 'SessionLocal', sessions)
    return client, sessions, users


def login(client, username, password):
    return client.post('/auth/login', json={'username': username, 'password': password})


def password_dari(keluaran: str) -> str:
    return keluaran.strip().splitlines()[0].rsplit(' ', 1)[-1]


def test_buat_reset_dan_tutup_akun(k, capsys):
    client, sessions, _ = k
    assert kelola.main(['akun', 'buat', '--username', 'dosen3', '--nama', 'Dosen Tiga', '--nip', '1003', '--oleh', 'Pengelola A']) == 0
    awal = password_dari(capsys.readouterr().out)
    assert login(client, 'dosen3', awal).status_code == 200

    assert kelola.main(['akun', 'reset-password', 'dosen3', '--oleh', 'Pengelola A']) == 0
    baru = password_dari(capsys.readouterr().out)
    assert login(client, 'dosen3', awal).status_code == 401
    assert login(client, 'dosen3', baru).status_code == 200

    assert kelola.main(['akun', 'tutup', 'dosen3', '--oleh', 'Pengelola A']) == 0
    assert login(client, 'dosen3', baru).status_code == 401

    with sessions() as db:
        aksi = [r.aksi for r in db.scalars(select(AuditLog).where(AuditLog.aksi.like('kelola_%')).order_by(AuditLog.created_at))]
        assert aksi == ['kelola_buat_akun', 'kelola_reset_password', 'kelola_tutup_akun']
        assert all(r.detail['oleh'] == 'Pengelola A' for r in db.scalars(select(AuditLog).where(AuditLog.aksi.like('kelola_%'))))


def test_buat_akun_menolak_duplikat_dan_oleh_kosong(k, capsys):
    assert kelola.main(['akun', 'buat', '--username', 'dosen1', '--nama', 'X', '--oleh', 'A']) == 1
    assert 'sudah dipakai' in capsys.readouterr().err
    assert kelola.main(['akun', 'buat', '--username', 'baru', '--nama', 'X', '--nip', 'dosen2', '--oleh', 'A']) == 1
    assert 'NIP' in capsys.readouterr().err
    assert kelola.main(['akun', 'buat', '--username', 'baru', '--nama', 'X', '--oleh', '  ']) == 1
    with pytest.raises(SystemExit):
        kelola.main(['akun', 'buat', '--username', 'baru', '--nama', 'X'])


def test_impor_csv(k, tmp_path, capsys):
    client, sessions, _ = k
    sumber = tmp_path / 'dosen.csv'
    sumber.write_text('Username,Nama,NIP,Peran\ndosen10,Dosen Sepuluh,2010,\ndosen1,Duplikat,,\ndosen11,Dosen Sebelas,,dosen\n,Tanpa Username,,\n', encoding='utf-8-sig')
    keluar = tmp_path / 'password.csv'
    assert kelola.main(['akun', 'impor', str(sumber), '--keluar', str(keluar), '--oleh', 'A']) == 0
    out = capsys.readouterr().out
    assert '2 akun dibuat' in out and '2 baris dilewati' in out
    with keluar.open(encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    assert [r['username'] for r in rows] == ['dosen10', 'dosen11']
    assert login(client, 'dosen10', rows[0]['password_awal']).status_code == 200
    # tidak menimpa berkas password yang sudah ada
    assert kelola.main(['akun', 'impor', str(sumber), '--keluar', str(keluar), '--oleh', 'A']) == 1


def test_tautkan_dokumen(k):
    client, sessions, users = k
    identifier = upload(client, users[0])['documents'][0]['id']
    path = '/documents/' + identifier
    assert client.get(path, headers=headers(users[1])).status_code == 404
    assert kelola.main(['dokumen', 'tautkan', identifier, 'dosen2', '--peran', 'Anggota', '--oleh', 'A']) == 0
    assert client.get(path, headers=headers(users[1])).status_code == 200
    # tetap tidak boleh mengubah
    assert client.post(path + '/approve', headers=headers(users[1])).status_code == 403
    assert kelola.main(['dokumen', 'tautkan', identifier, 'dosen1', '--oleh', 'A']) == 1
    assert kelola.main(['dokumen', 'tautkan', 'bukan-kode', 'dosen2', '--oleh', 'A']) == 1


def test_daftar_gagal_dan_proses_ulang(k, capsys):
    client, sessions, users = k
    identifier = upload(client, users[0], 'sk-gagal.pdf')['documents'][0]['id']
    with sessions() as db:
        assert db.get(Document, uuid.UUID(identifier)).status == 'gagal'
    assert kelola.main(['dokumen', 'gagal']) == 0
    assert identifier in capsys.readouterr().out
    # Dokumen yang bukan gagal tidak boleh diproses ulang.
    lain = upload(client, users[0], 'sk-tinggi.pdf', b'%PDF-1.4\nlain')['documents'][0]['id']
    assert kelola.main(['dokumen', 'proses-ulang', lain, '--oleh', 'A']) == 1
    # Ganti nama supaya mock tidak lagi memilih skenario gagal, lalu proses ulang.
    with sessions() as db:
        db.get(Document, uuid.UUID(identifier)).nama_berkas = 'sk-perbaikan.pdf'
        db.commit()
    assert kelola.main(['dokumen', 'proses-ulang', identifier, '--oleh', 'A']) == 0
    assert 'Status sekarang: terverifikasi' in capsys.readouterr().out
    with sessions() as db:
        assert db.scalar(select(AuditLog).where(AuditLog.aksi == 'kelola_proses_ulang')).detail['oleh'] == 'A'
