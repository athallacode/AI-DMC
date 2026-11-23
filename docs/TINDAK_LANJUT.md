# Tindak Lanjut AI-DMC

Catatan diskusi 12 sampai 16 November 2026 yang belum dikerjakan. Urutan di tiap bagian sesuai prioritas yang disarankan.

## 1. Kecepatan pemrosesan dokumen

Hasil pengecekan 16 November: dokumen scan lambat karena OCR (PaddleOCR) berjalan di CPU. Saat diamati, satu dokumen lebih dari 2 menit di tahap OCR, memakai sekitar 10 dari 16 inti CPU, sementara GPU hanya 2%. Paddle yang terpasang versi CPU. Di uji 22 dokumen nyata: rata-rata 180 detik per dokumen, paling lama 734 detik (scan multi halaman). Model gemma4:e4b (6,6 GB) sedikit melebihi VRAM RTX 3050 (6 GB), jadi sebagian jalan di CPU. LLM dipanggil 3 kali untuk voting.

Opsi percepatan (ukur ulang dengan data uji tiap perubahan, catat detik yang dihemat dan akurasinya):
1. OCR hanya 2 sampai 3 halaman awal. Disarankan. Perkiraan 2 sampai 4 kali lebih cepat untuk scan; risiko isi lampiran (daftar dosen) tidak terbaca semua.
2. Model OCR versi mobile, sekitar 2 kali lebih cepat di CPU, akurasi sedikit turun di scan buram.
3. Lewati voting kalau jawaban pertama jelas; skor keyakinan perlu cara hitung lain.
4. OCR di GPU; tercepat tapi berebut VRAM 6 GB dengan gemma.

## 2. Backend dan alur unggah (sudah dicocokkan dengan rancangan DOK-CoE-AIIS-DMC-001)

1. **SK untuk banyak dosen.** Rancangan: dokumen yang memuat banyak dosen disimpan sekali lalu ditautkan ke setiap dosen. Sekarang dosen kedua yang mengunggah berkas yang sama hanya mendapat "Sudah pernah diunggah" dan tidak tertaut. Usulan: tautkan pengunggah kedua ke dokumen lama.
2. **Dokumen gagal tidak bisa diproses ulang.** Cek duplikat hash tidak melihat status, jadi dokumen `gagal` buntu. Usulan sesuai kontrak (tanpa endpoint baru): unggah ulang berkas yang statusnya `gagal` memproses ulang dokumen lama. Dokumen `ditolak` tetap final sesuai rancangan.
3. **Pesan duplikat** di laman Unggah belum memakai `document_id` untuk tautan ke dokumen (P2-05).
4. Selesai 23 November 2026: saat sesi habis, formulir koreksi meminta password tanpa menutup formulir, dan draf tersimpan di tab browser.
5. Selesai 23 November 2026: login dibatasi 5 kali gagal per username dalam 15 menit.
6. Prioritas rendah: laman Verifikasi dan "Baru diarsipkan AI" mengambil detail dokumen satu per satu; proses AI tanpa antrean terpisah sehingga unggahan banyak berkas saling memperlambat.
7. **Panduan dosen** (`docs/PANDUAN_DOSEN.md`) masih menulis bahwa menutup laman saat aksi tertunda membatalkan aksi; sekarang aksi justru langsung dikirim.

Catatan: sejak 23 November 2026, dokumen yang terputus restart dilanjutkan otomatis saat backend start.

## 3. Akurasi AI

- Data nyata (22 dokumen, satu dosen): kategori 40,9% kalau memakai label folder, 95,5% sampai 100% kalau memakai taksonomi. Perlu keputusan Admin CoE: SK pembimbing TA dan berita acara sidang masuk PND (taksonomi) atau PNJ (folder).
- Data dummy format nyata (`tools/generate_dummy_format_nyata.py`, 75 latih / 45 uji, belum di-commit): kategori 93,3%, jenis 86,7%. Semua dokumen yang lolos otomatis benar. Yang tertukar: surat tugas asesor dan narasumber, surat tugas reviewer, SK pembina dan kepanitiaan.
- Langkah berikut: validasi tanggal dan nomor dokumen harus tertulis di teks; contoh di prompt untuk jenis yang tertukar; perbaikan orientasi OCR (foto diputar 180 derajat). Fine-tune LoRA ditunda sampai ada sekitar 100 dokumen nyata.

## 4. Keamanan dan repo

- Ollama terbuka ke jaringan (`0.0.0.0:11434`) karena variabel sistem `OLLAMA_HOST`. Ubah ke `127.0.0.1:11434` lalu buka ulang Ollama. Ada dua instance Ollama berjalan.
- Selesai 23 November 2026: push sempat ditolak (403) karena akun GitHub `sofwanrsd` ditangguhkan oleh GitHub, bukan karena izin. Branch `feat/ai-asli-dan-perbaikan-ui` di-push dengan akun pemilik repositori dan diajukan sebagai Pull Request ke `main`.
