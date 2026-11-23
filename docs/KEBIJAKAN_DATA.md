# Kebijakan Data dan Keamanan AI-DMC

AI Document Management Center, CoE AIIS Telkom University
Draf untuk ditetapkan CoE, November 2026

Dokumen ini menjelaskan data apa yang disimpan AI-DMC, siapa yang bisa melihatnya, dan aturan yang berlaku bagi dosen dan pengelola. Isinya disusun dari kode di branch `feat/ai-asli-dan-perbaikan-ui` per 22 November 2026. Bagian 10 memuat hal yang belum terpenuhi, dan Bagian 11 memuat hal yang perlu diputuskan CoE.

Dokumen ini bukan nasihat hukum. Kesesuaian dengan UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi dan aturan internal Telkom University sebaiknya dicek oleh unit hukum atau pengelola data kampus.

## 1. Ruang lingkup

Berlaku untuk:

- aplikasi AI-DMC (frontend, backend, database, folder berkas, layanan AI),
- server tempat aplikasi berjalan, termasuk cadangannya,
- semua pengguna: dosen, Admin CoE, dan pengelola server.

## 2. Data yang disimpan

| Data | Contoh | Tempat |
|---|---|---|
| Akun pengguna | Nama, username, NIP, peran, hash password | Database |
| Berkas dokumen | PDF, DOCX, JPG, PNG yang diunggah | Folder `storage/` di server, nama berkas diganti kode acak |
| Teks dokumen | Teks hasil ekstraksi PDF atau OCR | Database |
| Metadata hasil AI | Jenis, judul, nomor, tanggal, periode, ringkasan, skor keyakinan | Database |
| Dosen terkait | Nama, NIP, peran dosen yang disebut di dokumen | Database |
| Riwayat koreksi | Nilai sebelum dan sesudah dikoreksi dosen | Database |
| Log audit | Siapa, kapan, aksi apa, dokumen mana | Database |

Dokumen eviden sering memuat **data pribadi orang lain**, bukan hanya pengunggah: NIP dosen lain di SK bersama, nama dan NIM mahasiswa beserta nilainya di daftar nilai, dan nama mahasiswa di berita acara sidang. Seluruh isi dokumen diperlakukan sebagai data pribadi.

Yang **tidak** disimpan: password dalam bentuk asli (hanya hash Argon2), dan isi dokumen di log aplikasi secara sengaja. Kalau proses gagal, log mencatat kode dokumen dan pesan galat.

## 3. Pemrosesan AI

- **Semua pemrosesan AI berjalan di server sendiri.** OCR memakai PaddleOCR, klasifikasi memakai model Gemma lewat Ollama. Keduanya berjalan lokal.
- **Tidak ada dokumen atau teks yang dikirim ke layanan AI publik** (OpenAI, Google, Anthropic, dan sejenisnya). Aturan ini tertulis di pedoman proyek dan wajib dijaga saat pengembangan lanjutan.
- Internet hanya dipakai sekali saat pemasangan, untuk mengunduh model dan image Docker.
- **Teks dokumen diperlakukan sebagai data, bukan perintah.** Kalimat di dokumen yang menyerupai perintah ke AI disaring sebelum dikirim ke model, dan dokumen itu otomatis masuk Kotak Verifikasi.
- **AI tidak mengarang data.** Field yang tidak tertulis di dokumen dikosongkan.
- **Hasil AI bukan keputusan akhir.** Dosen tetap memeriksa, terutama sebelum data dipakai untuk keperluan administrasi resmi.

## 4. Hak akses

| Pengguna | Bisa melihat |
|---|---|
| Dosen pengunggah | Semua dokumen yang ia unggah |
| Dosen lain yang tertaut | Dokumen tempat NIP-nya tercantum, **setelah pengunggah menyetujui**, kecuali dokumen bertingkat akses **rahasia**. Hanya melihat dan mengunduh |
| Admin CoE (akun aplikasi) | Hanya dokumen yang ia unggah atau tempat ia tertaut. Mengelola akun, memproses ulang dokumen gagal, dan menautkan SK bersama lewat laman Admin (atau perintah `app.kelola` di server). Tidak bisa membuka isi dokumen dosen lain (lihat Panduan Admin) |
| Pengelola server | Secara teknis bisa membaca seluruh database dan folder berkas. Karena itu dibatasi lewat aturan di Bagian 8 |

Cara dosen lain tertaut ke dokumen:

