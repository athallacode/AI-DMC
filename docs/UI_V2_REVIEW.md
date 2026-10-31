# Pemeriksaan UI AI-DMC v2

Tanggal: 31 Oktober 2026. Acuan tunggal: .agents/skills/ai-dmc-apple-glass-ui/SKILL.md, identik dengan lampiran SKILL (2).md. Seluruh skill telah dibaca sebelum perubahan.

Repo sudah berisi tujuh commit implementasi v2 sebelum pemeriksaan ini. Perubahan lokal pada shell dan Unggah dipertahankan, termasuk penanganan Esc dropdown dan pemisah tanggal. Pemeriksaan ini melengkapi hasilnya tanpa menulis ulang riwayat tersebut.

## Checklist Bagian 11

| No. | Pemeriksaan | Hasil |
|---|---|---|
| 1 | Token Bagian 2, tanpa hex baru di komponen | Lulus. Seluruh 35 token cocok dengan skill; tidak ada hex di luar root token atau komponen TSX. Backdrop modal diturunkan dari token netral. |
| 2 | Font benar-benar Inter | Lulus. Chrome CDP Rendered Fonts melaporkan Inter-Bold untuk h1 dan Inter untuk subjudul, keduanya custom font. Fallback tidak dipakai pada elemen yang diperiksa. Inter dari next/font/google terpasang pada html; cv11, ss01, ss03 dan antialiasing aktif. |
| 3 | Skala judul 44px/700, tracking -0.03em | Lulus. Desktop 44px, tracking -1.32px; HP 34px, tracking -1.02px. Subjudul 17px; judul bagian 22px/600. |
| 4 | Segmented navbar dan kategori | Lulus. Aktif memakai permukaan putih dan shadow-raised. Pada HP kategori membungkus menjadi dua baris supaya seluruh opsi terlihat tanpa scroll horizontal. Link navbar mempertahankan aria-current; tombol kategori mempertahankan aria-pressed. |
| 5 | Glass hanya pada elemen yang diizinkan | Lulus. Navbar, tab bar HP, toolbar sticky, antrean, toast, modal. Kartu konten tetap solid. Pratinjau arsip tidak membuka modal bertumpuk. |
| 6 | Kartu memakai shadow-card, bukan border | Lulus. Kartu dan dropzone solid tanpa border luar; thumbnail memakai shadow-raised. Garis inset tetap ada di dalam list/tabel. |
| 7 | Semua teks minimal 4,5:1 | Pengecualian disetujui pengguna. Token v2 dipertahankan persis; ink-3 dan ink-4 tidak memenuhi batas. Lihat angka di bawah. |
| 8 | 375px dan 1280px tanpa overflow/potongan layout | Lulus pada tiga laman. Lebar dokumen sama dengan viewport. Kategori HP seluruhnya terlihat; nama berkas panjang memakai ellipsis sesuai list ringkas. Scroll vertikal normal tetap ada. |
| 9 | Keyboard dan fokus | Lulus. Avatar: Enter membuka, Esc menutup dan mengembalikan fokus. Koreksi: 25 Tab dan 25 Shift+Tab tetap di modal; Esc menutup dan mengembalikan fokus. Ring fokus terlihat. Select tetap kontrol native yang distyling, dengan chevron Lucide. |
| 10 | Larangan Bagian 9 | Lulus untuk tampilan yang diperiksa: tanpa gradien/glow/maskot/emoji/banner demo, dashed hanya saat drag, nama arsip netral, select tanpa panah native, empty state verifikasi langsung di latar. Tidak ada animasi baru di luar daftar skill. |
| 11 | Screenshot desktop dan HP pada PR | Screenshot tersedia lokal dan ditautkan di bawah. Belum dilampirkan ke PR karena pekerjaan ini tidak membuat PR atau perubahan remote. |

## Kontras yang dipertahankan

Pengguna memilih: **Pertahankan token v2; laporkan pengecualian kontras**.

| Token teks | Pada putih | Pada bg abu |
|---|---:|---:|
| ink | 16,83:1 | 15,46:1 |
| ink-2 | 7,41:1 | 6,81:1 |
| ink-3 | 3,62:1 | 3,33:1 |
| ink-4 | 2,57:1 | 2,36:1 |
| accent | 4,88:1 | 4,48:1 |

Jadi checklist kontras tidak dinyatakan lulus penuh. Nilai di atas dihitung untuk pasangan permukaan solid; glass bergantung pada konten di belakangnya.

## Screenshot final

| Laman | Desktop 1280px | HP 375px |
|---|---|---|
| Unggah | [Desktop](screenshots/v2/unggah-1280.png) | [HP](screenshots/v2/unggah-375.png) |
| Kotak Verifikasi kosong | [Desktop](screenshots/v2/verifikasi-1280.png) | [HP](screenshots/v2/verifikasi-375.png) |
| Arsip Saya | [Desktop](screenshots/v2/arsip-1280.png) | [HP](screenshots/v2/arsip-375.png) |
| Verifikasi terisi, fixture visual | [Desktop](screenshots/v2/verifikasi-terisi-1280.png) | [HP](screenshots/v2/verifikasi-terisi-375.png) |

Screenshot utama diambil dari akun QA dengan backend mock lokal. Untuk memeriksa kartu dan form koreksi ketika antrean server kosong, browser mengintersep respons baca dan merender satu dokumen sintetis high.png sebagai pending. Ini hanya fixture pengujian tampilan; tidak ada unggahan atau perubahan status dokumen backend. Screenshot HP utama memakai viewport 375x900 agar tab bar fixed tidak muncul di tengah gambar full-page.

## Batas perubahan dan hasil teknis

- Backend dan frontend/lib/api.ts tidak berubah. Perbandingan AST terhadap baseline e622e6f menemukan 66 pemanggilan API, state, effect, timer, dan routing tetap identik pada tujuh berkas yang diperiksa.
- Prefix [MOCK] berasal dari judul hasil mock backend. Nama pada Arsip Saya di-strip hanya pada layer render JSX; judul asli dan respons backend tidak diubah.
- Production build dan pemeriksaan tipe lulus. Browser tidak melaporkan pageerror pada skenario ini. Dropzone diuji idle/drag; icon box 56px, baris tabel 56px dan grouped list 64px terukur.
- Pengujian backend tidak diulang karena tidak ada perubahan backend. Pengujian ini tidak mengklaim validasi PostgreSQL atau pipeline asli.
- Bukti mesin: [browser](screenshots/v2/checks.json), [token/kontras](screenshots/v2/static-checks.json), [batas perilaku](screenshots/v2/behavior-checks.json). Script browser: frontend/scripts/ui-v2-check.mjs; password QA dibaca dari environment.

## Commit pelengkapan berurutan

1. 056663c — Inter pada html dan bobot eksplisit.
2. 6a66b9f — warna lapisan modal mengikuti token netral.
3. 250e125 — skala dan bobot teks komponen.
4. 659775a — Demo pill, dropdown akun dan fokus.
5. 7677d80 — dropzone dan grouped list.
6. d3f18e9 — nilai kosong dan select custom.
7. c6ba4c4 — empty state verifikasi.

Commit pemeriksaan akhir menyimpan penyesuaian responsif yang ditemukan lewat screenshot, ukuran baris, bukti pengujian, dan laporan ini.
