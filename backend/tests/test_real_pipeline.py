"""Uji adapter dengan ekstraksi asli, respons LLM sintetis, dan SQLite migrasi."""
import json
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document as Docx
from pydantic import ValidationError

from test_application import context, headers
from app.config import get_settings
from app.schemas import PipelineResult
from pipeline.schemas import buat_output
from pipeline.taxonomy import load_taxonomy
import pipeline.main as source


@pytest.mark.parametrize('votes,expected', [(3, 'terverifikasi'), (1, 'menunggu_verifikasi')])
def test_real_upload_to_archive(context, monkeypatch, votes, expected):
    client, _, users = context
    settings = get_settings()
    monkeypatch.setattr(settings, 'pipeline_mode', 'real')
    monkeypatch.setattr(settings, 'pipeline_votes', votes)
    monkeypatch.setattr(settings, 'ollama_model', 'synthetic-integration-test')
    monkeypatch.setattr(settings, 'taxonomy_path', Path(__file__).resolve().parents[2] / 'pipeline/config/taxonomy.json')

    class FakeOllama:
        def __init__(self, config):
            assert config.jumlah_voting == votes
            assert config.ollama_model == 'synthetic-integration-test'
            self.nama_model = config.ollama_model

        def chat_json(self, system, user, schema, temperature):
            assert 'DOKUMEN SINTETIS' in user
            return json.dumps({'jenis': 'SK mengajar', 'judul': 'Uji integrasi sintetis'})

    monkeypatch.setattr(source, 'KlienOllama', FakeOllama)
    doc = Docx()
    doc.add_paragraph('DOKUMEN SINTETIS UNTUK UJI INTEGRASI. Keputusan penugasan mengajar semester ganjil. ' * 8)
    content = BytesIO()
    doc.save(content)
    response = client.post('/documents', headers=headers(users[0]), files=[('files', ('synthetic.docx', content.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))])
    assert response.status_code == 200, response.text
    identifier = response.json()['documents'][0]['id']
    detail = client.get('/documents/' + identifier, headers=headers(users[0])).json()
    assert detail['status'] == expected, detail
    assert detail['kategori'] == 'PND'
    assert detail['model_dipakai'] == 'synthetic-integration-test'
    assert client.get('/documents/' + identifier, headers=headers(users[1])).status_code == 404
    taxonomy = client.get('/taxonomy', headers=headers(users[0])).json()
    assert taxonomy['source'] == 'pipeline'
    assert taxonomy['categories'] == load_taxonomy().data['kategori']


def test_failed_source_contract_remains_strict_for_success():
    failed = buat_output(status='gagal', jenis_berkas=None, teks='', error='Uji gagal')
    assert PipelineResult.model_validate(failed).status == 'gagal'
    with pytest.raises(ValidationError):
        PipelineResult.model_validate({**failed, 'status': 'sukses'})


def test_unavailable_llm_marks_failed(context, monkeypatch):
    from pipeline.llm import LLMError

    client, _, users = context
    monkeypatch.setattr(get_settings(), 'pipeline_mode', 'real')

    class Unavailable:
        def __init__(self, settings):
            self.nama_model = settings.ollama_model

        def chat_json(self, *args, **kwargs):
            raise LLMError('Uji tidak tersedia: detail internal jangan ditampilkan')

    monkeypatch.setattr(source, 'KlienOllama', Unavailable)
    doc = Docx()
    doc.add_paragraph('Dokumen sintetis untuk pengujian layanan yang tidak tersedia. ' * 8)
    content = BytesIO()
    doc.save(content)
    response = client.post('/documents', headers=headers(users[0]), files=[('files', ('unavailable.docx', content.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))])
    identifier = response.json()['documents'][0]['id']
    detail = client.get('/documents/' + identifier, headers=headers(users[0])).json()
    assert detail['status'] == 'gagal'
    assert 'detail internal' not in json.dumps(detail)
