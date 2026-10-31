---
name: "ai-dmc-apple-glass-ui"
description: "Pakai skill ini setiap kali membuat atau mengubah UI frontend AI-DMC (Next.js). Arah desain Apple light + glass: latar abu flat, satu warna aksen, glass hanya untuk elemen kecil yang mengambang."
---

# Panduan Desain UI AI-DMC: Apple Light + Glass (v2)

Skill ini jadi acuan tunggal tampilan aplikasi AI-DMC. Diturunkan dari gaya "Apple light + glass capsules" yang sudah disetujui di proyek tim sebelumnya, lalu disesuaikan untuk aplikasi web dan identitas CoE AIIS.

Kalau ragu, pilih yang **lebih sepi**. Aplikasi ini dipakai dosen untuk kerja, bukan untuk dipamerkan.

**Acuan rasa Apple yang benar:** app Apple untuk kerja (Files, Settings, iCloud Drive web, Mail), bukan laman marketing apple.com. Yang diambil adalah bahasa desainnya: tipografi besar dengan tracking rapat, kedalaman lewat shadow lembut, kapsul segmented, list berkelompok, dan banyak ruang. Yang tidak diambil: hero produk raksasa dan teks promosi.

---

## 1. Prinsip Utama

1. **Tenang dan bersih.** Latar abu Apple flat, banyak ruang kosong, tanpa dekorasi.
2. **Hierarki tegas.** Tiap laman punya satu judul besar yang jelas jadi titik awal mata. Beda ukuran judul dan body harus terasa, bukan tipis-tipis.
3. **Kedalaman, bukan garis.** Elemen utama dipisahkan dari latar dengan shadow lembut, bukan border tebal. Border hanya untuk elemen sekunder dan pemisah di dalam kartu.
4. **Satu warna aksen, dipakai hemat.** Biru AIIS hanya untuk tombol utama, link saat hover, fokus, dan status aktif. Teks biasa (termasuk nama dokumen di tabel) tetap `--ink`.
5. **Glass punya fungsi.** Dipakai untuk elemen yang mengambang di atas konten (navbar, modal, panel unggah, toast). Kartu konten utama tetap putih solid.
6. **Satu laman, satu tugas utama.** Tombol utama cuma satu per layar.
7. **Dosen tidak mengisi formulir dari nol.** UI menampilkan hasil AI yang sudah terisi, tugas dosen hanya Setujui atau Koreksi.

---

## 2. Design Tokens

Tempel di `frontend/app/globals.css`:

```css
:root {
  /* Latar dan permukaan */
  --bg: #F5F5F7;              /* latar halaman, flat */
  --surface: #FFFFFF;         /* kartu konten */
  --surface-muted: #FAFAFC;   /* hover baris, area sekunder */
  --fill: #EDEDF0;            /* latar kapsul segmented, kotak ikon */
  --border: #E5E5EA;          /* garis pemisah tipis */

  /* Teks */
  --ink: #1D1D1F;             /* teks utama */
  --ink-2: #55555A;           /* teks sekunder */
  --ink-3: #86868B;           /* label, keterangan */
  --ink-4: #A1A1A6;           /* placeholder, nilai kosong, teks nonaktif */

  /* Aksen tunggal: biru AIIS */
  --accent: #0B7AA0;          /* tombol utama, fokus, status aktif (kontras 4,8:1 di putih) */
  --accent-hover: #096A8B;
  --accent-soft: #E6F4FA;     /* latar terpilih, highlight lembut */
  --accent-brand: #2AABD2;    /* biru AIIS asli, khusus ikon / ilustrasi, BUKAN teks */

  /* Status (hanya untuk pill status kecil) */
  --st-proses-bg: #F2F2F7;    --st-proses-fg: #55555A;
  --st-verif-bg: #FFF4E5;     --st-verif-fg: #9A5B00;
  --st-ok-bg: #E8F6EE;        --st-ok-fg: #1E7A46;
  --st-tolak-bg: #FDECEC;     --st-tolak-fg: #B3141B;

  /* Merah Telkom: logo dan aksi destruktif saja */
  --telkom-red: #E1252B;

  /* Glass */
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(255, 255, 255, 0.9);
  --glass-line: rgba(185, 205, 235, 0.6);
  --glass-blur: 20px;

  /* Bentuk */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-icon: 14px;        /* kotak ikon ala app icon */
  --radius-lg: 20px;
  --radius-pill: 999px;

  /* Bayangan: netral, lebar, lembut */
  --shadow-card: 0 1px 1px rgba(0,0,0,0.03), 0 8px 24px rgba(0,0,0,0.06);
  --shadow-raised: 0 1px 2px rgba(0,0,0,0.06), 0 2px 6px rgba(0,0,0,0.06);  /* item aktif di kapsul */
  --shadow-float: 0 12px 40px rgba(0,0,0,0.10);

  /* Gerak */
  --ease: cubic-bezier(0.25, 0.1, 0.25, 1);
}
```

