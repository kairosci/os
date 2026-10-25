# Gezinme

Arch'de her şey klavyeyle olur — _HER ŞEY!_ Sistem ilk başladığında, yalnızca fareyle kelimenin tam anlamıyla hiçbir şey yapamazsınız. Ama `Super + Space` tuşlarına basarak Arch Menüsü'nü açabilirsiniz ve buradan hemen hemen her şeyi yapabilirsiniz.

Ama Arch menüsünün çoğu zaman sistemi kullanmanın ana yolu olması bile amaçlanmıyor. Bundan daha hızlı olabiliriz! En önemli uygulamaların hepsi doğrudan tek tek kısayol tuşlarına bağlı. Terminali `Super + Return` ile, bir tarayıcıyı `Super + Shift + Return` ile başlatırsınız. Birini diğerinin ardından açmayı deneyin, Hyprland'in döşeme büyüsünü iş başında göreceksiniz:

 ![navigation-browser-terminal](images/navigation-browser-terminal.webp)

Ardından yan yana olmak yerine üst üste dizmek için `Super + J` tuşlarına basabilirsiniz:

 ![navigation-stacked](images/navigation-stacked.webp)

Yan yana konumlarına geri döndürmek için tekrar `Super + J` tuşlarına basın. Ardından tarayıcıdayken pencereleri takas etmek için `Super + Shift + Arrow Right` tuşlarını deneyin.



 ![navigation-fourway-tiling](images/navigation-fourway-tiling.webp)

Etkin olmasını istediğiniz pencere arasında `Super + Arrow` ile gezinirsiniz. Bu, odağı değiştirir ve imleci yeni uygulamanın ortasına taşır.

`Super + Shift + 2` tuşlarına basarsanız, o anda odaklanılan uygulamayı ikinci çalışma alanına taşırsınız. `Super + Shift + 1` onu geri taşır. (`Super + Shift + Alt + 2` ise o anda odaklanılan uygulamayı, o çalışma alanına geçmeden ikinci çalışma alanına taşır).

`Super` tuşunu basılı tutar ve bir pencereye tıklamak için fareyi kullanırsanız, nerede durduğunu yeniden düzenleyebilirsiniz. `Super` tuşunu basılı tutar ve farenin sağ düğmesini kullanırsanız, pencereyi serbestçe yeniden boyutlandırabilirsiniz.

Bir pencereyi `Super + W` veya `Super + Q` ile kapatırsınız (ve tüm pencereleri `Ctrl + Alt + Delete` ile kapatırsınız).

Ayrıca `Super + F` ile tam ekrana veya `Super + Alt + F` ile yalnızca tam genişliğe (üst çubuğu koruyarak) veya `Super + Ctrl + F` ile bir pencere içinde tam ekrana geçebilirsiniz (YouTube için harika!).

### Dwindle ile kayan düzen

Arch'nin varsayılan düzenine dwindle denir. Bir çalışma alanında açtığınız tüm pencereleri, onları küçültmek zorunda kalsa bile her zaman görünür tutar.

 ![navigation-dwindle-layout](images/navigation-dwindle-layout.webp)

Ama bir çalışma alanını, pencerelerin ekranın görünür kenarının ötesine yan yana dizildiği kayan düzene çevirmeyi de seçebilirsiniz. Tek bir çalışma alanını `Super + L` ile bu düzene çevirirsiniz.


 ![navigation-scrolling-layout](images/navigation-scrolling-layout.webp)

Seçim çalışma alanı başına yapılır ve kalıcıdır. Böylece 1. çalışma alanını gezinme için dwindle düzeninde ve 2. çalışma alanını kod için kayan düzende tutabilirsiniz; yeniden başlatmanın ardından da öyle geri gelirler.

Kayan düzeni varsayılan olarak kullanmak isterseniz, bunu `~/.config/hypr/looknfeel.lua` içinde ayarlayabilirsiniz:

```lua
hl.config({
  general = {
    layout = "scrolling",
  },
})
```

### Pencereleri gruplama

Pencereler `Super + G` kullanılarak gruplanabilir. Bir gruba girdikten sonra, bu etkinken başlattığınız her pencere gruba ait olacaktır. Bu gruplanmış pencereler arasında `Super + Ctrl + Arrow Left/Right` kullanarak veya doğrudan sırayla gruplanmış pencereye gitmek için `Super + Alt + 1/2/3/4` kullanarak gezinebilirsiniz.

Bir pencereyi `Super + Alt + G` ile gruptan çıkarabilir veya tekrar `Super + G` tuşlarına basarak tüm grubu dağıtabilirsiniz. Son olarak, grup dışındaki pencereleri `Super + Alt + Arrows` ile grubun içine taşıyabilirsiniz.

### Scratchpad çalışma alanı

Son olarak, bir Quake konsolu gibi, o anda üzerinde olduğunuz çalışma alanının üzerine açılan özel bir scratchpad çalışma alanı vardır. Onu `Super + Grave` veya `Super + S` ile açıp kapatın ve `Super + Shift + Grave` veya `Super + Alt + S` kullanarak oraya bir pencere yerleştirin.

Özellikle bir ajan çalıştıran bir terminal için veya geçerli çalışma alanından ayrılmadan hızla etkileşime girmek istediğiniz kontroller için çok iyi çalışır. Bir pencereyi scratchpad'den taşımak için, onu `Super + Shift + 1` gibi bir kısayolla doğrudan başka bir çalışma alanına gönderin.

Scratchpad tek bir pencere tutarken, ekranı kaplamak yerine ortalanmış bir panel olarak açılır. Üzerine ikinci bir uygulama koyarsanız tam genişliğe geri döner, böylece ikisinin yan yana duracak yeri olur.

### Alışmak biraz zaman alıyor!

Masaüstünüzde bu şekilde gezinmeye alışmak biraz zaman alıyor, ama alıştığınızda geleneksel fare odaklı bir masaüstü deneyimine geri dönmek zor olacaktır!
