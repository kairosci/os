# Yangilanishlar

Arch va paketlaringiz Arch menyusidagi (`Super + Space`) _Yangilash > Arch_ orqali yangilab turiladi.

Arch ning oʻzi [Arch Package Repository](https://github.com/kairosci/arch) dan oddiy pacman paketlari sifatida oʻrnatilgan, shuning uchun yangilash [eng soʻnggi Arch relizi](https://github.com/kairosci/arch) ni oʻrnatadi, tizimingizni eng soʻnggisi bilan sinxron qilish uchun kutilayotgan har qanday migratsiyalarni ishga tushiradi va [Arch Arch Mirror](https://github.com/kairosci/arch) va [AUR](https://aur.archlinux.org/) dan (agar biror AUR paketlarini oʻrnatgan boʻlsangiz) barcha tizim paketlarini yangilaydi.

Yangi relizlar chiqarilganda, soatingizning oʻng tomonida doira strelka piktogrammasi paydo boʻladi. Uni bosing va yangilash jarayoni boshlanadi.

![update-available](images/update-available.webp)

### Toʻrtta kanal

Arch toʻrtta kanal boʻylab yangilanadi: stable, RC, edge va dev. Yangi oʻrnatishlar [rasmiy relizlar](https://github.com/kairosci/arch) ni, shuningdek eng soʻnggisidan bir oy orqada ishlaydigan [barqaror Arch Arch oynasi](https://github.com/kairosci/arch) ni kuzatuvchi stable kanalda boshlanadi, shunday qilib biz konfiguratsiya oʻzgarishlarini talab qiluvchi har qanday yangi mos kelmasliklarni ular odamlarga muammo tugʻdirishidan oldin tuta olamiz.

Lekin oʻsha mumkin boʻlgan muammolarni aniqlashga yordam bermoqchi boʻlsangiz, edge kanalda ishlashingiz mumkin. Bu Arch paketlaringizni eng soʻnggi dasturlash yigʻmalarini kuzatib turishga majbur qiladi va eng soʻnggi Arch paketlari mavjud boʻlishi bilanoq yangilash imkonini beradi. Buni faqat Linux bilan tajribangiz boʻlsa va muammolari bor tizimni qanday tiklashni bilsangiz qilishingiz kerak.

Har qanday yangi yirik relizdan oldin biz RC kanali yordamida yakuniy tekshiruv qilamiz. Agar yakuniy sayqallashga yordam berish bilan qiziqsangiz, Discord dagi #arch-release-candidates ga keling.

Nihoyat, dev kanali bor, u Arch ni toʻgʻridan-toʻgʻri `~/arch` dagi manba kodining git checkout iga, edge paketlari bilan birgalikda bogʻlaydi. Bu kanaldan faqat tajribali Linux foydalanuvchisi boʻlsangiz, toʻgʻridan-toʻgʻri Arch da ishlasangiz va buzilishga chidashga tayyor boʻlsangiz foydalanishingiz kerak.

Kanallar orasida Arch menyusidagi _Yangilash > Channel_ yordamida (yoki terminalda `arch-channel-set` bilan) almashishingiz mumkin.

### Proshivka yangilanishlari

Paketlaringiz eskiradigan yagona narsa emas. Koʻplab noutbuklar va periferik qurilmalar BIOS, SSD va dock proshivkasini Linux Vendor Firmware Service orqali yetkazadi va Arch menyusidagi _Yangilash > Firmware_ uskunangizda kutib turgan har qanday narsani olib kelib oʻrnatadi. U birinchi marta ishga tushirganingizda `fwupd` ni oʻrnatadi. Koʻp proshivka faqat qayta yuklash davomida yozilishi mumkin, shuning uchun bittasi soʻralishiga hayron boʻlmang.

### Toʻgʻridan-toʻgʻri pacman/yay yangilanishlari haqida ogohlantirish

Agar Arch bilan allaqachon tanish boʻlsangiz, shunchaki oʻzingiz `pacman -Syu` yoki `yay -Syu` ni ishga tushirish vasvasasiga tushishingiz mumkin, lekin agar shunday qilsangiz, Arch yangi paketlar bilan birga ishga tushiradigan snapshot, migratsiyalar va konfiguratsiya yangilanishlarini oʻtkazib yuborasiz. Shuning uchun Arch aslida toʻgʻridan-toʻgʻri tizim yangilashini toʻxtatadi va uning oʻrniga sizni `archctl update` ga yoʻnaltiradi. (Agar haqiqatan ham nima qilayotganingizni bilsangiz, himoya sizga uni bitta tranzaksiya uchun qanday chetlab oʻtishni aytadi.)

### Yomon yangilanishlarni qaytarish

Yangilanishni qilgandan keyin qachonlardir muammoga duch kelsangiz, tizimingizni yangilanishdan oldin olingan snapshotga qaytarishingiz mumkin. Shunchaki qayta ishga tushiring va yangilanishni boshlashingizdan oldingi yuklash menyusida snapshotni tanlang.

![bootloader](images/bootloader.webp)

Agar qandaydir tarzda konfiguratsiya fayllaringiz buzilgan boʻlsa, terminalda `arch reinstall` yordamida Arch qayta oʻrnatishini ham bajarishingiz mumkin. Bu barcha standart Arch paketlarini qayta oʻrnatadi, sizni stable ga qoʻyadi va juda yangi boʻlgan har qanday paketlarni pasaytiradi hamda barcha konfiguratsiya fayllarini tiklaydi. Eʼtibor bering, buni qilish orqali Arch standartlariga barcha foydalanuvchi konfiguratsiya oʻzgarishlaringiz ustiga yoziladi!
