import json
from fastapi import HTTPException
from ..config import get_settings

DEMO = [
    {'kode': 'PND', 'nama': 'Pendidikan', 'subkategori': [{'nama': 'SK mengajar dan beban kerja', 'jenis': ['SK mengajar']}]},
    *[{'kode': code, 'nama': name, 'subkategori': [{'nama': 'Contoh sementara', 'jenis': ['Dokumen contoh']}]} for code, name in [('PNL', 'Penelitian'), ('PKM', 'Pengabdian kepada masyarakat'), ('PUB', 'Publikasi'), ('PNJ', 'Penunjang'), ('ADM', 'Administrasi'), ('LAINNYA', 'Lainnya')]],
]


def load_taxonomy():
    settings = get_settings()
    if settings.pipeline_mode == 'mock':
        return {'source': 'demo', 'categories': DEMO}
    try:
        value = json.loads(settings.taxonomy_path.read_text(encoding='utf-8'))
        categories = value.get('categories', value.get('kategori')) if isinstance(value, dict) else value
        for category in categories:
            assert category['kode'] and category['nama'] and isinstance(category['subkategori'], list)
            for sub in category['subkategori']:
                assert sub['nama'] and isinstance(sub['jenis'], list)
        return {'source': 'pipeline', 'categories': categories}
    except (OSError, ValueError, KeyError, TypeError, AssertionError):
        raise HTTPException(503, 'Taksonomi pipeline belum tersedia atau formatnya belum sesuai kontrak adapter.')


def valid_classification(kategori, subkategori, jenis):
    return any(c['kode'] == kategori and any(s['nama'] == subkategori and jenis in s['jenis'] for s in c['subkategori']) for c in load_taxonomy()['categories'])
