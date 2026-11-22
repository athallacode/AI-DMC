# Panduan Admin dan Pengelola AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Versi uji coba, November 2026

Panduan ini untuk dua peran:

- **Admin CoE**: memutuskan siapa yang dapat akun, menjawab pertanyaan dosen, menetapkan kategori dokumen.
- **Pengelola server**: menjalankan perintah di server atas permintaan Admin CoE.

Aplikasi belum punya laman admin. Semua tugas di panduan ini dikerjakan lewat perintah `app.kelola` di server. Perintah yang mengubah data wajib menyebut nama pengelola (`--oleh`) dan dicatat di log audit.

## 1. Cara menjalankan perintah

Masuk ke server lewat SSH, lalu ke folder aplikasi. Semua perintah berbentuk:

```
docker compose exec backend python -m app.kelola <kelompok> <perintah> [pilihan]
```

Untuk singkatnya, panduan ini menulis `kelola` sebagai pengganti `docker compose exec backend python -m app.kelola`.

Bantuan selalu tersedia:

```
kelola --help
kelola akun --help
kelola dokumen proses-ulang --help
```

Di laptop pengembang (tanpa Docker), jalankan dari folder `backend` dengan `PYTHONPATH=..` dan `python -m app.kelola`.

## 2. Mengelola akun

### Melihat semua akun

```
kelola akun daftar
```

### Membuat satu akun

```
kelola akun buat --username budi --nama "Budi Santoso" --nip 19800101 --oleh "Nama Pengelola"
```

- `--peran` boleh diisi `dosen` (bawaan) atau `admin`.
- **NIP wajib diisi untuk dosen.** Dosen hanya bisa tertaut ke dokumen lewat NIP.
- Password awal muncul **sekali** di layar. Sampaikan langsung ke dosennya, jangan lewat grup chat.

### Membuat banyak akun dari daftar dosen

1. Siapkan berkas CSV (bisa disimpan dari Excel sebagai **CSV UTF-8**) dengan kolom:

   | username | nama | nip | peran |
   |---|---|---|---|
   | budi | Budi Santoso | 19800101 | dosen |
   | sari | Sari Permata | 19850202 | |

   Kolom `peran` boleh kosong, isinya dianggap `dosen`.

2. Salin berkas ke container, jalankan impor, lalu ambil hasilnya:

   ```
   docker compose cp dosen.csv backend:/tmp/dosen.csv
   kelola akun impor /tmp/dosen.csv --keluar /tmp/password_awal.csv --oleh "Nama Pengelola"
   docker compose cp backend:/tmp/password_awal.csv ./password_awal.csv
   docker compose exec backend rm /tmp/dosen.csv /tmp/password_awal.csv
   ```

3. Baris yang bermasalah (username atau NIP sudah dipakai, nama kosong) dilewati dan disebutkan di layar. Baris lain tetap dibuat.
4. `password_awal.csv` berisi password semua akun baru. **Hapus berkas itu setelah password dibagikan.**

### Dosen lupa password

```
kelola akun reset-password budi --oleh "Nama Pengelola"
```

Password baru muncul sekali di layar. Pastikan yang meminta memang pemilik akun, misalnya datang langsung atau lewat email kampus.

### Dosen berhenti atau pindah tugas

```
kelola akun tutup budi --oleh "Nama Pengelola"
```

- Akun tidak bisa dipakai masuk lagi. Dokumennya tetap tersimpan.
- Sesi yang sedang terbuka tetap berlaku sampai habis, paling lama 60 menit.
- Untuk membuka akun lagi, pakai `reset-password`.

### Sebelum aplikasi dibuka untuk dosen

Akun dummy (`dosen1`, `dosen2`, `admin`) hanya untuk pengembangan. Tutup semuanya:

```
kelola akun tutup dosen1 --oleh "Nama Pengelola"
kelola akun tutup dosen2 --oleh "Nama Pengelola"
kelola akun tutup admin --oleh "Nama Pengelola"
```

Buat dulu akun admin pengganti dengan `akun buat --peran admin`.

## 3. Mengelola dokumen

### Melihat dokumen gagal

```
kelola dokumen gagal
```

Tampil kode dokumen, waktu unggah, pengunggah, nama berkas, dan penyebab singkat. Penyebab umum:

| Keterangan | Artinya | Tindakan |
|---|---|---|
| Pemrosesan terhenti saat layanan dimulai ulang | Server atau backend di-restart saat dokumen diproses | Proses ulang |
| Pemrosesan gagal | Berkas rusak, terkunci password, tidak ada teks terbaca, atau layanan AI mati | Cek Ollama jalan (`ollama ps`), lalu proses ulang. Kalau tetap gagal, minta dosen mengirim berkas yang lebih jelas |

### Memproses ulang dokumen gagal

```
kelola dokumen proses-ulang 1f2e3d4c-0000-4000-8000-123456789abc --oleh "Nama Pengelola"
```

