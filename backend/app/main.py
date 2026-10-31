from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from .api import auth, documents
from .config import get_settings
from .database import SessionLocal, get_db
from .models import Correction, User
from .security import current_user
from .services.pipeline import mark_interrupted
from .services.taxonomy import load_taxonomy


@asynccontextmanager
async def lifespan(app):
    # MVP uses one worker. No durable task queue: explicitly fail interrupted jobs.
    with SessionLocal() as db:
        mark_interrupted(db)
    yield


app = FastAPI(title='AI-DMC API', version='0.1.0', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(','), allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Authorization', 'Content-Type'])
app.include_router(auth.router)
app.include_router(documents.router)


@app.get('/health')
def health(db: Session = Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'status': 'ok', 'pipeline_mode': get_settings().pipeline_mode, 'confidence_threshold': get_settings().confidence_threshold}


@app.get('/taxonomy')
def taxonomy(user: User = Depends(current_user)):
    return load_taxonomy()


@app.get('/admin/koreksi/export')
def export_corrections(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.peran != 'admin':
        raise HTTPException(403, 'Hanya admin yang dapat mengekspor koreksi.')
    return jsonable_encoder([{'id': row.id, 'document_id': row.document_id, 'user_id': row.user_id, 'sebelum': row.sebelum, 'sesudah': row.sesudah, 'created_at': row.created_at} for row in db.scalars(select(Correction).order_by(Correction.created_at)).all()])
