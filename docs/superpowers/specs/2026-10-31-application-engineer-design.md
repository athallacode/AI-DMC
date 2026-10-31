# Rancangan AI-DMC: Application Engineer

Tanggal: 31 Oktober 2026. Status: disetujui pengguna dalam chat sebelum implementasi. Pengguna juga mengonfirmasi lima tabel.

## Ruang lingkup

Kerjakan P2-01 sampai P2-24 dari Panduan Tim AI-DMC, serta fondasi bersama B-01, B-02, B-03 yang telah diizinkan pengguna. Integrasi asli, deploy server, uji dosen, review partner, dan pengiriman laporan memerlukan hasil kerja atau akses dari pihak terkait; jangan menyatakan selesai sebelum benar-benar dilakukan.

Tidak membangun OCR, ekstraksi teks, klasifikasi LLM, evaluasi model, atau taksonomi resmi milik Orang 1. Tidak mengirim pesan, membuat perubahan remote, atau mengklaim persetujuan partner.

## Pendekatan

Gunakan satu repositori dengan frontend Next.js, backend FastAPI, PostgreSQL, penyimpanan lokal storage/, dan Docker Compose. Pendekatan ini mengikuti kontrak tim dan memudahkan penggantian mock dengan pipeline asli.

Alternatif frontend dahulu dengan API tiruan mempercepat pratinjau tetapi menunda pembuktian kontrol akses dan penyimpanan. Alternatif backend dahulu menstabilkan kontrak tetapi menunda umpan balik tampilan. Pilihan yang disarankan adalah irisan alur lengkap: login, unggah, pemrosesan mock, verifikasi, lalu arsip.

## Batas komponen

- backend/app/api/: autentikasi, taksonomi, dokumen, ekspor koreksi admin.
- backend/app/models/ dan backend/alembic/: skema serta migrasi PostgreSQL.
- backend/app/services/: penyimpanan, hashing, transisi status, audit, adapter pipeline.
- backend/app/integrations/: mock sementara dan fixture taksonomi minimal yang ditandai sebagai data demo. Folder pipeline/ tetap milik Orang 1.
- frontend/: empat laman, komponen bersama, klien API dan token desain.
- docs/: kontrak yang disalin dari panduan, wireframe desktop/HP, cara menjalankan, checklist handoff.
- .agents/skills/ai-dmc-apple-glass-ui/SKILL.md: salinan panduan desain pengguna.

## Data dan autentikasi

Ikuti lima tabel yang secara eksplisit dirinci pada bagian 4.3: users, documents, dokumen_dosen, koreksi, audit_log. P2-03 menyebut enam tabel, tetapi tabel keenam tidak didefinisikan; usulan ini memakai lima tabel terdefinisi tanpa menciptakan entitas tambahan.

Gunakan UUID, waktu dengan zona waktu, JSONB untuk metadata dan snapshot koreksi, migrasi Alembic, password Argon2, JWT dengan masa berlaku, dan tiga akun seed khusus development. Rahasia dibaca dari environment. Endpoint dokumen memeriksa pemilik atau dosen tertaut; dokumen rahasia hanya boleh diakses pemilik. Tidak menambahkan pengecualian admin untuk membaca dokumen pengguna lain.

Audit bersifat append-only, termasuk login, unggah, persetujuan, koreksi, penolakan, dan unduh. Proteksi UPDATE/DELETE ditegakkan di PostgreSQL, bukan hanya konvensi kode. Ekspor koreksi hanya untuk admin.

## Alur berkas dan pipeline

Unggahan menerima PDF, DOCX, JPG, PNG, maksimal 20 MB per berkas. Validasi ekstensi dan isi dasar berkas, simpan memakai UUID, hitung SHA-256, dan tangani duplikat tanpa membocorkan dokumen pengguna lain. ID dokumen lama hanya dikembalikan jika pengguna mempunyai akses.

Background task menggunakan sesi database sendiri dan adapter process_document(file_path). Mode mock harus eksplisit di konfigurasi serta tampilan development. Sediakan skenario deterministik skor tinggi, skor rendah, dan gagal. Jangan menampilkan hasil mock sebagai hasil AI asli.

Hasil valid dipetakan ke dokumen dan dosen terkait, termasuk tautan pengunggah. Skor >= ambang environment (default 0.85) menghasilkan terverifikasi; skor lebih rendah menunggu_verifikasi. Kegagalan menjadi gagal dengan pesan yang dapat dipahami. Berkas yang masih diproses saat backend berhenti ditangani secara eksplisit saat startup; jangan dibiarkan diproses selamanya.

## Frontend dan interaksi

Gunakan panduan Apple light + glass pengguna: latar abu polos, kartu putih, satu aksen biru, Inter, Lucide, glass untuk navbar/modal/panel antrean/toast/toolbar yang mengambang. Lebar konten maksimum 1080 px, verifikasi dua kolom di desktop dan bertumpuk di HP, navigasi bawah di HP.

Empat laman: Login, Unggah, Kotak Verifikasi, Arsip Saya. Form koreksi terisi hasil AI, nilai kosong ditulis Tidak ditemukan, dropdown memakai /taxonomy. Polling antrean setiap 2–3 detik berhenti saat semua berkas selesai atau komponen ditutup.

Setujui dan Tolak menawarkan Urungkan selama tiga detik dengan menunda permintaan mutasi sampai tenggat berakhir. Urungkan membatalkan permintaan yang belum dikirim; UI menampilkan status tertunda dan mencegah aksi ganda. Pilihan ini memenuhi kebutuhan tanpa menambahkan endpoint baru pada kontrak tim. Penutupan laman sebelum permintaan dikirim membatalkan aksi tertunda.

Pratinjau PDF/gambar memakai endpoint berotorisasi; DOCX disediakan sebagai unduhan dengan keterangan yang jelas. Filter arsip mencakup kategori, status, tahun. Konfirmasi dosen terkait mengikuti persetujuan dokumen dan perubahan dicatat di audit.

## Urutan hasil kerja

1. Wireframe empat laman pada 375 px dan 1280 px, dokumen batas tugas, salinan skill desain.
2. Compose, environment example, skema/migrasi/seed, health dan autentikasi.
3. Unggah, kontrol akses, detail/unduh, adapter mock, threshold, daftar dan filter.
4. Frontend terhubung ke backend: login, unggah, verifikasi/koreksi, arsip.
5. Ekspor koreksi, audit append-only, pemeriksaan responsif/keyboard, panduan dosen dan README.
6. Handoff pipeline asli dan kesiapan deploy; verifikasi bersama dilakukan setelah dependensi tersedia.

## Verifikasi

Backend: migrasi pada PostgreSQL nyata, login valid/tidak valid, penolakan token kosong, unggahan campuran, duplikat, pembatasan 20 MB, akses silang dua dosen, rahasia, batas skor 0.85, pipeline gagal, snapshot koreksi, ekspor admin, penolakan UPDATE/DELETE audit. Frontend: build/typecheck, alur end-to-end mock, keyboard, focus modal, tampilan 375/1280 px dan screenshot. Data uji sintetis saja; data/, storage/, .env dan hasil lokal tidak masuk Git.

## Kriteria pelaporan

Bedakan selesai secara lokal, menunggu review partner, dan menunggu dependensi eksternal. Jangan menandai pipeline asli, deploy CoE, atau Definition of Done GitHub selesai hanya karena demo mock berhasil.