- Hanya dokumen berstatus gagal yang bisa diproses ulang.
- Perintah menunggu sampai selesai, bisa beberapa menit untuk dokumen scan.
- Setelah selesai, dokumen masuk arsip atau Kotak Verifikasi dosen seperti unggahan biasa.

### SK bersama: menautkan dosen lain ke dokumen

Berkas yang persis sama hanya disimpan sekali. Kalau dosen B mendapat pesan "Sudah pernah diunggah" untuk SK yang sudah diunggah dosen A, tautkan dosen B ke dokumen milik A:

1. Minta kode dokumen ke dosen A, atau cari di database (lihat Bagian 6).
2. Jalankan:

   ```
   kelola dokumen tautkan <kode-dokumen> <username-dosen-B> --peran Anggota --oleh "Nama Pengelola"
   ```

Dosen B langsung bisa melihat dan mengunduh dokumen itu di Arsip. Ia tidak bisa menyetujui, menolak, atau mengoreksi; itu tetap hak pengunggah.

Dosen yang NIP-nya tertulis di dokumen sebenarnya tertaut otomatis setelah pengunggah menyetujui. Penautan manual hanya perlu kalau NIP tidak tertulis atau tidak terbaca AI.

## 4. Menjawab permintaan dosen

| Permintaan | Tindakan |
|---|---|
| Belum punya akun | Buat akun (Bagian 2) |
| Lupa password | `akun reset-password` |
| Dokumen berstatus Gagal | `dokumen proses-ulang` |
| "Sudah pernah diunggah" padahal belum | Cari pemilik dokumen, lalu `dokumen tautkan` |
| Salah menolak dokumen | Belum ada perintah. Catat kode dokumennya dan teruskan ke Admin CoE; perubahan status lewat database hanya dengan persetujuan Admin CoE |
| Minta dokumen dihapus | Belum ada perintah. Catat permintaannya, putuskan bersama Admin CoE sesuai Kebijakan Data |
| Hasil AI sering salah untuk jenis tertentu | Catat contoh dokumen dan jenis yang benar, teruskan ke tim pengembang |

## 5. Perawatan rutin

**Harian**

- Cek dokumen gagal: `kelola dokumen gagal`.
- Cek semua layanan jalan: `docker compose ps` (semua berstatus running atau healthy).
- Pastikan cadangan semalam berhasil (lihat Kebutuhan Server bagian 8).

**Mingguan**

- Cek sisa ruang disk: `df -h`.
- Lihat galat backend: `docker compose logs --since 168h backend | grep -i error`.

**Sebelum restart atau update**

Pastikan tidak ada dokumen yang sedang diproses, supaya tidak berubah menjadi gagal:

```
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT count(*) FROM documents WHERE status = 'diproses'"
```

Kalau hasilnya bukan 0, tunggu sebentar lalu cek lagi. Restart di luar jam kerja.

## 6. Pemeriksaan lewat database (hanya baca)

Untuk pertanyaan yang belum tersedia perintahnya, pengelola bisa membaca database. Masuk dengan:

```
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

Contoh kueri:

```sql
-- Mencari dokumen berdasarkan nama berkas (untuk kasus SK bersama)
SELECT d.id, u.username, d.nama_berkas, d.status
FROM documents d JOIN users u ON u.id = d.owner_id
WHERE d.nama_berkas ILIKE '%pengajaran%';

-- Jumlah dokumen per status
SELECT status, count(*) FROM documents GROUP BY status;

-- 20 aktivitas terakhir di log audit
SELECT a.created_at, u.username, a.aksi, a.document_id, a.detail
FROM audit_log a JOIN users u ON u.id = a.user_id
ORDER BY a.created_at DESC LIMIT 20;
```

Aturan:

- **Jangan mengubah data lewat SQL** (`UPDATE`, `DELETE`, `INSERT`) kecuali sudah disetujui Admin CoE dan dicatat. Log audit sendiri memang tidak bisa diubah atau dihapus.
- Jangan membuka kolom `teks` atau berkas di `storage/` kecuali untuk memperbaiki masalah yang dilaporkan.

Di log audit, aksi lewat perintah `kelola` bernama `kelola_...`. Kolom `user_id` berisi akun yang terdampak, dan nama pengelola ada di `detail.oleh`.

## 7. Batasan saat ini

- Belum ada laman admin di aplikasi.
- Belum ada perintah untuk menghapus dokumen, membatalkan status Ditolak, mengubah tingkat akses dokumen, atau mengubah nama dan NIP akun.
- Akun ditutup dengan mengganti password secara acak, bukan dengan status nonaktif.
- Ekspor riwayat koreksi baru tersedia lewat API `GET /admin/koreksi/export` dengan akun admin.

Rincian dan usulan perbaikannya ada di Kebijakan Data dan Keamanan, Bagian 10.
