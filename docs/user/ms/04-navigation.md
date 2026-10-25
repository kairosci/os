# Navigasi

Segala-galanya dalam Arch berlaku melalui papan kekunci — _SEGALA-GALANYA!_ Apabila sistem mula-mula dimulakan, anda memang tidak boleh buat apa-apa dengan tetikus sahaja. Tetapi anda boleh tekan `Super + Space` untuk memaparkan Arch Menu dan dari sini anda boleh buat hampir segala-galanya.

Tetapi Arch Menu pun tidak bertujuan untuk menjadi cara utama mengendalikan sistem pada kebanyakan masa. Kita boleh jadi lebih pantas daripada itu! Semua aplikasi yang paling penting terikat terus kepada kekunci pintas individu. Anda mulakan terminal dengan `Super + Return` dan pelayar dengan `Super + Shift + Return`. Cuba lakukan satu demi satu, dan anda akan nampak keajaiban tiling Hyprland beraksi:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Anda kemudian boleh tekan `Super + J` untuk menyusunnya bertindih di atas satu sama lain dan bukannya bersebelahan:

 ![navigation-stacked](images/navigation-stacked.webp)

Tekan `Super + J` sekali lagi untuk mengembalikannya ke kedudukan bersebelahan. Kemudian cuba `Super + Shift + Arrow Right` semasa berada di pelayar untuk menukar tetingkap-tetingkap tersebut.

Sekarang cuba `Super + Ctrl + T` untuk memulakan Activity monitor. Ia akan muncul sebagai tetingkap terapung. Anda boleh menjadikannya tetingkap tiling menggunakan `Super + T` (dan tekan itu sekali lagi untuk menjadikannya terapung semula). Sekarang tekan `Super + Shift + F` untuk membuka pengurus fail. Anda akan mempunyai susunan empat bahagian yang kemas:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Anda menavigasi antara tetingkap yang anda mahu aktif dengan `Super + Arrow`. Ini akan menukar fokus dan menggerakkan kursor ke tengah aplikasi baharu.

Jika anda tekan `Super + Shift + 2`, anda akan memindahkan aplikasi yang sedang difokuskan ke ruang kerja kedua. `Super + Shift + 1` memindahkannya kembali. (Dan `Super + Shift + Alt + 2` akan memindahkan aplikasi yang sedang difokuskan ke ruang kerja kedua tanpa beralih kepadanya).

Jika anda tahan `Super` dan guna tetikus untuk mengklik pada tetingkap, anda boleh menyusun semula kedudukannya. Jika anda tahan `Super` dan guna butang kanan pada tetikus, anda boleh mengubah saiz tetingkap dengan bebas.

Anda menutup tetingkap pada `Super + W` atau `Super + Q` (dan menutup semua tetingkap pada `Ctrl + Alt + Delete`).

Anda juga boleh pergi ke skrin penuh dengan `Super + F` atau malah hanya lebar penuh (mengekalkan bar atas) dengan `Super + Alt + F` atau skrin penuh di dalam tetingkap dengan `Super + Ctrl + F` (bagus untuk YouTube!).

### Susun atur dwindle lwn scrolling

Susun atur lalai Arch dipanggil dwindle. Ia memastikan semua tetingkap yang anda buka pada satu ruang kerja kelihatan pada setiap masa, walaupun terpaksa mengecilkannya.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Tetapi anda juga boleh pilih untuk menukar ruang kerja kepada susun atur scrolling di mana tetingkap berbaris bersebelahan, melampaui tepi paparan yang kelihatan. Anda menukar satu ruang kerja kepada susun atur ini melalui `Super + L`.

Menekan `Super + L` sekali lagi menjadikan ruang kerja terapung, di mana tetingkap bertindih dengan bebas dan anda meletakkannya sendiri, dan tekanan ketiga mengembalikannya kepada dwindle. `Super + Alt + L` melaluinya ke arah sebaliknya. Tetingkap yang memang terapung — tetingkap yang anda keluarkan dengan `Super + T`, atau aplikasi yang sentiasa dibuka dalam keadaan terapung — terus terapung apabila ruang kerja kembali kepada tiling. Bar atas menandakan ruang kerja yang anda berada dengan susun aturnya: segi empat untuk dwindle, bulatan untuk scrolling, dan segi tiga untuk floating. Mengklik tanda itu juga menukar susun atur secara bergilir.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Pilihan adalah mengikut ruang kerja, dan pilihan itu kekal. Jadi anda boleh kekalkan ruang kerja 1 pada dwindle untuk melayari dan ruang kerja 2 pada scrolling untuk kod, dan kedua-duanya akan kembali seperti itu selepas dimulakan semula.

Jika anda ingin menggunakan susun atur scrolling sebagai lalai, anda boleh menetapkannya dalam `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Mengumpulkan tetingkap

Tetingkap boleh dikumpulkan menggunakan `Super + G`. Sebaik sahaja anda berada dalam kumpulan, setiap tetingkap yang anda mulakan semasa itu aktif akan tergolong dalam kumpulan. Anda boleh bergerak antara tetingkap terkumpul ini menggunakan `Super + Ctrl + Arrow Left/Right` atau `Super + Alt + 1/2/3/4` untuk pergi terus ke tetingkap terkumpul mengikut turutan.

Anda boleh memindahkan tetingkap keluar daripada kumpulan dengan `Super + Alt + G` atau membubarkan seluruh kumpulan dengan menekan `Super + G` sekali lagi. Akhir sekali, anda boleh memindahkan tetingkap di luar kumpulan ke dalamnya dengan `Super + Alt + Arrows`.

### Ruang kerja scratchpad

Akhir sekali, terdapat ruang kerja scratchpad khas yang jatuh ke atas mana-mana ruang kerja yang anda sedang berada, seperti konsol Quake. Togolnya dengan `Super + Grave` atau `Super + S`, dan letakkan tetingkap di situ menggunakan `Super + Shift + Grave` atau `Super + Alt + S`.

Ia berfungsi dengan sangat baik untuk terminal yang menjalankan agent, atau untuk kawalan yang anda mahu berinteraksi dengan cepat tanpa meninggalkan ruang kerja semasa. Untuk mengalihkan tetingkap keluar dari scratchpad, hantarkannya terus ke ruang kerja lain dengan sesuatu seperti `Super + Shift + 1`.

Semasa scratchpad memegang satu tetingkap, ia jatuh sebagai panel tengah dan bukannya merentangi skrin. Letakkan aplikasi kedua padanya dan ia kembali ke lebar penuh, jadi kedua-duanya mempunyai ruang untuk duduk bersebelahan.

### Ia mengambil masa untuk membiasakan diri!

Ia mengambil sedikit masa untuk membiasakan diri menavigasi desktop anda seperti ini, tetapi sebaik sahaja anda membiasakannya, susah untuk kembali kepada pengalaman desktop tradisional yang dipandu tetikus!
