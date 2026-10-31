import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

JSONType = JSON().with_variant(JSONB(), 'postgresql')


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text)
    nip: Mapped[str | None] = mapped_column(Text, unique=True)
    username: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    peran: Mapped[str] = mapped_column(Text, default='dosen')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint("peran IN ('dosen','admin')"),)


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'), index=True)
    nama_berkas: Mapped[str] = mapped_column(Text)
    path_berkas: Mapped[str] = mapped_column(Text)
    hash_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    jenis_berkas: Mapped[str | None] = mapped_column(Text)
    kategori: Mapped[str | None] = mapped_column(Text, index=True)
    subkategori: Mapped[str | None] = mapped_column(Text)
    jenis: Mapped[str | None] = mapped_column(Text)
    judul: Mapped[str | None] = mapped_column(Text)
    nomor_dokumen: Mapped[str | None] = mapped_column(Text)
    tanggal_terbit: Mapped[date | None] = mapped_column(Date)
    periode: Mapped[str | None] = mapped_column(Text)
    metadata_lain: Mapped[dict] = mapped_column(JSONType, default=dict)
    skor_keyakinan: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    ringkasan: Mapped[str | None] = mapped_column(Text)
    teks: Mapped[str | None] = mapped_column(Text)
    model_dipakai: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default='diproses', index=True)
    tingkat_akses: Mapped[str] = mapped_column(Text, default='pribadi')
    versi: Mapped[int] = mapped_column(Integer, default=1)
    induk_versi: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('documents.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    __table_args__ = (
        CheckConstraint("status IN ('diproses','menunggu_verifikasi','terverifikasi','ditolak','gagal')"),
        CheckConstraint("tingkat_akses IN ('publik_coe','pribadi','rahasia')"),
        CheckConstraint('skor_keyakinan >= 0 AND skor_keyakinan <= 1'),
    )


class DocumentLecturer(Base):
    __tablename__ = 'dokumen_dosen'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('documents.id'), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('users.id'), index=True)
    nama: Mapped[str] = mapped_column(Text)
    nip: Mapped[str | None] = mapped_column(Text)
    peran: Mapped[str | None] = mapped_column(Text)
    dikonfirmasi: Mapped[bool] = mapped_column(Boolean, default=False)


class Correction(Base):
    __tablename__ = 'koreksi'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('documents.id'), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    sebelum: Mapped[dict] = mapped_column(JSONType)
    sesudah: Mapped[dict] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditLog(Base):
    __tablename__ = 'audit_log'
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    aksi: Mapped[str] = mapped_column(Text)
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey('documents.id'))
    detail: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
