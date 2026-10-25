# Navigasi

Semua hal di Arch terjadi lewat keyboard — _SEMUA!_ Saat sistem pertama kali dimulai, kamu benar-benar tidak bisa melakukan apa pun hanya dengan mouse. Tapi kamu bisa menekan `Super + Space` untuk menampilkan Menu Arch dan dari sini kamu bisa melakukan hampir semua hal.

Tapi menu Arch bahkan tidak dimaksudkan menjadi cara utama untuk mengoperasikan sistem ini sepanjang waktu. Kita bisa lebih cepat dari itu! Semua aplikasi yang paling penting terikat langsung ke hotkey masing-masing. Kamu memulai terminal dengan `Super + Return` dan browser dengan `Super + Shift + Return`. Coba lakukan satu demi satu, dan kamu akan melihat keajaiban tiling Hyprland beraksi:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Lalu kamu bisa menekan `Super + J` untuk menumpuknya satu di atas yang lain, bukan berdampingan:

 ![navigation-stacked](images/navigation-stacked.webp)

Tekan `Super + J` lagi untuk mengembalikannya ke posisi berdampingan. Lalu coba `Super + Shift + Arrow Right` saat berada di browser untuk menukar jendelanya.

Sekarang coba `Super + Ctrl + T` untuk memulai monitor Activity. Sekarang tekan `Super + Shift + F` untuk membuka pengelola file. Kamu akan memiliki susunan empat arah yang rapi:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Kamu berpindah di antara jendela yang ingin kamu aktifkan dengan `Super + Arrow`. Ini akan mengalihkan fokus dan memindahkan kursor ke tengah aplikasi yang baru.

Jika kamu menekan `Super + Shift + 2`, kamu akan memindahkan aplikasi yang sedang terfokus ke workspace kedua. `Super + Shift + 1` memindahkannya kembali. (Dan `Super + Shift + Alt + 2` akan memindahkan aplikasi yang sedang terfokus ke workspace kedua tanpa ikut berpindah ke sana).

Jika kamu menahan `Super` dan menggunakan mouse untuk mengklik sebuah jendela, kamu bisa mengatur ulang di mana jendela itu berada. Jika kamu menahan `Super` dan menggunakan tombol kanan mouse, kamu bisa mengubah ukuran jendela dengan bebas.

Kamu menutup jendela dengan `Super + W` atau `Super + Q` (dan menutup semua jendela dengan `Ctrl + Alt + Delete`).

Kamu juga bisa masuk ke layar penuh dengan `Super + F` atau bahkan hanya selebar layar penuh (dengan tetap mempertahankan bar atas) dengan `Super + Alt + F` atau layar penuh di dalam sebuah jendela dengan `Super + Ctrl + F` (cocok untuk YouTube!).

### Tata letak dwindle vs scrolling

Tata letak default Arch disebut dwindle. Tata letak ini menjaga semua jendela yang kamu buka di satu workspace tetap terlihat setiap saat, meski harus menyusutkannya.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Tapi kamu juga bisa memilih untuk mengubah sebuah workspace menjadi tata letak scrolling, di mana jendela-jendela berjajar berdampingan, melampaui tepi layar yang terlihat. Kamu mengubah satu workspace menjadi tata letak ini lewat `Super + L`.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Pilihannya berlaku per workspace, dan tetap bertahan. Jadi kamu bisa menjaga workspace 1 tetap di dwindle untuk browsing dan workspace 2 di scrolling untuk kode, dan keduanya akan kembali seperti itu setelah restart.

Jika kamu ingin menggunakan tata letak scrolling sebagai default, kamu bisa mengaturnya di `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Mengelompokkan jendela

Jendela bisa dikelompokkan menggunakan `Super + G`. Setelah kamu masuk ke sebuah grup, setiap jendela yang kamu mulai saat grup itu aktif akan menjadi bagian dari grup tersebut. Kamu bisa berpindah di antara jendela-jendela yang dikelompokkan ini menggunakan `Super + Ctrl + Arrow Left/Right` atau `Super + Alt + 1/2/3/4` untuk langsung menuju jendela dalam grup sesuai urutan.

Kamu bisa memindahkan jendela keluar dari pengelompokan dengan `Super + Alt + G` atau membubarkan seluruh grup dengan menekan `Super + G` lagi. Terakhir, kamu bisa memindahkan jendela di luar grup masuk ke dalamnya dengan `Super + Alt + Arrows`.

### Workspace scratchpad

Terakhir, ada workspace scratchpad khusus yang turun di atas workspace tempatmu berada saat ini, mirip seperti konsol Quake. Alihkan dengan `Super + Grave` atau `Super + S`, dan tempatkan jendela di sana menggunakan `Super + Shift + Grave` atau `Super + Alt + S`.

Ini sangat cocok untuk terminal yang menjalankan agent, atau untuk kontrol yang ingin kamu gunakan dengan cepat tanpa meninggalkan workspace saat ini. Untuk memindahkan jendela dari scratchpad, kirim langsung ke workspace lain dengan sesuatu seperti `Super + Shift + 1`.

Selagi scratchpad hanya menampung satu jendela, ia turun sebagai panel terpusat, bukan membentang memenuhi layar. Letakkan aplikasi kedua di sana dan ia kembali selebar penuh, sehingga keduanya punya ruang untuk duduk berdampingan.

### Perlu waktu untuk terbiasa!

Perlu sedikit waktu untuk terbiasa menavigasi desktopmu seperti ini, tapi begitu kamu terbiasa, akan sulit untuk kembali ke pengalaman desktop tradisional yang mengandalkan mouse!
