# Muud paketid

Archil on hämmastav rikkus pakette peaaegu igat liiki tarkvara jaoks ametliku repo ja Arch User Repository (AUR) vahel.

See ei saaks olla ka lihtsamini kasutatav. Uue Archi paketi paigaldad, minnes Arch menüüs (`Super + Space`) jaotisesse _Paigalda > Package_ ja sisestades soovitud paketi. See filtreerib automaatselt uduselt kõigi pakettide loendit. (Saad seda teha ka käsitsi, kasutades terminalis käsku `archctl pkg add [package]`).

AUR-iga saad teha sama, kasuta lihtsalt jaotist _Paigalda > AUR_. Pea meeles, et AUR-i pole Archi meeskond kontrollinud. See on nagu RubyGems või npm. Igaüks saab üles laadida.

Kui soovid paketti eemaldada, saad kasutada Arch menüü jaotist _Eemalda > Package_. See eemaldab paketi, konfiguratsioonifailid ja sõltuvused. (Saad seda teha ka käsitsi, kasutades käsku `archctl pkg drop [package]`).
