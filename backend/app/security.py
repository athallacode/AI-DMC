import uuid
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import get_settings
from .database import get_db
from .models import User

hasher = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password):
    return hasher.hash(password)


def verify_password(password, encoded):
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def create_token(user):
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(user.id), 'iat': now, 'exp': now + timedelta(minutes=settings.jwt_expire_minutes)}, settings.jwt_secret, algorithm='HS256')


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if credentials is None:
        raise HTTPException(401, 'Silakan masuk terlebih dahulu.', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(credentials.credentials, get_settings().jwt_secret, algorithms=['HS256'], options={'require': ['sub', 'exp', 'iat']})
        user = db.get(User, uuid.UUID(payload['sub']))
    except (jwt.InvalidTokenError, ValueError, TypeError):
        user = None
    if user is None:
        raise HTTPException(401, 'Sesi berakhir. Silakan masuk kembali.', headers={'WWW-Authenticate': 'Bearer'})
    return user