**Kenapa biru, bukan merah Telkom, sebagai aksen?** Di aplikasi, merah dibaca sebagai "bahaya / hapus". Kalau semua tombol merah, tombol Tolak jadi tidak terbedakan. Jadi merah Telkom hanya muncul di logo dan aksi destruktif.

---

## 3. Tipografi

1. **Satu keluarga huruf: Inter.** Load lewat `next/font/google` dan pasang class-nya di `<html>`. Wajib dicek di DevTools (Computed > font-family) bahwa yang tampil benar-benar Inter, bukan fallback. Font fallback adalah penyebab utama teks terlihat renggang dan "tidak Apple".
2. Aktifkan fitur Inter dan smoothing:
   ```css
   body {
     font-feature-settings: "cv11", "ss01", "ss03";
     -webkit-font-smoothing: antialiased;
     -moz-osx-font-smoothing: grayscale;
     color: var(--ink);
     background: var(--bg);
   }
   ```
3. Skala:

| Peran | Ukuran / Tebal | Tracking / line-height | Contoh |
|---|---|---|---|
| Judul laman | 44px / 700 (HP 34px) | -0.03em / 1.1 | "Kotak Verifikasi" |
| Subjudul laman | 17px / 400, `--ink-3` | normal / 1.45 | "Tambahkan dokumen untuk diproses." |
| Judul bagian | 22px / 600 | -0.015em / 1.25 | "Unggahan terakhir" |
| Judul kartu | 17px / 600 | -0.01em / 1.3 | Nama dokumen di kartu |
| Body | 15px / 400 | normal / 1.5 | Isi umum, sel tabel |
| Label / meta | 13px / 500, `--ink-3` | normal / 1.4 | "31 Okt 2026" |
| Pill / badge | 12px / 600 | 0.01em | Status |

4. Jarak judul laman ke subjudul 8px. Subjudul ke konten pertama 32px.
5. Teks tidak pernah di bawah 12px.
6. Judul laman berupa kata benda singkat, bukan kalimat promosi.
7. Angka (skor, jumlah) pakai `font-variant-numeric: tabular-nums`.

---

## 4. Glass: Kapan Boleh, Kapan Tidak

### Boleh
1. **Navbar** sticky di atas.
2. **Modal / sheet** (misalnya form koreksi).
3. **Panel antrean unggah** yang mengambang di pojok bawah.
4. **Toast** notifikasi.
5. **Toolbar filter** yang menempel saat scroll.

### Tidak boleh
1. Kartu dokumen, tabel, atau kartu verifikasi (pakai `--surface` putih solid).
2. Latar seluruh halaman.
3. Glass di atas glass.

Catatan: di atas latar abu flat, glass memang tidak terlihat sampai konten di-scroll ke bawahnya. Itu normal. Jangan tambah gradien latar hanya supaya glass "kelihatan".

### Resep CSS

```css
.glass {
  background: var(--glass-bg);
  backdrop-filter: saturate(180%) blur(var(--glass-blur));
  -webkit-backdrop-filter: saturate(180%) blur(var(--glass-blur));
  border: 1px solid var(--glass-line);
  box-shadow: inset 0 1px 0 var(--glass-border), var(--shadow-float);
}

@supports not (backdrop-filter: blur(1px)) {
  .glass { background: rgba(255, 255, 255, 0.96); }
}
@media (prefers-reduced-transparency: reduce) {
  .glass { background: rgba(255, 255, 255, 0.98); backdrop-filter: none; }
}
```

Bayangan selalu netral (hitam transparan). **Tidak ada bayangan atau glow berwarna.**

---

## 5. Komponen

