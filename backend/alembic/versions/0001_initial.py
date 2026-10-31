"""Five application tables and database-enforced append-only audit log."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    json_type = sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')
    timestamp = sa.DateTime(timezone=True)
    op.create_table('users',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('nama', sa.Text(), nullable=False),
        sa.Column('nip', sa.Text(), unique=True),
        sa.Column('username', sa.Text(), unique=True, nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('peran', sa.Text(), nullable=False),
        sa.Column('created_at', timestamp, nullable=False),
        sa.CheckConstraint("peran IN ('dosen','admin')"))
    op.create_table('documents',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('owner_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('nama_berkas', sa.Text(), nullable=False),
        sa.Column('path_berkas', sa.Text(), nullable=False),
        sa.Column('hash_sha256', sa.String(64), unique=True, nullable=False),
        *[sa.Column(field, sa.Text()) for field in ['jenis_berkas', 'kategori', 'subkategori', 'jenis', 'judul', 'nomor_dokumen', 'periode', 'ringkasan', 'teks', 'model_dipakai']],
        sa.Column('tanggal_terbit', sa.Date()),
        sa.Column('metadata_lain', json_type, nullable=False),
        sa.Column('skor_keyakinan', sa.Numeric(3, 2)),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('tingkat_akses', sa.Text(), nullable=False),
        sa.Column('versi', sa.Integer(), nullable=False),
        sa.Column('induk_versi', sa.Uuid(), sa.ForeignKey('documents.id')),
        sa.Column('created_at', timestamp, nullable=False),
        sa.Column('updated_at', timestamp, nullable=False),
        sa.CheckConstraint("status IN ('diproses','menunggu_verifikasi','terverifikasi','ditolak','gagal')"),
        sa.CheckConstraint("tingkat_akses IN ('publik_coe','pribadi','rahasia')"),
        sa.CheckConstraint('skor_keyakinan >= 0 AND skor_keyakinan <= 1'))
    for field in ['owner_id', 'kategori', 'status']:
        op.create_index(f'ix_documents_{field}', 'documents', [field])
    op.create_table('dokumen_dosen',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('document_id', sa.Uuid(), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id')),
        sa.Column('nama', sa.Text(), nullable=False),
        sa.Column('nip', sa.Text()),
        sa.Column('peran', sa.Text()),
        sa.Column('dikonfirmasi', sa.Boolean(), nullable=False))
    op.create_index('ix_dokumen_dosen_document_id', 'dokumen_dosen', ['document_id'])
    op.create_index('ix_dokumen_dosen_user_id', 'dokumen_dosen', ['user_id'])
    op.create_table('koreksi',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('document_id', sa.Uuid(), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('sebelum', json_type, nullable=False),
        sa.Column('sesudah', json_type, nullable=False),
        sa.Column('created_at', timestamp, nullable=False))
    op.create_index('ix_koreksi_document_id', 'koreksi', ['document_id'])
    op.create_table('audit_log',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('user_id', sa.Uuid(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('aksi', sa.Text(), nullable=False),
        sa.Column('document_id', sa.Uuid(), sa.ForeignKey('documents.id')),
        sa.Column('detail', json_type, nullable=False),
        sa.Column('created_at', timestamp, nullable=False))
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""CREATE FUNCTION prevent_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'audit_log is append-only'; END; $$""")
        op.execute('CREATE TRIGGER audit_log_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON audit_log FOR EACH STATEMENT EXECUTE FUNCTION prevent_audit_mutation()')
    elif op.get_bind().dialect.name == 'sqlite':
        for action in ['UPDATE', 'DELETE']:
            op.execute(f"CREATE TRIGGER audit_log_no_{action.lower()} BEFORE {action} ON audit_log BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END")


def downgrade():
    if op.get_bind().dialect.name == 'postgresql':
        op.execute('DROP TRIGGER audit_log_immutable ON audit_log')
        op.execute('DROP FUNCTION prevent_audit_mutation()')
    for table in ['audit_log', 'koreksi', 'dokumen_dosen', 'documents', 'users']:
        op.drop_table(table)
