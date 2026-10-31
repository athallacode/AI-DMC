"""Development fixture, not extraction/OCR/AI. Filename low/gagal chooses scenario."""
from pathlib import Path


def process_document(file_path, *, scenario='high', original_name=None):
    path = Path(file_path)
    if scenario == 'fail':
        return {'status': 'gagal', 'error': 'Simulasi kegagalan pipeline mock.'}
    return {
        'status': 'sukses',
        'jenis_berkas': 'pdf_digital' if path.suffix == '.pdf' else 'docx' if path.suffix == '.docx' else 'gambar',
        'teks': '[MOCK] Teks contoh sintetis, bukan hasil ekstraksi berkas.',
        'klasifikasi': {'kategori': 'PND', 'subkategori': 'SK mengajar dan beban kerja', 'jenis': 'SK mengajar'},
        'skor_keyakinan': 0.72 if scenario == 'low' else 0.91,
        'metadata': {'judul': '[MOCK] ' + (original_name or path.name), 'nomor_dokumen': None, 'tanggal_terbit': None,
                     'periode': None, 'dosen_terkait': [], 'mitra_penerbit': None, 'sumber_dana': None, 'identifier': None},
        'ringkasan': 'Data simulasi untuk pengembangan aplikasi.',
        'model_dipakai': 'mock-development-only', 'waktu_proses_detik': 0, 'error': None,
    }