### 5.1 Navbar
- Glass, tinggi 56px, sticky. Navbar yang menempel di atas cukup pakai garis bawah `--glass-line` tanpa shadow float sampai halaman di-scroll.
- Kiri: logo Telkom University + AIIS, garis pemisah vertikal tipis, lalu "AI-DMC" 15px/600.
- Tengah: **kapsul segmented** berisi Unggah, Verifikasi (dengan angka badge), Arsip. Lihat 5.12.
- Kanan: avatar inisial 32px saja. Nama lengkap dan tombol keluar masuk ke dropdown avatar. Jangan tampilkan nama yang terpotong ("Dosen Satu (Dum...").
- Label mode demo (kalau ada): pill kecil "Demo" (12px/600, `--fill`, `--ink-2`) di sebelah teks "AI-DMC". Bukan banner di atas konten.
- Di HP: menu pindah ke tab bar bawah (glass juga), 3 ikon + label.

### 5.2 Tombol

| Jenis | Tampilan | Contoh |
|---|---|---|
| Utama | Latar `--accent`, teks putih 15px/600, radius pill, tinggi 40px, padding 0 20px | Setujui, Unggah |
| Sekunder | Latar `--accent-soft`, teks `--accent` | Koreksi |
| Netral | Latar `--fill`, teks `--ink` | Pilih berkas lain |
| Teks | Tanpa latar, teks `--accent` | Lihat detail |
| Destruktif | Teks `--telkom-red`, tanpa latar; jadi solid merah hanya di dialog konfirmasi | Tolak |

Hover: gelap sedikit. Tekan: `transform: scale(0.98)`. Fokus keyboard: ring 3px `--accent-soft` + outline 2px `--accent`. Jangan pernah hilangkan outline fokus.

### 5.3 Area Unggah (Dropzone)
- Kartu putih solid, radius `--radius-lg`, `--shadow-card`, **tanpa garis putus-putus** dalam keadaan diam. Padding vertikal 56px.
- Ikon: Lucide `FileUp` 24px warna `--accent-brand`, di dalam kotak 56px latar `--fill` radius `--radius-icon` (gaya app icon).
- Judul 20px/600 "Seret berkas ke sini atau pilih berkas", keterangan 13px `--ink-3` "PDF, DOCX, JPG, PNG · Maksimal 20 MB per berkas", jarak 24px ke tombol utama "Pilih berkas".
- Saat berkas diseret di atasnya: muncul outline putus-putus 2px `--accent` dengan offset -8px, latar `--accent-soft`. Dashed hanya muncul di keadaan ini.
- Di HP: tombol tambahan "Pindai dengan kamera" (netral).

### 5.4 Panel Antrean Unggah
- Glass, mengambang di kanan bawah (HP: sheet dari bawah), radius `--radius-lg`.
- Tiap berkas satu baris: nama berkas, status teks ("Membaca teks", "Mengklasifikasi", "Selesai"), progress bar tipis 3px warna `--accent`.
- Duplikat: teks "Sudah pernah diunggah" warna `--ink-3`, bukan merah.

### 5.5 Pill Status
Radius pill, 12px/600, padding 4px 10px, pakai pasangan warna `--st-*`:
- Diproses (abu), Menunggu verifikasi (oranye lembut), Terverifikasi (hijau lembut), Ditolak (merah lembut), Gagal (merah lembut + ikon).

### 5.6 Indikator Keyakinan AI
- Teks "Keyakinan AI 91%", di sebelahnya bar tipis 4px.
- Bar `--accent` kalau ≥ 85%, `--st-verif-fg` kalau di bawah.
- Di bawah 85%: kalimat kecil "AI kurang yakin, mohon dicek."
- Jangan pakai gauge bulat atau speedometer.

### 5.7 Kartu Verifikasi (komponen terpenting)
Kartu putih, `--shadow-card`, radius `--radius-lg`. Dua kolom di desktop, bertumpuk di HP:
1. **Kiri:** pratinjau dokumen (thumbnail halaman pertama) dengan radius `--radius-md` dan shadow `--shadow-raised` supaya terasa seperti kertas. Klik untuk perbesar.
2. **Kanan:**
   - Nama berkas (17px/600) + pill status.
   - Indikator keyakinan.
   - Klasifikasi: Kategori › Subkategori › Jenis, satu baris breadcrumb.
   - Metadata dalam daftar label-nilai (label `--ink-3` 13px, nilai `--ink` 15px). Field kosong ditulis "Tidak ditemukan" warna `--ink-4`.
   - Tombol: **Setujui** (utama), Koreksi (sekunder), Tolak (destruktif teks). Setujui paling kanan.

### 5.8 Form Koreksi
- Sheet/modal glass.
- Semua field sudah terisi hasil AI. Field yang diubah dosen diberi titik kecil `--accent` di sampingnya.
- Kategori, subkategori, jenis pakai dropdown dari endpoint `/taxonomy`.
- Input: latar putih, border `--border`, radius `--radius-sm`, tinggi 40px, fokus border `--accent`.

