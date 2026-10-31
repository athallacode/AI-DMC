"""Explicit development-only, idempotent seed. Password comes from SEED_PASSWORD."""
from sqlalchemy import select
from .config import get_settings
from .database import SessionLocal
from .models import User
from .security import hash_password


def main():
    settings = get_settings()
    if settings.app_environment != 'development':
        raise SystemExit('Seed hanya untuk development.')
    if not settings.seed_password or len(settings.seed_password) < 12:
        raise SystemExit('Isi SEED_PASSWORD minimal 12 karakter untuk akun dummy.')
    with SessionLocal() as db:
        for username, name, role, nip in [('dosen1', 'Dosen Satu (Dummy)', 'dosen', 'DUMMY-001'), ('dosen2', 'Dosen Dua (Dummy)', 'dosen', 'DUMMY-002'), ('admin', 'Admin (Dummy)', 'admin', None)]:
            if not db.scalar(select(User).where(User.username == username)):
                db.add(User(username=username, nama=name, peran=role, nip=nip, password_hash=hash_password(settings.seed_password)))
        db.commit()
    print('Akun development tersedia: dosen1, dosen2, admin. Password dari SEED_PASSWORD.')


if __name__ == '__main__':
    main()