1. AI membaca NIP dosen yang disebut di dokumen.
2. Kalau NIP itu milik akun terdaftar, dosen tersebut ditandai sebagai calon dosen terkait. Ia **belum bisa melihat dokumen**.
3. Pengunggah memeriksa daftar dosen terkait, lalu menyetujui atau mengoreksi. Pengunggah bisa menambah atau menghapus dosen terkait lewat form koreksi.
4. Setelah disetujui, dosen terkait yang punya akun bisa melihat dan mengunduh dokumen itu.

Menyetujui, menolak, dan mengoreksi hanya bisa dilakukan pengunggah. Dosen tertaut yang mencoba akan ditolak sistem.

Dokumen yang langsung diarsipkan AI juga mengikuti aturan ini: dosen terkait baru bisa melihatnya setelah pengunggah menekan **Sudah benar** atau menyimpan koreksi.

Tingkat akses dokumen ada tiga di database: `pribadi` (bawaan), `publik_coe`, dan `rahasia`. Saat ini belum ada tombol untuk mengubahnya dari aplikasi, dan `publik_coe` belum dipakai dalam aturan akses.

## 5. Akun dan sesi

- Akun dibuat oleh pengelola. Tidak ada pendaftaran mandiri.
- Password disimpan sebagai hash Argon2.
- Sesi berlaku **60 menit** dan berakhir saat tab browser ditutup.
- Draf koreksi yang belum tersimpan disimpan sementara di browser dosen (sessionStorage tab itu), supaya tidak hilang saat sesi habis. Draf tidak dikirim ke server dan terhapus saat dosen menekan Keluar atau menutup tab.
- Akun dummy (`dosen1`, `dosen2`, `admin`) hanya untuk pengembangan. **Wajib dihapus atau diganti password-nya sebelum dipakai dosen.**
- Saat dipindah ke server, rahasia baru wajib dibuat: password database, kunci JWT, dan password awal akun. Nilainya disimpan di `.env` di server dan tidak boleh masuk repositori.

## 6. Log audit

Aksi yang dicatat, beserta pelaku dan waktunya:

| Aksi | Keterangan |
|---|---|
| login | Masuk berhasil |
| login_gagal | Password salah untuk akun yang terdaftar |
| upload | Unggah dokumen, beserta nama berkas |
| unduh | Membuka atau mengunduh berkas |
| approve | Menyetujui hasil AI |
| reject | Menolak dokumen |
| koreksi | Mengoreksi hasil AI, beserta daftar field yang diubah |

Log audit tidak memuat isi dokumen. Log hanya dibaca pengelola untuk menelusuri masalah atau dugaan penyalahgunaan.

## 7. Penyimpanan, cadangan, dan penghapusan

- Server berada di kampus (on-premise). Database dan berkas tidak disimpan di layanan cloud.
- Hanya port HTTPS yang dibuka ke jaringan kampus. Database, backend, dan layanan AI hanya bisa diakses dari mesin server itu sendiri.
- Folder berkas tidak disajikan langsung oleh web server. Berkas hanya bisa diunduh lewat aplikasi setelah hak akses dicek.
- **Cadangan:** salinan database dan folder berkas setiap hari, disimpan di disk atau NAS terpisah, minimal 7 hari terakhir. Cadangan berisi data yang sama sensitifnya, jadi disimpan di tempat terkunci dan hanya bisa diakses pengelola.
- **Penghapusan:** aplikasi belum punya fitur hapus. Dokumen yang ditolak tetap tersimpan. Permintaan hapus dari dosen ditangani pengelola langsung di server dan dicatat. Lihat Bagian 11 untuk masa simpan.
- Unggahan yang sama persis dengan dokumen yang sudah ada tidak disimpan dua kali.

## 8. Kewajiban

**Dosen**

- Hanya mengunggah dokumen eviden kegiatan sendiri.
- Tidak membagikan password, dan keluar dari akun setelah memakai komputer bersama.
- Memeriksa hasil AI, termasuk daftar dosen terkait, karena setelah disetujui, dosen yang tertaut ikut bisa melihat dokumen.
- Tidak mengirim dokumen atau password lewat grup chat saat melaporkan masalah. Cukup sebut nama berkas dan waktu unggah.

**Admin CoE**

- Menetapkan pembagian kategori dan jenis dokumen.
- Menyetujui pembuatan dan penonaktifan akun dosen.
- Menjadi tempat dosen melapor dugaan kebocoran atau salah akses.

