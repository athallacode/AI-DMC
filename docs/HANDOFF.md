# Handoff Application Engineer

Ruang lingkup: Orang 2 dan fondasi bersama yang disetujui. Tanggal: 31 Oktober 2026. Pipeline asli belum tersedia; seluruh hasil demo memakai mock sementara di backend/app/integrations/mock.py.

## Status lokal

| Tugas | Hasil dan batas pemeriksaan |
|---|---|
| B-01 sampai B-03 | Struktur proyek, skill desain, ignore data, environment example dan Compose tersedia. YAML Compose valid; belum dijalankan dengan Docker. |
| P2-01 | Delapan PNG wireframe 375/1280 px tersedia. Belum direview Orang 1. |
| P2-02 sampai P2-07 | Backend, migrasi lima tabel, seed, login, unggah, detail/berkas, filter dan endpoint taksonomi demo tersedia. PostgreSQL nyata belum diuji. |
| P2-08 sampai P2-10 | Layout, Login, Unggah, antrean dan polling tersedia; hasil build/browser dicatat pada bagian verifikasi. |
| P2-11 sampai P2-18 | Adapter mock, aturan ambang, mutasi dan koreksi, verifikasi/arsip, Urungkan tertunda, keyakinan/status, dosen terkait, ekspor admin tersedia. Pipeline asli dan taksonomi resmi menunggu Orang 1. |
| P2-19 | Dockerfile tersedia, belum dibangun atau diuji pada server CoE. |
| P2-20 | Panduan dosen tersedia di docs/PANDUAN_DOSEN.md, belum dibagikan atau dipakai uji dosen. |
| P2-21 | Layout responsif, fokus, modal keyboard dan reduced motion tersedia; hasil pemeriksaan browser dicatat di bawah. |
| P2-22 | Audit append-only, unduh tercatat. Trigger UPDATE/DELETE diuji dengan SQLite; PL/pgSQL dan TRUNCATE PostgreSQL belum diuji langsung. |
| P2-23 | Menunggu uji coba dosen; belum ada masukan eksternal. |
| P2-24 | README backend/frontend dan panduan root tersedia. |

Status ini bukan pengganti Definition of Done tim: review partner, PR dan merge ke dev belum dilakukan.

## Verifikasi aktual

- Backend: 11 tes integrasi lulus melalui pytest pada SQLite sementara yang dibuat memakai migrasi Alembic.
- Python compileall: lulus.
- PostgreSQL: SQL migrasi berhasil dikompilasi offline; ini tidak memeriksa perilaku server PostgreSQL.
- Compose: YAML berhasil dibaca, tiga service terdefinisi. Docker tidak terpasang sehingga build image, health dependency dan permission volume belum diverifikasi.
- Wireframe: delapan PNG dibuat; referensi HP kartu verifikasi diperiksa secara visual.

- Frontend: TypeScript lulus dan production build bersih lulus untuk seluruh route.
- Browser Chrome: unggah lima berkas campuran, status mock tinggi/rendah/gagal, Urungkan, persetujuan tertunda, koreksi tersimpan/terverifikasi, dan filter kategori/status arsip lulus. Tidak ada error JavaScript halaman pada alur tersebut.
- Responsif: tidak ditemukan overflow horizontal pada 375 px dan 1280 px di laman yang diperiksa. Sepuluh screenshot sintetis disimpan di docs/screenshots/.
- Keyboard: 30 siklus Tab dan 30 Shift+Tab tetap berada dalam modal; Esc menutup modal dan mengembalikan fokus ke pemicu.
- Modal arsip: tombol Perbesar tidak ditampilkan lagi di dalam modal agar tidak membuat modal bertumpuk. Delapan siklus Tab tetap dalam dialog dan Esc menutupnya. Viewer PDF dilewati saat Tab; tombol Unduh tetap dapat dipakai keyboard untuk membuka dokumen di pembaca PDF.
- Pratinjau PDF: halaman dokumen sintetis berhasil tampil ketika viewer berada dalam viewport; screenshot tersedia. Area iframe PDF di luar viewport pada screenshot full-page bisa belum dirender oleh Chrome.
- Pengujian browser memakai database SQLite khusus QA dan mode mock. Ini belum membuktikan integrasi pipeline asli atau database PostgreSQL.

## Handoff ke Orang 1

1. Sediakan process_document(file_path) sinkron dengan JSON sesuai bagian 4.1 panduan tim. Mode sukses memerlukan jenis_berkas, klasifikasi, skor_keyakinan dan metadata. Field yang tidak ditemukan harus null.
2. Sepakati bentuk JSON taksonomi. Adapter sementara mengekspos categories → kode/nama/subkategori → nama/jenis. Bentuk file taksonomi tidak dirinci di PDF, jadi ini kontrak adapter sementara, bukan klaim keputusan tim yang sudah disepakati.
3. Sediakan modul pipeline importable dan file taksonomi. Atur PIPELINE_MODE=real, PIPELINE_IMPORT dan TAXONOMY_PATH. Pada container, tambahkan mount read-only pipeline ke /app/pipeline dan PYTHONPATH=/app; dependency pipeline harus dipasang pada image oleh integrasi bersama.
4. Jalankan sepuluh dokumen sintetis campuran sebelum memakai data asli dengan izin yang sesuai. Pastikan skenario sukses, skor rendah, gagal, dan metadata kosong terwakili.
5. Login admin dapat mengambil JSON koreksi dari GET /admin/koreksi/export. Endpoint ini belum diserahkan ke partner secara eksternal.

## Sebelum deploy atau uji dosen

- Sediakan Docker/PostgreSQL, jalankan migrasi dan seed development. Ulangi kontrol akses lintas dua dosen, jenis JSONB, row lock, serta trigger UPDATE/DELETE/TRUNCATE pada PostgreSQL nyata.
- Pastikan direktori storage dapat ditulis oleh user container; bind mount pada host Linux memerlukan ownership/permission yang sesuai. Jangan membuatnya dapat diakses publik lewat web server.
- Buat kredensial asli dan rahasia baru, nonaktifkan akun dummy, atur PIPELINE_MODE=real dan APP_ENVIRONMENT=production. Backend sengaja menolak production yang masih mock.
- Sediakan logo resmi. Navigasi sementara memakai wordmark teks; tidak mengklaim aset logo resmi sudah terpasang.
- Atur domain/HTTPS, origin frontend, akses server, backup berkas + database, dan satu worker backend selama background task belum memakai antrean persisten.
- Review partner dan approval kontrak, uji dosen, deployment kampus, dan laporan akhir dilakukan setelah dependensi tersedia. Tidak ada pesan atau perubahan GitHub remote yang dikirim dari pekerjaan lokal ini.

## Sumber teknis

Implementasi background task mengikuti [dokumentasi FastAPI](https://fastapi.tiangolo.com/tutorial/background-tasks/). Minimum patch Next.js diperiksa terhadap [pembaruan resmi 14 Oktober 2026](https://nextjs.org/blog/nextjs-security-update-october-14-2026). Versi yang benar-benar terpasang dikunci oleh lockfile masing-masing layanan.
