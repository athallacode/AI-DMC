from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest
from ..security import current_user, verify_password, create_token, hash_password
from ..services.documents import audit

router = APIRouter(prefix='/auth', tags=['auth'])
DUMMY_HASH = hash_password('constant-dummy-password-for-timing')


def public_user(user):
    return {'id': str(user.id), 'nama': user.nama, 'username': user.username, 'peran': user.peran}


@router.post('/login')
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, 'Username atau password tidak sesuai.')
    audit(db, user.id, 'login')
    db.commit()
    return {'access_token': create_token(user), 'token_type': 'bearer', 'user': public_user(user)}


@router.get('/me')
def me(user: User = Depends(current_user)):
    return public_user(user)
