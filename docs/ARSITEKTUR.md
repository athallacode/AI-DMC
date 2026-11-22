# Arsitektur Sistem AI-DMC (MVP)

Diagram di bawah digambar dari kode yang berjalan per 21 November 2026 (branch `feat/ai-asli-dan-perbaikan-ui`). Semua komponen jalan di satu mesin; tidak ada layanan AI publik.

## 1. Arsitektur sistem

```mermaid
flowchart LR
  subgraph Klien
    B[Browser dosen<br/>desktop / HP]
  end
  subgraph Aplikasi
    FE[Frontend<br/>Next.js 15 + React 19<br/>port 3000]
    API[Backend API<br/>FastAPI + Uvicorn<br/>port 8000]
    BG[Background task<br/>FastAPI, 1 worker]
  end
  subgraph Pipeline AI lokal
    EX[Ekstraksi teks<br/>PyMuPDF, python-docx]
    OCR[OCR<br/>PaddleOCR PP-OCRv6, CPU<br/>maks 5 halaman]
    CL[Klasifikasi + metadata<br/>saring injeksi, voting 3x]
    OL[Ollama<br/>gemma4:e4b<br/>port 11434]
  end
  subgraph Penyimpanan
    DB[(PostgreSQL 17<br/>Docker, 127.0.0.1:5432)]
    FS[[Folder storage<br/>berkas asli]]
    TX[[taxonomy.json<br/>7 kategori, 56 jenis]]
  end
  B -->|HTTP| FE
  FE -->|REST + JWT Bearer| API
  API -->|SQLAlchemy| DB
  API -->|simpan / baca berkas| FS
  API -->|GET /taxonomy| TX
  API -->|setelah unggah| BG
  BG -->|process_document| EX
  EX -->|halaman scan / foto| OCR
  EX --> CL
  OCR --> CL
  CL -->|structured output| OL
  CL -->|turunkan kategori dari jenis| TX
  BG -->|simpan hasil + status| DB
```

## 2. Alur pengguna (dosen)

```mermaid
flowchart TD
  A([Buka aplikasi]) --> L[Login username + password]
  L -->|gagal| L
  L --> U[Laman Unggah<br/>seret berkas / pindai kamera]
  U --> V{Tipe PDF/DOCX/JPG/PNG<br/>dan ukuran maks 20 MB?}
  V -->|tidak| E1[Pesan gagal di antrean]
  V -->|ya| D{Hash SHA-256<br/>sudah ada?}
  D -->|ya| E2[Sudah pernah diunggah]
  D -->|tidak| P[Status Diproses<br/>antrean bisa dikecilkan]
  P --> AI{Hasil AI}
  AI -->|error| G[Gagal<br/>hubungi pengelola]
  AI -->|skor 0,85 atau lebih| T[Terverifikasi otomatis]
  AI -->|skor di bawah 0,85| K[Kotak Verifikasi]
  T --> BA[Arsip: Baru diarsipkan AI]
  BA -->|Sudah benar| AR
  BA -->|Periksa| KO
  K --> F[Cek pratinjau, kategori,<br/>metadata, dosen terkait]
  F -->|Setujui| UR[Toast Urungkan 3 detik]
  F -->|Tolak| UR
  F -->|Koreksi| KO[Form koreksi<br/>dropdown taksonomi]
  UR -->|Urungkan| F
  UR -->|disetujui| AR[Arsip Saya<br/>cari, filter kategori/status/tahun]
  UR -->|ditolak| TL[Ditolak]
  KO -->|simpan| AR
```

## 3. Status dokumen

```mermaid
stateDiagram-v2
  [*] --> diproses: unggah
  diproses --> terverifikasi: skor >= 0,85
  diproses --> menunggu_verifikasi: skor < 0,85
  diproses --> gagal: pipeline error / layanan restart
  menunggu_verifikasi --> terverifikasi: Setujui / Koreksi
  menunggu_verifikasi --> ditolak: Tolak
  terverifikasi --> terverifikasi: Koreksi / Sudah benar
  terverifikasi --> ditolak: Tolak
  ditolak --> [*]
  gagal --> [*]
```

## 4. ERD

