import hashlib
import uuid
import zipfile
from pathlib import Path
from fastapi import UploadFile
from ..config import get_settings

MAX_BYTES = 20 * 1024 * 1024
ALLOWED = {'.pdf', '.docx', '.jpg', '.jpeg', '.png'}


def validate_content(path, extension):
    with path.open('rb') as stream:
        header = stream.read(16)
    if extension == '.pdf':
        return header.startswith(b'%PDF-')
    if extension == '.png':
        return header.startswith(b'\x89PNG\r\n\x1a\n')
    if extension in {'.jpg', '.jpeg'}:
        return header.startswith(b'\xff\xd8\xff')
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            return {'[Content_Types].xml', 'word/document.xml'}.issubset(names)
    except (zipfile.BadZipFile, OSError):
        return False


async def save_upload(upload: UploadFile):
    name = Path((upload.filename or '').replace('\\', '/')).name
    extension = Path(name).suffix.lower()
    if extension not in ALLOWED:
        await upload.close()
        raise ValueError('Format berkas tidak didukung. Gunakan PDF, DOCX, JPG, atau PNG.')
    root = get_settings().storage_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    identifier = uuid.uuid4()
    path = root / f'{identifier}{extension}'
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open('xb') as stream:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Ukuran berkas melebihi 20 MB. Pilih berkas yang lebih kecil.')
                digest.update(chunk)
                stream.write(chunk)
        if not size or not validate_content(path, extension):
            raise ValueError('Isi berkas tidak sesuai format atau berkas kosong. Pilih berkas yang valid.')
        return identifier, name, path, digest.hexdigest()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
