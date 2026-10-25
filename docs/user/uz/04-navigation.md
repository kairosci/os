# Navigatsiya

Arch’da hamma narsa klaviatura orqali amalga oshiriladi — _HAMMA NARSA!_ Tizim birinchi marta ishga tushganida, sichqonchaning o‘zi bilan tom ma’noda hech narsa qila olmaysiz. Lekin Arch menyusini ochish uchun `Super + Space` ni bosishingiz mumkin va bu yerdan deyarli hamma narsani qila olasiz.

Lekin Arch menyusi ko‘p vaqt davomida tizimni boshqarishning asosiy usuli bo‘lishi hatto mo‘ljallanmagan ham. Biz undan tezroq ishlay olamiz! Barcha eng muhim ilovalar to‘g‘ridan-to‘g‘ri alohida tezkor tugmalarga bog‘langan. Siz terminalni `Super + Return` bilan, brauzerni esa `Super + Shift + Return` bilan ishga tushirasiz. Ularni ketma-ket bajarib ko‘ring, shunda Hyprland plitkalashining sehrini amalda ko‘rasiz:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Keyin ularni yonma-yon emas, bir-birining ustiga taxlash uchun `Super + J` ni bosishingiz mumkin:

 ![navigation-stacked](images/navigation-stacked.webp)

Ularni yonma-yon holatiga qaytarish uchun yana `Super + J` ni bosing. Keyin brauzerda turganingizda oynalarni almashtirish uchun `Super + Shift + Arrow Right` ni sinab ko‘ring.

Endi Faollik monitorini ishga tushirish uchun `Super + Ctrl + T` ni sinab ko‘ring. U suzuvchi oyna sifatida paydo bo‘ladi. Uni `Super + T` yordamida plitkalashingiz mumkin (va uni yana suzuvchi qilish uchun shu tugmani yana bosing). Endi fayllar menejerini ochish uchun `Super + Shift + F` ni bosing. Sizda to‘rt qismli tartibli joylashuv hosil bo‘ladi:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Siz faol bo‘lishini xohlangan oynaga `Super + Arrow` bilan o‘tasiz. Bu fokusni almashtiradi va kursorni yangi ilovaning markaziga olib boradi.

Agar `Super + Shift + 2` ni bossangiz, hozirda fokuslangan ilovani ikkinchi ish maydoniga ko‘chirasiz. `Super + Shift + 1` uni orqaga ko‘chiradi. (`Super + Shift + Alt + 2` esa hozirda fokuslangan ilovani ikkinchi ish maydoniga, unga o‘tmasdan ko‘chiradi).

Agar `Super` ni bosib turib, sichqoncha bilan oynani bossangiz, uning qayerda turishini qayta tartibga sola olasiz. Agar `Super` ni bosib turib, sichqonchaning o‘ng tugmasini ishlatsangiz, oynaning o‘lchamini erkin o‘zgartirishingiz mumkin.

Siz oynani `Super + W` yoki `Super + Q` bilan yopasiz (va barcha oynalarni `Ctrl + Alt + Delete` bilan yopasiz).

Shuningdek, `Super + F` bilan to‘liq ekranga yoki `Super + Alt + F` bilan faqat to‘liq kenglikka (yuqori panelni saqlab qolgan holda) yoki `Super + Ctrl + F` bilan oyna ichida to‘liq ekranga o‘tishingiz mumkin (YouTube uchun yaxshi!).

### Dwindle va scrolling tartibi

Arch’ning standart tartibi dwindle deb ataladi. U bitta ish maydonida ochgan barcha oynalaringizni har doim ko‘rinadigan holatda saqlaydi, hatto ularni kichraytirishiga to‘g‘ri kelsa ham.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Lekin siz ish maydonini oynalar yonma-yon, displeyning ko‘rinadigan chetidan tashqariga tizilib ketadigan scrolling tartibiga aylantirishni ham tanlashingiz mumkin. Bitta ish maydonini `Super + L` orqali ushbu tartibga aylantirasiz.