### 5.9 Daftar Arsip
- Toolbar filter (glass, sticky): kapsul segmented kategori (Semua, PND, PNL, PKM, PUB, PNJ, ADM, LAINNYA) memakai komponen 5.12, lalu dropdown status dan tahun (5.13).
- Jumlah hasil ("14 dokumen") 13px `--ink-3` di atas tabel.
- Isi: tabel di dalam kartu putih `--shadow-card`, tanpa border luar. Kolom: Nama dokumen, Jenis, Tanggal terbit, Status.
- Nama dokumen 15px/500 warna `--ink`, **bukan biru**. Seluruh baris bisa diklik; saat hover latar `--surface-muted` dan nama jadi `--accent`.
- Kode kategori (PND dll) di bawah nama: 12px `--ink-3`.
- Nilai kosong: "Tidak ditemukan" warna `--ink-4`, supaya tidak bersaing dengan data yang ada.
- Header tabel 12px/600 `--ink-3`, tanpa latar.
- Baris tinggi 56px, garis pemisah `--border` yang dimulai dari padding kiri (inset), bukan full-width.
- Label teknis seperti "[MOCK]" tidak boleh muncul di nama dokumen. Kalau perlu, tampilkan pill kecil "Contoh" di samping nama.
- Di HP: tabel berubah jadi grouped list (5.14).

### 5.10 Empty State
- **Tanpa kartu pembungkus.** Langsung di atas `--bg`, posisi sedikit di atas tengah area konten (padding atas sekitar 96px).
- Ikon Lucide 24px di kotak 56px `--fill` radius `--radius-icon`.
- Judul 20px/600 (contoh: "Semua sudah dicek"), satu kalimat penjelas 15px `--ink-3` ("Belum ada dokumen yang menunggu konfirmasi."), satu tombol.
- Tanpa ilustrasi kartun.

### 5.11 Toast
- Glass, muncul di atas tengah, hilang 3 detik.
- Contoh: "Dokumen disetujui dan masuk arsip." Sertakan tombol "Urungkan" untuk aksi Setujui/Tolak.

### 5.12 Kapsul Segmented
Dipakai untuk menu navbar dan filter kategori. Ini ciri visual Apple yang paling kelihatan, jadi wajib konsisten.

```css
.segmented {
  display: inline-flex; gap: 2px; padding: 3px;
  background: var(--fill); border-radius: var(--radius-pill);
}
.segmented button {
  height: 32px; padding: 0 14px; border-radius: var(--radius-pill);
  font-size: 14px; font-weight: 500; color: var(--ink-2);
  transition: background 200ms var(--ease), color 200ms var(--ease);
}
.segmented button[aria-selected="true"] {
  background: var(--surface); color: var(--ink);
  box-shadow: var(--shadow-raised);
}
```

- Di navbar, item aktif boleh memakai warna teks `--accent` sebagai ganti `--ink`. Pilih satu dan konsisten.
- Ikon di menu navbar 16px, jarak 6px ke label.

### 5.13 Dropdown / Select
- Jangan pakai panah native browser. `appearance: none`, lalu chevron Lucide `ChevronDown` 16px `--ink-3` di kanan.
- Tinggi 36px, latar `--surface`, border `--border`, radius `--radius-sm`, teks 14px.
- Label di atas: 12px/600 `--ink-3`, jarak 6px.

### 5.14 Grouped List
Dipakai untuk "Unggahan terakhir" dan tampilan HP arsip. Gaya list Settings / Files.

- Kartu putih `--shadow-card`, radius `--radius-lg`, tanpa border luar.
- Tiap baris tinggi 64px, padding 0 20px:
  1. Kiri: kotak ikon 36px `--fill` radius 10px berisi ikon tipe berkas (Lucide `FileText` untuk PDF/DOCX, `Image` untuk JPG/PNG) 18px `--ink-2`.
  2. Tengah: nama berkas 15px/500 `--ink`, di bawahnya meta 13px `--ink-3` ("31 Okt 2026 · PDF").
  3. Kanan: pill status, lalu `ChevronRight` 16px `--ink-4`.
- Garis pemisah `--border` dimulai sejajar teks (setelah kotak ikon), tidak menyentuh tepi kiri.
- Hover: latar `--surface-muted`.

---

## 6. Layout Laman