```mermaid
erDiagram
  users ||--o{ documents : "mengunggah (owner_id)"
  users ||--o{ dokumen_dosen : "tertaut (user_id, boleh kosong)"
  documents ||--o{ dokumen_dosen : "memuat dosen"
  documents ||--o{ koreksi : "dikoreksi"
  users ||--o{ koreksi : "mengoreksi"
  users ||--o{ audit_log : "melakukan"
  documents |o--o{ audit_log : "dicatat"
  documents |o--o{ documents : "versi (induk_versi)"

  users {
    uuid id PK
    text nama
    text nip UK
    text username UK
    text password_hash "Argon2"
    text peran "dosen | admin"
    timestamptz created_at
  }
  documents {
    uuid id PK
    uuid owner_id FK
    text nama_berkas
    text path_berkas
    varchar64 hash_sha256 UK
    text jenis_berkas
    text kategori
    text subkategori
    text jenis
    text judul
    text nomor_dokumen
    date tanggal_terbit
    text periode
    jsonb metadata_lain
    numeric skor_keyakinan "0 sampai 1"
    text ringkasan
    text teks
    text model_dipakai
    text status "5 status"
    text tingkat_akses "publik_coe | pribadi | rahasia"
    int versi
    uuid induk_versi FK
    timestamptz created_at
    timestamptz updated_at
  }
  dokumen_dosen {
    uuid id PK
    uuid document_id FK
    uuid user_id FK
    text nama
    text nip
    text peran
    bool dikonfirmasi
  }
  koreksi {
    uuid id PK
    uuid document_id FK
    uuid user_id FK
    jsonb sebelum
    jsonb sesudah
    timestamptz created_at
  }
  audit_log {
    uuid id PK
    uuid user_id FK
    text aksi "login, upload, unduh, approve, reject, koreksi"
    uuid document_id FK
    jsonb detail
    timestamptz created_at
  }
```

Catatan: `audit_log` dijaga trigger database sehingga tidak bisa di-UPDATE, DELETE, atau TRUNCATE dari aplikasi.

## 5. Sequence: unggah dan proses AI

```mermaid
sequenceDiagram
  autonumber
  actor Dosen
  participant FE as Frontend
  participant API as Backend API
  participant DB as PostgreSQL
  participant FS as storage/
  participant PL as Pipeline AI
  participant OL as Ollama

  Dosen->>FE: Pilih atau seret berkas
  FE->>API: POST /documents (multipart, JWT)
  loop tiap berkas, maks 20
    API->>FS: Tulis berkas, hitung SHA-256, cek tipe dan isi
    API->>DB: Cari hash yang sama
    alt duplikat
      API->>FS: Hapus berkas baru
    else baru
      API->>DB: INSERT documents (diproses), dokumen_dosen (Pengunggah), audit_log
    end
  end
  API-->>FE: documents[], duplicates[], errors[]
  API-)PL: Background task process_document(path)
  PL->>PL: Ekstrak teks, OCR bila scan atau foto
  PL->>PL: Saring kalimat injeksi, bungkus teks sebagai data
  loop 3 kali (suhu 0, 0,4, 0,4)
    PL->>OL: Pilih jenis + ekstrak metadata (JSON schema)
    OL-->>PL: Jawaban JSON
  end
  PL-->>API: Hasil + skor = porsi suara terbanyak
  API->>DB: UPDATE hasil, status sesuai ambang 0,85, dosen terkait
  loop tiap 2,5 detik selama ada yang diproses
    FE->>API: GET /documents/{id}
    API-->>FE: Status terbaru
  end
  FE-->>Dosen: Toast "N dokumen selesai diproses"
```

## 6. Sequence: verifikasi

```mermaid
sequenceDiagram
  autonumber
  actor Dosen
  participant FE as Frontend
  participant API as Backend API
  participant DB as PostgreSQL

  Dosen->>FE: Buka Kotak Verifikasi
  FE->>API: GET /documents?status=menunggu_verifikasi
  API-->>FE: Daftar ringkas
  FE->>API: GET /documents/{id} dan /file (pratinjau)
  API->>DB: audit_log unduh
  alt Setujui atau Tolak
    Dosen->>FE: Tekan Setujui
    FE-->>Dosen: Toast Urungkan 3 detik
    opt Dosen menekan Urungkan
      FE-->>Dosen: Aksi dibatalkan, tidak ada request
    end
    FE->>API: POST /documents/{id}/approve (atau keepalive saat laman ditutup)
    API->>DB: Kunci baris, status terverifikasi, dikonfirmasi = true, audit_log
    API-->>FE: Dokumen terbaru
  else Koreksi
    Dosen->>FE: Tekan Koreksi
    FE->>API: GET /taxonomy
    Dosen->>FE: Ubah field lalu Simpan
    FE->>API: PATCH /documents/{id}
    API->>API: Validasi kombinasi taksonomi
    API->>DB: Simpan perubahan, koreksi (sebelum, sesudah), audit_log, status terverifikasi
    API-->>FE: Dokumen terbaru
  end
```
