# Frontend AI-DMC

Bagian Orang 2. Empat halaman Next.js dengan desain Apple light + glass, bahasa Indonesia, Inter, dan Lucide.

## Menjalankan

Node.js 22 atau lebih baru. Jalankan backend terlebih dahulu dan seed akun sesuai backend/README.md.

```powershell
cd frontend
npm ci
$env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
npm run dev
```

Buka http://localhost:3000. Masuk dengan akun yang dibuat seed backend. JWT disimpan dalam sessionStorage untuk sesi tab; tombol Keluar menghapus token. Backend tetap menjadi penentu izin akses dokumen.

```powershell
npm run typecheck
npm run build
npm start
```

`NEXT_PUBLIC_API_URL` dibaca saat build. Build membutuhkan koneksi ke Google Fonts untuk `next/font/google` Inter. Docker menerima variabel yang sama sebagai build argument. Jangan memasukkan secret ke variabel NEXT_PUBLIC.

## Perilaku

- Unggah PDF, DOCX, JPG, PNG; maksimum 20 MB tiap berkas. Antrean menampilkan hasil per berkas dan polling tiap 2,5 detik selama ada dokumen diproses.
- Banner mode demo mengikuti `/health`; dropdown demo mengikuti `/taxonomy`. Hasil mock bukan hasil AI asli.
- Kotak Verifikasi memuat detail dan pratinjau berotorisasi. Setujui/Tolak menunggu tiga detik sebelum permintaan dikirim; Urungkan membatalkannya. Menutup halaman membatalkan aksi tertunda. Setelah permintaan terkirim, tidak ada pembatalan server.
- Koreksi menampilkan metadata dan dosen terkait yang terisi. Simpan dan setujui memakai PATCH dan backend menyimpan riwayat perubahan.
- PDF dan gambar dapat diperbesar. DOCX diunduh untuk dibuka dengan aplikasi dokumen.
- Arsip awal menampilkan dokumen terverifikasi; filter kategori, status, tahun terbit memanggil backend.
- Modal mendukung Esc, focus trap, dan pengembalian fokus. Navigasi HP menggunakan tab bar. Reduced motion dan reduced transparency dihormati.

Logo pada navigasi masih berupa wordmark teks Telkom University dan CoE AIIS. Ganti dengan aset logo resmi ketika tersedia.

## Pemeriksaan manual

Periksa 375 px dan 1280 px: login, unggah lima berkas, status selesai/gagal/duplikat, koreksi, setujui/tolak dengan Urungkan, filter arsip, dan pratinjau. Gunakan Tab/Shift+Tab/Enter/Esc. Pastikan fokus terlihat, modal tidak melepas fokus ke latar, tidak ada scroll horizontal, dan akun dosen lain tidak dapat mengambil berkas pengguna. Pemeriksaan browser lengkap membutuhkan backend yang berjalan.

Script `scripts/browser-check.mjs` menerima `QA_PASSWORD`, `QA_USERNAME`, `QA_FIXTURE_DIR`, `QA_FRONTEND_URL`, `QA_BACKEND_URL`, dan opsional `PLAYWRIGHT_MODULE` (path absolut modul Playwright). Gunakan database mock QA terisolasi dan fixture sintetis unik: high.pdf, low.pdf, low.docx, high.png, fail.png. Pengulangan dengan isi berkas sama akan dianggap duplikat; reset database QA atau buat isi fixture baru. Script menyimpan screenshot desktop/HP di docs/screenshots. `scripts/keyboard-check.mjs` menguji siklus Tab/Shift+Tab, Esc, dan pengembalian fokus pada modal; membutuhkan minimal satu dokumen menunggu verifikasi.
