# Güncellemeler

Arch ve paketleriniz, Arch menüsündeki (`Super + Space`) _Güncelle > Arch_ aracılığıyla güncel tutulur.

Arch'nin kendisi, [Arch Package Repository](https://github.com/kairosci/os) üzerinden normal pacman paketleri olarak kurulur; bu yüzden bir güncelleme, [en son Arch sürümünü](https://github.com/kairosci/os) kurar, sisteminizi en son sürümle senkronize etmek için bekleyen taşımaları çalıştırır ve [Arch Arch Mirror](https://github.com/kairosci/os) ve [AUR](https://aur.archlinux.org/) (herhangi bir AUR paketi kurduysanız) üzerinden tüm sistem paketlerini günceller.

Yeni sürümler yayınlandığında, saatinizin sağında bir daire ok simgesi belirecektir. Ona tıklayın, güncelleme süreci başlayacaktır.

![update-available](images/update-available.webp)

### Dört kanal

Arch dört kanal boyunca güncellenir: stable, RC, edge ve dev. Yeni kurulumlar, [resmi sürümleri](https://github.com/kairosci/os) izleyen stable kanalında başlar; ayrıca en son sürümün bir ay gerisinde çalışan [stable Arch Arch aynası](https://github.com/kairosci/os) kullanılır, böylece yapılandırma değişiklikleri gerektiren yeni uyumsuzlukları, insanlara sorun çıkarmadan önce yakalayabiliriz.

Ancak bu olası sorunları tespit etmeye yardımcı olmak isterseniz edge kanalında çalışabilirsiniz. Bu, Arch paketlerinizin en son geliştirme sürümlerini izlemesini sağlar ve en son Arch paketlerine kullanılabilir olur olmaz güncellemenize olanak tanır. Bunu yalnızca Linux konusunda deneyimliyseniz ve sorun yaşayan bir sistemi nasıl kurtaracağınızı biliyorsanız yapmalısınız.

Herhangi bir büyük yeni sürümden önce, RC kanalını kullanarak son doğrulamayı yapacağız. Son rötuşlara yardım etmekle ilgileniyorsanız, Discord'da #arch-release-candidates kanalına gelin.

Son olarak, Arch'yi `~/arch` içindeki kaynak kodun bir git kopyasına doğrudan bağlayan ve edge paketleriyle birleştiren dev kanalı vardır. Bu kanalı yalnızca doğrudan Arch üzerinde çalışan ve bozulmaya katlanmaya hazır deneyimli bir Linux kullanıcısıysanız kullanmalısınız.

Arch menüsünden _Güncelle > Channel_ (veya terminalde `arch-channel-set`) kullanarak kanallar arasında geçiş yapabilirsiniz.

### Bellenim güncellemeleri

Güncel olmayan tek şey paketleriniz değildir. Birçok dizüstü bilgisayar ve çevre birimi, Linux Vendor Firmware Service aracılığıyla BIOS, SSD ve dock bellenimi gönderir ve Arch menüsündeki _Güncelle > Firmware_, donanımınızın bekleyen her şeyini alıp kuracaktır. İlk çalıştırdığınızda `fwupd` kurar. Çok fazla bellenim yalnızca yeniden başlatma sırasında yazılabilir, bu yüzden bir tane istenirse şaşırmayın.

### Doğrudan pacman/yay güncellemeleri hakkında uyarı

Arch'a zaten aşinaysanız, kendinizi sadece `pacman -Syu` veya `yay -Syu` çalıştırmaya cazip bulabilirsiniz, ancak bunu yaparsanız Arch'nin yeni paketlerle birlikte çalıştırdığı anlık görüntüyü, taşımaları ve yapılandırma güncellemelerini kaçırırsınız. Bu yüzden Arch aslında doğrudan bir sistem yükseltmesini durduracak ve sizi bunun yerine `archctl update` komutuna yönlendirecektir. (Gerçekten ne yaptığınızı biliyorsanız, koruma size tek bir işlem için bunu nasıl atlayacağınızı söyleyecektir.)

### Kötü güncellemeleri geri almak

Bir güncelleme yaptıktan sonra bir sorun yaşarsanız, sisteminizi güncellemeden önce alınan anlık görüntüye geri alabilirsiniz. Sadece yeniden başlatın ve önyükleme yükleme menüsünde, güncellemeyi başlatmadan önceki anlık görüntüyü seçin.

![bootloader](images/bootloader.webp)

Yapılandırma dosyalarınız bir şekilde bozulduysa, terminalde `arch reinstall` kullanarak bir Arch yeniden kurulumu da gerçekleştirebilirsiniz. Bu, tüm varsayılan Arch paketlerini yeniden kuracak, sizi stable'a koyacak ve çok yeni olan paketleri düşürecek ve tüm yapılandırma dosyalarını sıfırlayacaktır. Bunu yaparken Arch varsayılanlarına yaptığınız tüm kullanıcı yapılandırma değişikliklerinin üzerine yazılacağını unutmayın!
