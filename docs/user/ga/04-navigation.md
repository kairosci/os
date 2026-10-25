# Nascleanúint

Tarlaíonn gach rud in Arch tríd an méarchlár — _GACH RUD!_ Nuair a thosaíonn an córas den chéad uair, ní féidir leat rud ar bith a dhéanamh leis an luch amháin, go litriúil. Ach is féidir leat `Super + Space` a bhrú chun Roghchlár Arch a nochtadh agus as seo is féidir leat beagnach gach rud a dhéanamh.

Ach níl roghchlár Arch beartaithe fiú a bheith mar an phríomhshlí chun an córas a oibriú an chuid is mó den am. Is féidir linn dul níos tapúla ná sin! Tá na feidhmchláir is tábhachtaí ar fad ceangailte go díreach le heochairbhealaí aonair. Tosaíonn tú an teirminéal le `Super + Return` agus brabhsálaí le `Super + Shift + Return`. Bain triail as ceann i ndiaidh a chéile, agus feicfidh tú draíocht thíleáil Hyprland i ngníomh:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Is féidir leat `Super + J` a bhrú ansin chun iad a chruachadh ar bharr a chéile in ionad taobh le taobh:

 ![navigation-stacked](images/navigation-stacked.webp)

Brúigh `Super + J` arís chun iad a chur ar ais ina suíomhanna taobh le taobh. Ansin bain triail as `Super + Shift + Arrow Right` fad atá tú ar an mbrabhsálaí chun na fuinneoga a mhalartú.

Anois bain triail as `Super + Ctrl + T` chun an monatóir Gníomhaíochta a thosú. Beidh sé sin le feiceáil mar fhuinneog ar snámh. Is féidir leat é a thíleáil le `Super + T` (agus é sin a bhrú arís chun é a chur ar snámh arís). Anois brúigh `Super + Shift + F` chun bainisteoir na gcomhad a oscailt. Beidh socrú néata ceithre threo agat:

 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Déanann tú nascleanúint idir an fhuinneog is mian leat a bheith gníomhach le `Super + Arrow`. Athróidh sé sin an fócas agus bogfaidh sé an cúrsóir go lár an fheidhmchláir nua.

Má bhrúnn tú `Super + Shift + 2`, bogfaidh tú an feidhmchlár atá i bhfócas faoi láthair go dtí an dara spás oibre. Bogann `Super + Shift + 1` ar ais é. (Agus bogfaidh `Super + Shift + Alt + 2` an feidhmchlár atá i bhfócas faoi láthair go dtí an dara spás oibre gan aistriú chuige).

Má choinníonn tú `Super` síos agus má úsáideann tú an luch chun cliceáil ar fhuinneog, beidh tú in ann an áit a shuíonn sí a atheagrú. Má choinníonn tú `Super` síos agus má úsáideann tú an cnaipe deas ar an luch, is féidir leat an fhuinneog a athrú ó thaobh méide de go saor.

Dúnann tú fuinneog ar `Super + W` nó `Super + Q` (agus dúnann tú gach fuinneog ar `Ctrl + Alt + Delete`).

Is féidir leat dul go lánscáileán freisin le `Super + F` nó fiú go lánleithead amháin (agus an barra uachtarach á choinneáil) le `Super + Alt + F` nó lánscáileán laistigh d'fhuinneog le `Super + Ctrl + F` (go maith do YouTube!).

### Leagan amach dwindle in aghaidh scrollaithe

Tugtar dwindle ar leagan amach réamhshocraithe Arch. Coinníonn sé na fuinneoga ar fad a osclaíonn tú ar spás oibre amháin infheicthe an t-am ar fad, fiú má bhíonn air iad a chrapadh.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Ach is féidir leat a roghnú freisin spás oibre a thiontú ina leagan amach scrollaithe ina mbíonn fuinneoga líneáilte taobh le taobh, thar imeall infheicthe an taispeána. Tiontaíonn tú spás oibre amháin isteach sa leagan amach seo trí `Super + L`.

Má bhrúnn tú `Super + L` arís déantar an spás oibre ar snámh, áit a bhforluíonn fuinneoga go saor agus a gcuireann tú féin iad, agus cuireann tríú brú ar ais go dwindle é. Téann `Super + Alt + L` tríothu an treo eile. Fuinneog a bhíonn ar snámh ar aon nós — ceann a phreab tú amach le `Super + T`, nó aip a osclaíonn ar snámh i gcónaí — fanann sí ar snámh nuair a théann an spás oibre ar ais go tíleáil. Marcálann an barra uachtarach an spás oibre a bhfuil tú air lena leagan amach: cearnóg do dwindle, ciorcal do scrollú, agus triantán do snámh. Má chliceálann tú an marc sin timthriallann sé an leagan amach freisin.

 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Is de réir spáis oibre í an rogha, agus fanann sí. Mar sin is féidir leat spás oibre 1 a choinneáil ar dwindle le haghaidh brabhsála agus spás oibre 2 ar scrollú le haghaidh cóid, agus tiocfaidh siad ar ais mar sin tar éis atosú.

Más mian leat an leagan amach scrollaithe a úsáid mar an réamhshocrú, is féidir leat é sin a shocrú in `~/.config/hypr/looknfeel.lua`:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Fuinneoga a ghrúpáil

Is féidir fuinneoga a ghrúpáil le `Super + G`. Nuair a bheidh tú i ngrúpa, beidh gach fuinneog a thosóidh tú fad atá sé sin gníomhach sa ghrúpa. Is féidir leat bogadh idir na fuinneoga grúpáilte seo le `Super + Ctrl + Arrow Left/Right` nó `Super + Alt + 1/2/3/4` chun dul go díreach chuig fuinneog ghrúpáilte in ord.

Is féidir leat fuinneog a bhogadh amach as an ngrúpáil le `Super + Alt + G` nó an grúpa ar fad a dhíchóimeáil trí `Super + G` a bhrú arís. Ar deireadh, is féidir leat fuinneoga lasmuigh den ghrúpa a bhogadh isteach ann le `Super + Alt + Arrows`.

### Spás oibre scratchpad

Ar deireadh, tá spás oibre scratchpad speisialta ann a thiteann síos thar cibé spás oibre a bhfuil tú air faoi láthair, cosúil go mór le consól Quake. Scoránaigh é le `Super + Grave` nó `Super + S`, agus cuir fuinneog ann le `Super + Shift + Grave` nó `Super + Alt + S`.

Oibríonn sé go háirithe go maith do theirminéal a bhfuil gníomhaire á rith aige, nó do rialuithe ar mian leat idirghníomhú leo go tapa gan an spás oibre reatha a fhágáil. Chun fuinneog a bhogadh den scratchpad, seol go díreach chuig spás oibre eile í le rud éigin cosúil le `Super + Shift + 1`.

Fad a choinníonn an scratchpad fuinneog amháin, titeann sé síos mar phainéal lárnaithe seachas a bheith ar fud an scáileáin. Cuir an dara haip air agus téann sé ar ais go dtí an lánleithead, ionas go mbeidh spás ag an dá cheann suí taobh le taobh.

### Tógann sé roinnt dul i dtaithí air!

Tógann sé tamall beag dul i dtaithí ar nascleanúint a dhéanamh ar do dheasc mar seo, ach nuair a dhéanfaidh tú, beidh sé deacair dul ar ais go heispéireas deisce traidisiúnta atá á thiomáint ag an luch!
