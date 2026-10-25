# Matn ajratish va diktovka

### Matn ajratish

Matn ajratish uchun ekranda hudud tanlash uchun `Super + Ctrl + PrtScr` ni bosing. Tesseract ochiq kodli OCR modeli keyin oʻsha tanlovni tezda matnga aylantiradi va buferga joylashtiradi. Keyin qoʻyish uchun shunchaki `Super + V` ni bosasiz.

Bu rasm ost yozuvlaridan manzillarni yoki veb-sayt sarlavhalariga oʻrnatilgan telefon raqamlarini olish uchun juda foydali.

 ![text-extraction](images/text-extraction.webp)

### Diktovka

Yangi oʻrnatishlarda [Superwhisper](https://superwhisper.com/) standart diktovka backendi hisoblanadi, offlayn model yuklab olishlarisiz bulutli qayta ishlashni ishlatadi. Arch menyusidagi _Sozlash > Standartlar > Diktovka_ orqali Superwhisper yoki [Voxtype](https://voxtype.io/) ni tanlang. Backend tanlash kerak boʻlsa uni oʻrnatadi va diktovka uchun standart qiladi. Voxtype 150MB joy egallaydigan bazaviy ingliz modelini yuklaydi; modelni `voxtype setup model` bilan va boshqa sozlamalarni `~/.config/voxtype/config.toml` orqali oʻzgartiring. Superwhisper bulutli yoki mahalliy qayta ishlashni tanlash uchun sozlamalarini ochadi va OPR ilovani yangilab turadi.

Siz `Right Alt` yoki `F9` ni bosib turish yoki `Super + Ctrl + X` bilan almashtirish orqali diktovka qilasiz va aytilgan matn fokuslangan kiritish maydonida paydo boʻladi. Bu yorliqlar tanlangan backendni ishlatadi. Right Alt modifikator akkordida ishlatilganda ham diktovkani boshlaydi; oʻsha akkordlar uchun Left Alt ishlating. Right Alt AltGr boʻlgan klaviatura tartiblarida AltGr ni yozish uchun mavjud qoldirish uchun `F9` ishlating.

Bir xil yorliqlar ikkala backend bilan ham ishlaydi. Backendni Sozlash > Standartlar > Diktovka orqali tanlang. Backend oʻrnatuvchisi uni sozlaydi va tanlovni saqlaydi. Qaysi biri tanlanganini koʻrish uchun `archctl default dictation` ni ishga tushiring. Tanlov `~/.config/arch/defaults/dictation` da saqlanadi. Yangi oʻrnatishlar Superwhispen ni avtomatik tanlaydi.

Arch tanlangan backendning ish stoli integratsiyasini avtomatik yuklaydi. `~/.config/hypr/` da Superwhisper konfiguratsiyasi kerak emas.

Maxsus bogʻlanishlar va skriptlar `arch dictation start`, `arch dictation stop` va `arch dictation toggle` ishlatishi mumkin. Tanlangan backend yozuv va transkripsiyani bajaradi. Superwhispen ni tanlash uning mahalliy ushlab turish yorligʻini oʻchiradi va mahalliy almashtirishini `Alt + Space` ga oʻrnatadi, uni Archning yozuv tugmalaridan alohida saqlaydi. Superwhisper kamida bitta mahalliy yozuv yorligʻini talab qiladi va uning bekor qilish yorligʻi mavjud qoladi.

Qoʻshimcha backendlar Archni oʻzgartirmasdan integratsiya qilinishi mumkin. PATH da `start`, `stop` va `toggle` ni qabul qiladigan va tezda qaytadigan, xatoda nolga teng boʻlmagan holat qaytaradigan `arch-dictation-<backend>` nomli bajariluvchi faylni taqdim eting. Uning oʻrnatuvchisi provayderni sozlaydi va muvaffaqiyatli sozlashdan keyin `arch-dictation-use <backend>` ni chaqiradi. Bu avvalgi backendni toʻxtatadi va tanlovni atomik saqlaydi; `stop` provayder boʻsh yoki mavjud boʻlmaganda muvaffaqiyatli boʻlishi kerak. Backend nomlari kichik harflar, raqamlar va chiziqchalarni ishlatadi. Sozlash uchun `arch-install-dictation-<backend>` ni taqdim eting; `archctl default dictation <backend>` uni ishga tushiradi. Oʻsha tanlovchini chaqirish uchun Arch menyu kengaytmasi orqali Standartlar menyu yozuvini qoʻshing. Ixtiyoriy ish stoli integratsiyasi `${XDG_CONFIG_HOME:-$HOME/.config}/<backend>/shortcuts.lua` da yashashi mumkin.