`Super + L` ni yana bosish ish maydonini suzuvchi holatga aylantiradi, bunda oynalar erkin bir-birining ustiga chiqadi va ularni o‘zingiz joylashtirasiz, uchinchi marta bosish esa uni dwindle’ga qaytaradi. `Super + Alt + L` ularni teskari tartibda aylanib o‘tadi. Baribir suzuvchi bo‘lgan oyna — `Super + T` bilan chiqarib olganingiz yoki har doim suzuvchi bo‘lib ochiladigan ilova — ish maydoni plitkalashga qaytganda ham suzuvchi bo‘lib qoladi. Yuqori panel siz turgan ish maydonini uning tartibi bilan belgilaydi: dwindle uchun kvadrat, scrolling uchun doira va suzuvchi uchun uchburchak. O‘sha belgini bosish ham tartibni aylantiradi.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Tanlov har bir ish maydoni uchun alohida bo‘ladi va u saqlanib qoladi. Shunday qilib, siz 1-ish maydonini ko‘rish uchun dwindle’da va 2-ish maydonini kod uchun scrolling’da saqlashingiz mumkin, va ular qayta ishga tushirilgandan keyin ham shu holatda qaytib keladi.

Agar scrolling tartibini standart sifatida ishlatishni xohlasangiz, buni `~/.config/hypr/looknfeel.lua` da sozlashingiz mumkin:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Oynalarni guruhlash

Oynalarni `Super + G` yordamida guruhlash mumkin. Guruh ichiga kirganingizdan so‘ng, u faol bo‘lgan paytda ishga tushirgan har bir oynangiz guruhga tegishli bo‘ladi. Ushbu guruhlangan oynalar orasida `Super + Ctrl + Arrow Left/Right` yordamida yoki tartib bo‘yicha guruhlangan oynaga to‘g‘ridan-to‘g‘ri o‘tish uchun `Super + Alt + 1/2/3/4` yordamida harakatlanishingiz mumkin.

Siz oynani `Super + Alt + G` bilan guruhlashdan chiqarishingiz yoki `Super + G` ni yana bosib, butun guruhni tarqatib yuborishingiz mumkin. Nihoyat, guruhdan tashqaridagi oynalarni `Super + Alt + Arrows` bilan uning ichiga ko‘chirishingiz mumkin.

### Scratchpad ish maydoni

Nihoyat, siz hozir turgan ish maydoni ustiga, xuddi Quake konsoliga o‘xshab, tushadigan maxsus scratchpad ish maydoni bor. Uni `Super + Grave` yoki `Super + S` bilan yoqing va u yerga oynani `Super + Shift + Grave` yoki `Super + Alt + S` yordamida joylashtiring.

U, ayniqsa, agent ishlayotgan terminal uchun yoki joriy ish maydonini tark etmasdan tezda o‘zaro ta’sir qilmoqchi bo‘lgan boshqaruv elementlari uchun yaxshi ishlaydi. Oynani scratchpad’dan ko‘chirish uchun uni `Super + Shift + 1` kabi biror narsa bilan to‘g‘ridan-to‘g‘ri boshqa ish maydoniga yuboring.

Scratchpad bitta oynani ushlab turgan paytda, u ekranni qamrab olish o‘rniga markazlashtirilgan panel sifatida tushadi. Unga ikkinchi ilovani qo‘ysangiz, u to‘liq kenglikka qaytadi, shunda ikkovining yonma-yon o‘tirishiga joy bo‘ladi.

### Bunga ko‘nikish biroz vaqt oladi!

Ish stolingizda bunday harakatlanishga ko‘nikish biroz vaqt oladi, lekin ko‘nikkaningizdan so‘ng, an’anaviy sichqoncha bilan boshqariladigan ish stoli tajribasiga qaytish qiyin bo‘ladi!
