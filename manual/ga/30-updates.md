# Nuashonruithe

Coinnítear Arch agus do phacáistí cothrom le dáta trí _Nuashonraigh > Arch_ sa roghchlár Arch (`Super + Space`).

Suiteáiltear Arch féin mar phacáistí rialta pacman ó [Stóras Pacáistí Arch](https://github.com/kairosci/arch), mar sin suiteálann nuashonrú [an t-eisiúint Arch is déanaí](https://github.com/kairosci/arch), ritheann sé aon imircí ar feitheamh chun do chóras a chur i sioncron leis an gceann is déanaí, agus nuashonraíonn sé pacáistí córais go léir ó [Scáthán Arch Arch](https://github.com/kairosci/arch) agus [AUR](https://aur.archlinux.org/) (má tá aon phacáistí AUR suiteáilte agat).

Nuair a dhéantar eisiúintí nua, taispeánfar deilbhín saighead chiorcail ar thaobh deas do chloig. Cliceáil air agus tosóidh an próiseas nuashonraithe.

![update-available](images/update-available.webp)

### Ceithre bhealach

Nuashonraítear Arch feadh ceithre bhealach: stable, RC, edge, agus dev. Tosaíonn suiteálacha nua ar an mbealach cobhsaí, a rianaíonn na [heisiúintí oifigiúla](https://github.com/kairosci/arch), chomh maith le [scáthán Arch Arch cobhsaí](https://github.com/kairosci/arch) atá ag rith mí amháin chun deiridh ar an gceann is déanaí, ionas gur féidir linn aon neamh-chomhoiriúnachtaí nua a éilíonn athruithe cumraíochta a ghabháil sula gcuirfidh siad fadhbanna ar dhaoine.

Ach más mian leat cabhrú leis na fadhbanna féideartha sin a aimsiú, is féidir leat rith ar bhealach edge. Coinneoidh sé sin do phacáistí Arch ag rianú na leaganacha forbartha is déanaí, agus ligeann duit nuashonrú chuig na pacáistí Arch is déanaí a luaithe atá siad ar fáil. Níor chóir duit é seo a dhéanamh ach má tá taithí agat le Linux, agus má tá a fhios agat conas córas a bhfuil fadhbanna aige a aisghabháil.

Roimh aon phríomh-eisiúint nua, beimid ag déanamh bailíochtú deiridh ag úsáid an bhealaigh RC. Má tá suim agat cabhrú leis an snasú deiridh, tar croch amach i #arch-release-candidates ar an Discord.

Mar fhocal scoir, tá an bealach dev ann, a nascann Arch go díreach le seiceáil amach git den chód foinse in `~/arch`, in éineacht le pacáistí edge. Níor chóir duit an bealach seo a úsáid ach más úsáideoir Linux le taithí tú, ag obair go díreach ar Arch, agus toilteanach briseadh a fhulaingt.

Is féidir leat aistriú idir bealaí trí _Nuashonraigh > Bealach_ a úsáid ón roghchlár Arch (nó `arch-channel-set` sa teirminéal).

### Nuashonruithe firmearta

Ní hé amháin do phacáistí a théann as dáta. Seolann go leor ríomhairí glúine agus forimeallacha BIOS, SSD, agus firmearta duga trí Sheirbhís Firmearta Soláthraí Linux, agus gheobhaidh _Nuashonraigh > Firmearta_ sa roghchlár Arch agus suiteálfaidh sé cibé rud atá ag fanacht ag do chrua-earraí. Suiteálann sé `fwupd` an chéad uair a rithann tú é. Ní féidir a lán firmearta a scríobh ach le linn atosaigh, mar sin ná bíodh iontas ort má iarrtar ceann ort.

### Rabhadh faoi nuashonruithe díreacha pacman/yay

Má tá tú eolach ar Arch cheana, b'fhéidir go dteastaíonn uait `pacman -Syu` nó `yay -Syu` a rith leat féin, ach má dhéanann tú é sin, caillfidh tú an seat, na himircí, agus na nuashonruithe cumraíochta a ritheann Arch mar aon le pacáistí nua. Sin an fáth go stopfaidh Arch uasghrádú díreach córais i ndáiríre agus go ndíreoidh sé tú chuig `archctl update` ina ionad. (Má tá a fhios agat i ndáiríre cad atá á dhéanamh agat, inseoidh an garda duit conas é a sheachaint d'idirbheart amháin.)

### Nuashonruithe dona a aischur

Má bhíonn fadhb agat riamh tar éis nuashonrú a dhéanamh, is féidir leat do chóras a aischur chuig an seat a tógadh roimh an nuashonrú. Atosaigh agus pioc an seat sa roghchlár lódála tosaithe ón am sular thosaigh tú an nuashonrú.

![bootloader](images/bootloader.webp)

Má tá do chomhaid chumraíochta truaillithe ar bhealach éigin, is féidir leat athshuiteáil Arch a dhéanamh freisin trí `arch reinstall` a úsáid sa teirminéal. Athshuiteálfaidh sé seo na pacáistí réamhshocraithe Arch go léir, cuirfidh sé tú ar stable agus ísleoidh sé aon phacáistí atá ró-nua, agus athshocróidh sé na comhaid chumraíochta go léir. Tabhair faoi deara go bhforscríobhfar do athruithe cumraíochta úsáideora go léir ar réamhshocruithe Arch agus seo á dhéanamh!
