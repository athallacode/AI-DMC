# Backend AI-DMC

Bagian Orang 2: FastAPI, PostgreSQL, autentikasi, dokumen, koreksi dan audit. Tidak ada implementasi OCR atau LLM di sini. Mode default development memakai fixture sintetis di `app/integrations/mock.py`.

## Jalankan

Gunakan Python 3.12, PostgreSQL 16 atau lebih baru. Jalankan perintah dari folder `backend/`. Buat virtual environment lalu install `requirements.txt`. Salin `.env.example` di akar proyek menjadi `.env`; isi `JWT_SECRET` dengan nilai acak minimal 32 karakter dan `DATABASE_URL` PostgreSQL yang benar.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock
alembic upgrade head
$env:SEED_PASSWORD = 'Ganti-Dengan-Password-Dummy-Anda'
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Seed hanya berjalan pada `APP_ENVIRONMENT=development`, tidak mereset password akun yang sudah ada. Akun awal: `dosen1`, `dosen2`, `admin`; password memakai `SEED_PASSWORD`. Jangan gunakan akun dummy untuk production. Dokumentasi interaktif: `http://localhost:8000/docs`; health: `/health`.

`requirements.txt` mencatat rentang dependensi langsung; `requirements.lock` mematok versi yang telah diuji, termasuk dependensi transitif. Untuk pembaruan dependensi, install ulang dari rentang tersebut di virtual environment baru, jalankan pengujian, kemudian regenerasi lock.

Compose dan cara menjalankan seluruh aplikasi dijelaskan di README akar. Container menjalankan migrasi sebelum Uvicorn. Jalankan satu worker; background task MVP belum memakai antrean persisten. Pada startup, proses lama yang belum selesai ditandai gagal agar tidak menggantung. Gunakan satu instance backend selama fase MVP.

## Environment

| Variabel | Kegunaan |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://user:password@host:5432/database` |
| `JWT_SECRET` | Wajib, minimal 32 karakter |
| `JWT_EXPIRE_MINUTES` | Default 60 |
| `STORAGE_DIR` | Default `../storage`; path relatif terhadap working directory backend |
| `CONFIDENCE_THRESHOLD` | Default 0.85, rentang 0–1 |
| `CORS_ORIGINS` | Origin frontend dipisah koma, default `http://localhost:3000` |
| `PIPELINE_MODE` | `mock` atau `real` |
| `PIPELINE_IMPORT` | Default `pipeline.main:process_document` |
| `TAXONOMY_PATH` | Default `../pipeline/config/taxonomy.json` |
| `APP_ENVIRONMENT` | Default development; production menolak mode mock |
| `SEED_PASSWORD` | Hanya untuk perintah seed, minimal 12 karakter |

## Kontrak API

Login JSON `POST /auth/login` menerima `username,password`, menghasilkan `access_token,token_type,user`. Kirim token pada `Authorization: Bearer ...`. `/auth/me` menyediakan profil sesi. Seluruh endpoint dokumen, taksonomi dan ekspor membutuhkan token. File juga membutuhkan header token; frontend mengambil Blob berotorisasi untuk pratinjau.

`POST /documents` memakai multipart field `files` berulang (maksimal 20 berkas per permintaan, 20 MB per berkas). Response berisi `documents`, `duplicates`, dan `errors` supaya kegagalan satu berkas tidak membatalkan yang valid. SHA-256 unik global; duplikat milik orang lain tidak mengungkap ID. PDF/PNG/JPG diperiksa signature dasar; DOCX harus ZIP dengan `[Content_Types].xml` dan `word/document.xml`. Pemeriksaan ini bukan antivirus atau validasi penuh konten dokumen.

`GET /documents?status=&kategori=&tahun=` menghasilkan array. Tahun memakai tanggal terbit dokumen. `GET /documents/{id}` menghasilkan detail datar, `metadata_lain`, `dosen_terkait`, `error` dan `is_mock`. Tidak mengekspos path penyimpanan atau hash. `/file` mengirim berkas asli dan mencatat audit. Pemilik atau dosen tertaut boleh mengakses; dokumen rahasia hanya pemilik, termasuk terhadap admin.

`POST /documents/{id}/approve` mengonfirmasi dosen terkait; `/reject` menolak. `PATCH /documents/{id}` menerima field klasifikasi/metadata datar, `metadata_lain` dan `dosen_terkait:[{nama,nip,peran}]`, menyimpan snapshot lengkap sebelum/sesudah dan menyetujui dokumen. Ketiganya hanya menerima status menunggu_verifikasi atau terverifikasi. Perubahan konkurensi diserialkan dengan row lock pada PostgreSQL.

`GET /taxonomy` menghasilkan `{source,categories:[{kode,nama,subkategori:[{nama,jenis:[string]}]}]}`. Dalam mode mock, semua kategori ada tetapi subkategori selain PND hanyalah fixture sementara. Struktur taksonomi asli perlu disepakati dengan Orang 1 melalui adapter ini. `GET /admin/koreksi/export` hanya admin dan menghasilkan array snapshot koreksi JSON.

## Mock dan handoff Orang 1

Nama berkas mengandung `low` atau `rendah` menghasilkan skor 0.72; `fail` atau `gagal` menghasilkan kegagalan. Nama lain mendapat 0.91. Hasil ditandai `mock-development-only` dan judul `[MOCK]`. Ini bukan hasil membaca isi berkas. Ambang dibandingkan sebelum skor dibulatkan ke NUMERIC(3,2); skor 0.849 tetap menunggu walaupun tampilan dua desimal menjadi 0.85.

Untuk pipeline asli: sediakan modul importable di `PYTHONPATH`, atur `PIPELINE_MODE=real`, `PIPELINE_IMPORT` dan `TAXONOMY_PATH`, lalu jalankan uji handoff. Fungsi sinkron menerima path dan menghasilkan JSON sesuai PDF panduan bagian 4.1. Adapter memvalidasi skema, kategori/taksonomi, skor dan tanggal. Exception/output tidak valid menghasilkan status gagal dengan pesan aman. Orang 2 tidak menyediakan pipeline asli.

## Skema dan audit

Migrasi `0001` membuat lima tabel aplikasi dan tabel teknis `alembic_version`. Tabel teknis tersebut bukan tabel bisnis keenam. Trigger PostgreSQL menolak UPDATE, DELETE dan TRUNCATE pada audit_log. Pengelola DB tetap dapat mengubah skema sebagai administrator; pakai kredensial deployment yang dibatasi sesuai lingkungan CoE.

## Pengujian

```powershell
python -m pytest -q --basetemp=.test-tmp
```

Pengujian lokal memakai SQLite sementara melalui migrasi Alembic untuk alur API, kontrol akses, duplikat, validasi ukuran/format, threshold, snapshot koreksi, ekspor admin, audit append-only dan startup terhenti. Ini tidak menggantikan pengujian PostgreSQL untuk tipe JSONB, row lock, trigger PL/pgSQL dan Compose. Jalankan migrasi/seed serta skenario lintas dua dosen di PostgreSQL sebelum deploy.