**Pengelola server**

- Tidak membuka isi dokumen dosen kecuali untuk memperbaiki masalah yang dilaporkan, dan mencatat setiap akses semacam itu.
- Menjaga `.env`, kunci SSH, dan cadangan. Akses SSH memakai kunci, bukan password.
- Menutup akun dosen yang pindah tugas atau berhenti dengan `kelola akun tutup` (lihat Panduan Admin).
- Memasang pembaruan keamanan sistem operasi secara berkala.
- Tidak menambahkan panggilan ke layanan AI publik dalam kode.

## 9. Penanganan insiden

Insiden meliputi: akun dipakai orang lain, dokumen terlihat oleh orang yang tidak berhak, server atau cadangan hilang, atau dokumen terkirim ke luar kampus.

1. Pelapor menghubungi Admin CoE secepatnya.
2. Pengelola mengamankan sistem: menonaktifkan akun terkait, mengganti password atau kunci, atau mematikan akses dari jaringan kalau perlu.
3. Pengelola menelusuri log audit untuk mengetahui dokumen apa yang terdampak dan siapa yang mengaksesnya.
4. Admin CoE memberi tahu dosen yang datanya terdampak, dan melapor ke unit kampus yang berwenang sesuai aturan pelindungan data pribadi.
5. Penyebab dicatat dan diperbaiki sebelum sistem dibuka kembali.

## 10. Hal yang belum terpenuhi

Temuan dari kode per 22 November 2026, diurutkan dari yang paling penting. Dua celah hak akses dosen tertaut sudah ditutup pada 22 November 2026 (lihat Bagian 4).

| No | Hal | Dampak | Usulan |
|---|---|---|---|
| 1 | Akun tidak punya status aktif atau nonaktif | Akun ditutup dengan mengganti password secara acak (`kelola akun tutup`). Sesi yang sedang terbuka tetap berlaku sampai habis | Tambah status aktif pada akun |
| 2 | Batas percobaan login hanya per akun (5 kali gagal dalam 15 menit, akun terkunci 15 menit). Login gagal sudah dicatat di log audit (`login_gagal`) | Orang lain bisa sengaja mengunci akun dosen selama 15 menit | Tambah batas per alamat IP setelah reverse proxy meneruskan IP asli |
| 3 | Belum ada skrip cadangan | Data hilang kalau disk rusak | Pasang skrip cadangan harian sebelum dipakai dosen |
| 4 | Berkas di folder `storage/` tidak dienkripsi | Siapa pun yang memegang disk atau cadangan bisa membaca dokumen | Enkripsi disk server dan disk cadangan |
| 5 | Belum ada fitur hapus dan masa simpan | Dokumen yang salah unggah tersimpan selamanya | Tetapkan masa simpan, buat prosedur hapus oleh pengelola |
| 6 | Tingkat akses tidak bisa diatur dari aplikasi | Dokumen sensitif tidak bisa ditandai rahasia oleh dosen | Tambah pilihan tingkat akses di form koreksi |
| 7 | Laman Admin belum bisa menghapus dokumen atau mengubah nama dan NIP akun | Permintaan seperti itu masih ditangani pengelola server bersama Admin CoE | Tambah laman admin sederhana |
| 8 | Belum ada HTTPS dan reverse proxy di konfigurasi deploy | Password dan dokumen lewat jaringan tanpa enkripsi | Pasang HTTPS sebelum dibuka ke dosen (lihat Kebutuhan Server) |
| 9 | Token sesi disimpan di sessionStorage browser | Rentan dicuri kalau ada celah skrip di halaman | Pertimbangkan cookie HttpOnly saat pengembangan lanjutan |

## 11. Keputusan yang perlu ditetapkan CoE

- [ ] Siapa Admin CoE dan siapa pengelola server.
- [ ] Masa simpan dokumen, misalnya selama dosen aktif ditambah sekian tahun, dan masa simpan log audit.
- [ ] Masa simpan dokumen berstatus Ditolak.
- [ ] Apakah daftar nilai yang berisi data mahasiswa boleh diunggah utuh, atau cukup halaman rekap.
- [ ] Prosedur pelaporan insiden ke unit kampus.
- [ ] Siapa yang menandatangani kebijakan ini dan kapan ditinjau ulang (usulan: setiap tahun).

---

Disahkan oleh: ______________________ Tanggal: ____________