| Laman | Isi utama |
|---|---|
| Login | Kartu putih di tengah lebar 380px, `--shadow-card`, logo di atas, 2 input, 1 tombol. Latar `--bg` polos. |
| Unggah | Judul laman + subjudul, dropzone, lalu "Unggahan terakhir" (grouped list, 5 item) dengan link "Lihat Arsip Saya" sejajar judul bagian. Panel antrean mengambang. |
| Kotak Verifikasi | Judul + jumlah ("4 dokumen menunggu konfirmasi"), daftar kartu verifikasi bertumpuk dengan jarak 16px. Kalau kosong, empty state 5.10. |
| Arsip Saya | Judul, toolbar filter, jumlah hasil, tabel. |

Grid:
1. Lebar konten maksimum 1080px, di tengah.
2. Padding samping 24px desktop, 16px HP.
3. Jarak antar elemen kelipatan 4px (8, 12, 16, 24, 32, 48, 64).
4. Jarak navbar ke judul laman 48px desktop, 32px HP.
5. Jarak antar bagian besar (dropzone ke "Unggahan terakhir") 48px.
6. Tidak ada scroll horizontal di HP.

---

## 7. Gerak (Motion)
1. Durasi 150 sampai 250ms, easing `var(--ease)`.
2. Yang boleh bergerak: hover dan tekan tombol, pergantian item kapsul segmented, munculnya modal/sheet (fade + naik 8px), toast, progress bar.
3. Hormati `prefers-reduced-motion`: matikan animasi non-esensial.
4. Tidak ada animasi berulang (pulse, shimmer berlebihan). Skeleton loading boleh, abu `--surface-muted` statis atau shimmer sangat halus.

---

## 8. Ikon
- Satu set saja: **Lucide** (`lucide-react`), stroke 1.75, ukuran 16, 18, atau 20px.
- Warna ikon ikut teks di sebelahnya, kecuali ikon di kotak app icon (boleh `--accent-brand`).
- Ikon bukan dekorasi, selalu ada label teksnya.

---

## 9. Larangan (biar tidak kelihatan "AI banget" atau "admin panel generik")

1. Gradien aurora, mesh gradient, blob, atau glow berwarna di latar.
2. Lebih dari satu warna aksen.
3. Glass di semua tempat, terutama kartu konten.
4. Deretan kartu identik dengan ikon di lingkaran warna-warni.
5. Emoji di UI.
6. Teks promosi ("Revolusi pengelolaan dokumen!"). Pakai bahasa kerja yang lugas.
7. Em-dash di copy.
8. Font lebih dari satu keluarga, atau font fallback yang lolos tanpa dicek.
9. Ilustrasi kartun atau maskot.
10. Shadow tebal atau shadow berwarna.
11. Banner info bergaris di atas judul laman (pakai pill di navbar).
12. Garis putus-putus di dropzone saat diam.
13. Semua teks link berwarna biru di tabel atau list.
14. Panah select native browser.
15. Empty state di dalam kartu besar yang sisanya kosong.
16. Judul laman yang hampir sama besar dengan judul bagian.

---

## 10. Copywriting UI
1. Bahasa Indonesia baku tapi santai, kalimat pendek.
2. Tombol pakai kata kerja: Unggah, Setujui, Koreksi, Tolak, Simpan.
3. Istilah konsisten di semua laman: "Kotak Verifikasi", "Arsip Saya", "Keyakinan AI". Jangan ganti-ganti sinonim.
4. Pesan error menjelaskan apa yang harus dilakukan: "Format berkas tidak didukung. Gunakan PDF, DOCX, JPG, atau PNG."
5. Empty state ditulis positif kalau memang selesai: "Semua sudah dicek", bukan "Belum ada dokumen".

---

## 11. Checklist Sebelum PR UI
1. Hanya pakai token dari Bagian 2, tidak ada warna hex baru di komponen.
2. Font yang tampil benar-benar Inter (cek Computed di DevTools).
3. Judul laman 44px/700 dengan tracking -0.03em, terasa jauh lebih besar dari judul bagian.
4. Menu navbar dan filter kategori memakai kapsul segmented 5.12.
5. Glass hanya di elemen yang tercantum di Bagian 4.
6. Kartu utama memakai `--shadow-card`, bukan border.
7. Kontras teks minimal 4,5:1.
8. Dicek di lebar 375px (HP) dan 1280px (desktop), tidak ada yang terpotong atau scroll horizontal.
9. Bisa dipakai pakai keyboard saja (Tab, Enter, Esc), outline fokus terlihat.
10. Tidak melanggar satu pun larangan di Bagian 9.
11. Screenshot desktop + HP dilampirkan di PR.
