import time
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest
from ..security import current_user, verify_password, create_token, hash_password
from ..services.documents import audit

router = APIRouter(prefix='/auth', tags=['auth'])
DUMMY_HASH = hash_password('constant-dummy-password-for-timing')


def public_user(user):
    return {'id': str(user.id), 'nama': user.nama, 'username': user.username, 'peran': user.peran}


class PembatasLogin:
    """Batas percobaan login per username, disimpan di memori (backend berjalan 1 worker).

    Sengaja per username, bukan per IP: di server semua permintaan datang lewat reverse proxy
    dengan IP yang sama, jadi batas per IP akan mengunci semua dosen sekaligus.
    Username yang tidak terdaftar ikut dihitung supaya respons tidak membedakan akun ada atau tidak.
    """

    def __init__(self):
        self._gagal: dict[str, list[float]] = {}
        self._kunci = Lock()

    def _jendela(self):
        return get_settings().login_kunci_menit * 60

    def _bersihkan(self, sekarang):
        batas = sekarang - self._jendela()
        for kunci in [k for k, waktu in self._gagal.items() if not waktu or waktu[-1] < batas]:
            del self._gagal[kunci]

    def sisa_kunci(self, username) -> int:
        """Detik sampai username boleh mencoba lagi; 0 kalau tidak terkunci."""
        sekarang = time.monotonic()
        with self._kunci:
            self._bersihkan(sekarang)
            waktu = [w for w in self._gagal.get(username.lower(), []) if w > sekarang - self._jendela()]
            if len(waktu) < get_settings().login_maks_gagal:
                return 0
            return max(1, int(waktu[0] + self._jendela() - sekarang))

    def catat_gagal(self, username):
        with self._kunci:
            self._gagal.setdefault(username.lower(), []).append(time.monotonic())

    def reset(self, username=None):
        with self._kunci:
            if username is None:
                self._gagal.clear()
            else:
                self._gagal.pop(username.lower(), None)


pembatas = PembatasLogin()


@router.post('/login')
def login(body: LoginRequest, db: Session = Depends(get_db)):
    sisa = pembatas.sisa_kunci(body.username)
    if sisa:
        menit = -(-sisa // 60)
        raise HTTPException(429, f'Terlalu banyak percobaan masuk yang gagal. Coba lagi dalam {menit} menit atau hubungi pengelola.')
    user = db.scalar(select(User).where(User.username == body.username))
    valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        pembatas.catat_gagal(body.username)
        if user:
            audit(db, user.id, 'login_gagal')
            db.commit()
        raise HTTPException(401, 'Username atau password tidak sesuai.')
    pembatas.reset(body.username)
    audit(db, user.id, 'login')
    db.commit()
    return {'access_token': create_token(user), 'token_type': 'bearer', 'user': public_user(user)}


@router.get('/me')
def me(user: User = Depends(current_user)):
    return public_user(user)
