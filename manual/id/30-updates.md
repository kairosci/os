# Pembaruan

Arch dan paketmu tetap mutakhir melalui _Perbarui > Arch_ di menu Arch (`Super + Space`).

Arch itu sendiri dipasang sebagai paket pacman biasa dari [Arch Package Repository](https://github.com/kairosci/arch), jadi pembaruan memasang [rilis Arch terbaru](https://github.com/kairosci/arch), menjalankan migrasi yang tertunda untuk menyinkronkan sistemmu dengan yang terbaru, dan memperbarui semua paket sistem dari [Arch Arch Mirror](https://github.com/kairosci/arch) dan [AUR](https://aur.archlinux.org/) (jika kamu telah memasang paket AUR apa pun).

Saat rilis baru dibuat, ikon panah lingkaran akan muncul di sebelah kanan jam-mu. Klik itu dan proses pembaruan akan dimulai.

![update-available](images/update-available.webp)

### Empat saluran

Arch diperbarui sepanjang empat saluran: stable, RC, edge, dan dev. Pemasangan baru dimulai pada saluran stable, yang melacak [rilis resmi](https://github.com/kairosci/arch), serta [mirror Arch Arch stable](https://github.com/kairosci/arch) yang berjalan satu bulan di belakang yang terbaru, jadi kami dapat menangkap ketidakcocokan baru apa pun yang memerlukan perubahan konfigurasi sebelum menyebabkan masalah bagi orang-orang.

Tetapi jika kamu ingin membantu menemukan potensi masalah tersebut, kamu dapat berjalan di saluran edge. Itu akan membuat paket Arch-mu melacak build pengembangan terbaru, dan memungkinkan kamu memperbarui ke paket Arch terbaru segera setelah tersedia. Kamu hanya boleh melakukan ini jika kamu berpengalaman dengan Linux, dan tahu cara memulihkan sistem yang bermasalah.

Sebelum rilis besar baru apa pun, kami akan melakukan validasi akhir menggunakan saluran RC. Jika kamu tertarik membantu pemolesan akhir, datanglah nongkrong di #arch-release-candidates di Discord.

Terakhir, ada saluran dev, yang menghubungkan Arch langsung ke checkout git dari kode sumber di `~/arch`, digabungkan dengan paket edge. Kamu hanya boleh menggunakan saluran ini jika kamu pengguna Linux berpengalaman, bekerja langsung pada Arch, dan bersedia mentolerir kerusakan.

Kamu dapat beralih antar saluran menggunakan _Perbarui > Channel_ dari menu Arch (atau `arch-channel-set` di terminal).

### Pembaruan firmware

Paketmu bukan satu-satunya hal yang menjadi basi. Banyak laptop dan periferal mengirimkan firmware BIOS, SSD, dan dock melalui Linux Vendor Firmware Service, dan _Perbarui > Firmware_ di menu Arch akan mengambil dan memasang apa pun yang menunggu perangkat kerasmu. Ini memasang `fwupd` pertama kali kamu menjalankannya. Banyak firmware hanya dapat ditulis selama reboot, jadi jangan terkejut jika diminta untuk itu.

### Peringatan tentang pembaruan pacman/yay langsung

Jika kamu sudah familier dengan Arch, kamu mungkin tergoda untuk hanya menjalankan `pacman -Syu` atau `yay -Syu` sendiri, tetapi jika kamu melakukan itu, kamu akan melewatkan snapshot, migrasi, dan pembaruan konfigurasi yang dijalankan Arch bersama paket baru. Itulah mengapa Arch akan benar-benar menghentikan peningkatan sistem langsung dan mengarahkan kamu ke `archctl update` sebagai gantinya. (Jika kamu benar-benar tahu apa yang kamu lakukan, penjaga akan memberitahumu cara melewatinya untuk satu transaksi.)

### Mengembalikan pembaruan yang buruk

Jika kamu pernah mengalami masalah setelah melakukan pembaruan, kamu dapat mengembalikan sistemmu ke snapshot yang diambil sebelum pembaruan. Cukup mulai ulang dan pilih snapshot di menu pemuatan boot dari sebelum kamu memulai pembaruan.

![bootloader](images/bootloader.webp)

Jika entah bagaimana berkas konfigurasimu telah rusak, kamu juga dapat melakukan pemasangan ulang Arch menggunakan `arch reinstall` di terminal. Ini akan memasang ulang semua paket Arch bawaan, menempatkan kamu di stable dan menurunkan paket apa pun yang terlalu baru, dan mengatur ulang semua berkas konfigurasi. Perhatikan bahwa semua perubahan konfigurasi pengguna terhadap bawaan Arch akan ditimpa dengan melakukan ini!
