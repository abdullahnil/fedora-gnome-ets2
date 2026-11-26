# fedora-gnome-ets2

**Euro Truck Simulator 2**'yi Fedora + GNOME'da, Windows'taki kadar akıcı oynamak için kurulum, taşıma ve takılma teşhis aracı.

Araç, bir laptopta (HP Victus 16, Intel i7-14700HX, RTX 4060 Laptop, 144 Hz harici monitör) ETS2'yi Windows 11'den Fedora 44'e taşırken yaşanan her sorunun ölçülerek çözülmesiyle ortaya çıktı. Bu README hem aracın nasıl kullanılacağını hem de **neden bu ayarların seçildiğini**, yani hangi ölçümün hangi kararı doğurduğunu anlatıyor.

```bash
git clone https://github.com/abdullahnil/fedora-gnome-ets2.git
cd fedora-gnome-ets2
./fedora-gnome-ets2 kur          # her şeyi ayarla
./fedora-gnome-ets2 tasi         # (isteğe bağlı) Windows'tan oyunu ve profilleri al
./fedora-gnome-ets2 truckersmp   # (isteğe bağlı) çok oyunculu
./fedora-gnome-ets2 teshis       # takılma varsa sebebini bul
```

---

## İçindekiler

1. [Komutlar](#komutlar)
2. [Neden Proton? (yerel Linux sürümü değil)](#neden-proton)
3. [`kur` ne yapar? Her ayar ve sebebi](#kur-ne-yapar)
4. [Windows'tan taşıma](#windowstan-taşıma)
5. [TruckersMP](#truckersmp)
6. [Takılma avı: 30 saniyede bir gelen donma](#takılma-avı)
7. [FPS sınırı ve 144 Hz](#fps-sınırı-ve-144-hz)
8. [Ölçüm sonuçları](#ölçüm-sonuçları)
9. [Bilinen sorunlar](#bilinen-sorunlar)
10. [Geri alma ve kaldırma](#geri-alma-ve-kaldırma)

---

## Komutlar

| Komut | Ne yapar |
|---|---|
| `kur` | gamemode ve MangoHud'u kurar, donanımı algılar, ETS2'yi Proton Experimental'a zorlar, başlatma seçeneklerini ve MangoHud ayarını yazar. |
| `tasi` | Windows bölümünü **salt okunur** bağlar, oyunu (yeniden indirmemek için) ve profilleri/modları/ayarları kopyalar. Windows'ta hiçbir şeyi değiştirmez. |
| `truckersmp` | `truckersmp-cli`'yi kurar, Steam'deki oyunu kullanan bir başlatıcı ve menü girişi ekler, sürüm uyumunu kontrol eder. |
| `teshis` | GNOME Shell'in donup donmadığını ölçer, donmalar düzenliyse aralığını bulur ve zamanlayıcılı eklentileri listeler. |
| `teshis --dene EKLENTI` | Bir eklentiyi kapatıp yeniden ölçer: suçlu o mu, değil mi, değilse nerede aramalı. |
| `analiz [KAYIT\|KLASÖR]` | MangoHud kayıtlarını akıcılık değerleriyle karşılaştırmalı tabloya döker. |
| `oyunda-kapat [EKLENTI]` | Oyun açıkken kendiliğinden kapatılacak GNOME eklentilerini listeler ya da listeye ekler. |
| `durum` | Şu anki Proton, başlatma seçenekleri ve ayarları gösterir. |
| `geri-al` | Steam ayar dosyalarını aracın ilk çalıştırılmasından önceki hâline döndürür. |

Steam ayarlarını değiştiren komutlar (`kur`, `tasi`, `geri-al`) Steam'i kısa süreliğine kapatır, çünkü Steam açıkken kendi ayar dosyalarının üstüne yazar. Değiştirilen her dosyanın tarihli bir yedeği (`.yedek-YYYYAAGG-SSDDss`) alınır.

**Gereksinimler:** Fedora (paketler `dnf` ile kurulur), GNOME, Steam (yerel paket; Flatpak Steam da bulunur ama denenmedi), Python 3. NVIDIA'ya ve Intel hibrit işlemcilere özel ayarlar yalnızca o donanım varsa eklenir.

---

## Neden Proton?

ETS2'nin yerel bir Linux sürümü var, ama **Windows sürümünü Proton ile çalıştırmak** daha iyi sonuç veriyor:

| Yol | Durum |
|---|---|
| Yerel Linux sürümü | **OpenGL** kullanıyor. Kullanıcı raporlarına göre Windows'taki DirectX 11'den belirgin şekilde yavaş. |
| Yerel sürümde Vulkan (`-rdevice vk`) | SCS'ye göre **deneysel ve desteklenmiyor**. 1.60 ve Benelux güncellemesinden sonra bozuk görüntü raporları var. |
| **Windows sürümü + Proton** (DirectX 11 → DXVK → Vulkan) | Raporlarda Windows'la aynı ya da daha iyi. Bir yan faydası da var: Windows'taki oyun dosyaları, `config.cfg` ve modlar birebir kullanılabiliyor. |

Kaynaklar: [ProtonDB](https://protondb.com/app/227300), [SCS forumu: Vulkan deneysel](https://forum.scssoft.com/viewtopic.php?p=2140165), [SCS forumu: Linux için resmi Vulkan isteği (2026)](https://forum.scssoft.com/viewtopic.php?p=2157333).

---

## `kur` ne yapar?

### Proton Experimental'a zorlama
Steam'in ayarında (`config.vdf` → `CompatToolMapping`) ETS2 `proton_experimental`'a zorlanır. Bu, taşımada da önemli: zorlanmazsa Steam Linux sürümünü indirip Windows'tan kopyalanan dosyaların üstüne yazar.

### Başlatma seçenekleri
Araç donanıma göre şuna benzer bir satır üretir:

```
DXVK_FILTER_DEVICE_NAME=NVIDIA __NV_PRIME_RENDER_OFFLOAD=1 __VK_LAYER_NV_optimus=NVIDIA_only
__GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1 MANGOHUD_CONFIGFILE=$HOME/.config/MangoHud/ets2.conf
gamemoderun taskset -c 0-15 mangohud %command% -nointro
```

| Parça | Neden |
|---|---|
| `DXVK_FILTER_DEVICE_NAME=NVIDIA` | Hibrit laptoplarda DXVK bazen Intel'i seçiyor. Bu sistemde eFootball'da DXVK'nın ikinci bir aygıtı Intel'de açtığı görüldü. ETS2 günlüğünde artık tek ekran kartı olarak `NVIDIA GeForce RTX 4060M` görünüyor. *(yalnızca NVIDIA + başka bir GPU varsa)* |
| `__NV_PRIME_RENDER_OFFLOAD=1 __VK_LAYER_NV_optimus=NVIDIA_only` | NVIDIA'nın PRIME yük aktarımı: oyun NVIDIA'da çizilir, Vulkan Intel'i hiç görmez. *(hibrit)* |
| `__GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1` | NVIDIA'nın gölgelendirici önbelleği boyut sınırına gelince kendini temizlemesin. Temizlenirse daha önce gördüğün yerlerde gölgelendiriciler yeniden derlenir, bu da takılma demek. *(NVIDIA)* |
| `gamemoderun` | Oyun açıkken işlemciyi performans moduna alır. Günlükte görünen `libgamemode.so: cannot open shared object file` uyarıları zararsız: Steam'in yalıtılmış çalışma ortamının içindeki süreçlerden geliyor, oyun modunu dışarıdaki süreç açıyor. |
| `taskset -c 0-15` | **Yalnızca hızlı çekirdekler.** Intel 12. nesil ve sonrası işlemcilerde iki tür çekirdek var (14700HX'te 8 hızlı çekirdek = 16 iş parçacığı, 5,3-5,5 GHz; 12 verimlilik çekirdeği, 3,9 GHz). Windows'un zamanlayıcısı oyunu hızlı çekirdeklerde tutar, Linux her zaman tutamaz; ETS2'nin ana iş parçacığı yavaş çekirdeğe düşerse kare kaçar. Liste `/sys/devices/cpu_core/cpus`'tan otomatik okunur. *(Intel hibrit işlemci)* |
| `mangohud` | FPS ve kare süresi göstergesi. Kendi ayar dosyası `MANGOHUD_CONFIGFILE` ile verilir. |
| `-nointro` | Açılış videolarını atlar. |

### MangoHud ayarı (`~/.config/MangoHud/ets2.conf`)
- **Kare süresi grafiği:** takılmalar grafikte sivri tepe olarak görünür.
- **Tuşlar:**
  - **Sol Shift+F1:** FPS sınırını değiştirir (60 → 72 → 48 → sınırsız).
  - **Sol Shift+F2:** 120 saniyelik kayıt başlatır.
  - **Sağ Shift+F12:** göstergeyi gizler ya da gösterir.
- **Kayıtlar:** `~/Documents/MangoHud-kayitlar` klasörüne yazılır, `analiz` komutuyla okunur.

### Oyunda takılma yapan eklentileri kapatma
`kur` küçük bir düzenek kurar. Oyun `gamemoderun` ile başladığında, listedeki GNOME eklentileri kendiliğinden kapatılır; oyun bitince (çökse bile) geri açılır. Böylece sevdiğin ama oyunda takılma yapan bir eklentiyi masaüstünde kullanmaya devam edebilirsin. Varsayılan listede yalnızca [takılma avında](#takılma-avı) bulunan public-ip-address var.

| Dosya | Görevi |
|---|---|
| `~/.config/oyun-eklentileri.conf` | Oyunda kapatılacak eklentiler, her satıra bir kimlik. `fedora-gnome-ets2 oyunda-kapat EKLENTI` ile de eklenebilir. |
| `~/.local/bin/oyun-eklentileri` | Kapatıp açan betik. Yalnızca **kendi kapattıklarını** geri açar; sen bilerek kapattığın bir eklentiyi açmaz. |
| `~/.config/gamemode.ini` | gamemode'a oyun başlarken ve biterken bu betiği çalıştırmasını söyler (`[custom] start=` / `end=`). |

Notlar:
- **Mevcut `gamemode.ini`:** dosyada zaten bir `[custom]` bölümü varsa araç ona dokunmaz, ne eklenmesi gerektiğini yazar.
- **Split lock:** split lock koruması zaten kapalıysa (`kernel.split_lock_mitigate=0`) `disable_splitlock=0` da eklenir. Böylece gamemode'un her oyunda yetkisiz denediği ve günlüğü kirleten `Failed to update split_lock_mitigate` hatası susar.
- **Açılıştaki tek takılma:** GNOME bir eklentiyi kapatınca ondan sonra yüklenen eklentileri de bir kez yeniden başlatır. Bu, oyunun açılış ekranında belki tek bir anlık takılma yapar; sürüş sırasında bir etkisi yoktur.
- **Kalan hata:** günlükte kalan `Failed to update cpu governor policy` hatası da zararsız. gamemode işlemciyi performans kipine almaya çalışıyor ama yetkisi yok; işlemci tuned sayesinde zaten o kipte.

### Kontrol edilenler
- **Güç profili:** HP laptoplarda `performance` olmalı. Bu, Windows'taki OMEN Gaming Hub Performans modunun karşılığı.
- **Ekran kartı güç sınırı:** bu sistemde NVIDIA Dynamic Boost çalışıyor ve sınır 80 W'tan 118 W'a kadar çıkıyor. Yani Linux kartı kısmıyor.

---

## Windows'tan taşıma

`tasi` komutu:

1. NTFS bölümlerini bulur ve **salt okunur** bağlar. BitLocker ile şifreli bölümleri atlar. İş bitince bağladıklarını ayırır.
2. Oyunu (`steamapps/appmanifest_227300.acf` + `common/Euro Truck Simulator 2`) ve belgeler klasörünü (`Users/*/Documents/Euro Truck Simulator 2`, OneDrive dahil) bulur.
3. **Oyun dosyalarını kopyalar.** Bu sistemde 37 GB, NVMe'den NVMe'ye 23 saniye sürdü. Steam bunları görüp oyunu yalnızca eksik parçaları indirerek günceller. Proton aynı Windows dosyalarını kullandığı için bu güvenli.
4. Oyunu bir kez açıp kapatır, çünkü Proton'un sanal Windows klasörü (`compatdata/227300/pfx`) ilk açılışta oluşuyor.
5. Profilleri, modları ve ayarları oraya kopyalar ve Windows'takilerle karşılaştırarak doğrular.

| | Taşınır mı? |
|---|---|
| Oyun dosyaları | Evet. 37 GB'lık indirmeden kurtarır. |
| `profiles/` (yerel profiller) | Evet |
| `steam_profiles/` | Zaten Steam Cloud'da, kendiliğinden gelir. Güvenlik için yine de kopyalanır. |
| `mod/` | Evet. `.scs` modlar Linux'ta aynen çalışır. |
| `config.cfg` | Evet. Aynı Windows sürümü çalıştığı için grafik ayarların birebir geçerli. |
| `screenshot/`, `music/` | Evet |
| `profiles(…).bak`, `cache/`, günlükler | Hayır. Bunlar oyunun her sürüm güncellemesinde aldığı otomatik yedekler (bu sistemde 1,1 GB) ve geçici dosyalar. |

**Güvenlik:** Linux'ta zaten profil varsa (yani taşımadan sonra oynamaya başladıysan) araç önce onay ister, mevcut profillerin `.tar.gz` yedeğini alır, ve Windows'taki dosyaları yalnızca Linux'takinden **daha yeni** olanların üstüne yazar (`rsync --update`). Linux'ta oynanmış bir kayıt eski Windows kaydıyla ezilmez.

**Kontroller:** Klavye ve fare atamaları aynen gelir. Gamepad, direksiyon gibi DirectInput aygıtları Linux'ta farklı kimlikle göründüğü için oyunun kontrol ayarlarından yeniden atanmaları gerekir.

---

## TruckersMP

TruckersMP Linux'u resmi olarak desteklemiyor. Topluluğun yaptığı [`truckersmp-cli`](https://github.com/truckersmp-cli/truckersmp-cli) aracıyla Proton üzerinden çalışıyor. `truckersmp` komutu bu aracı `pipx` ile kurar ve `~/.local/bin/truckersmp-ets2` başlatıcısını yazar.

Başlatıcının yaptığı seçimler ve sebepleri:

| Seçim | Neden |
|---|---|
| `start` komutu (`update` değil) | `update` Steam'i kapatır ve oyunu SteamCMD ile ayrıca indirmeye kalkar. `start` yalnızca TruckersMP'nin kendi dosyalarını indirir. |
| `--gamedir`: Steam'deki oyun | İkinci bir 37 GB kopyaya gerek kalmaz. |
| `--protondir`: Steam'in Proton Experimental'ı | Aracın varsayılanı Proton 8. Onu ayrıca indirmek SteamCMD gerektiriyor. |
| `--steamruntimedir`: Proton'un istediği Steam Linux Runtime | Proton'un `toolmanifest.vdf` dosyasındaki `require_tool_appid` alanından otomatik bulunur. |
| `--rendering-backend dx11` | Aracın varsayılanı **OpenGL**. DX11 (DXVK) daha hızlı. |
| Ayrı Proton klasörü, ortak belgeler klasörü | TruckersMP kendi Windows klasörünü kullanır, böylece tek oyunculu oyunun klasörü farklı ayarlarla açılıp bozulmaz. Ama `Documents/Euro Truck Simulator 2` bir bağlantıyla tek oyunculu oyununkine yönlendirilir: profiller, ayarlar ve modlar ortak. |
| `PULSE_LATENCY_MSEC=60` | İlk açılışta görülen ses takılmasına karşı daha büyük ses tamponu. |

**Dikkat:**
- Terminalde düz `truckersmp-cli` çalıştırma. O zaman araç kendi Proton klasörünü arar ve şu hatayı verir: `Proton is not found in ~/.local/share/truckersmp-cli/Proton — Run with '--update'`. Önerdiği `--update`'i de uygulama. Her zaman menüdeki **TruckersMP (Euro Truck Simulator 2)** girişini ya da `truckersmp-ets2` komutunu kullan.
- **Sürüm gecikmesi:** Steam ETS2'yi güncellediğinde TruckersMP o sürüme yetişene kadar çok oyunculu açılmaz. Bu genelde birkaç gün sürer ve Windows'ta da aynıdır. `truckersmp` komutu iki sürümü karşılaştırır: [TruckersMP API](https://api.truckersmp.com/v2/version) ile oyun günlüğündeki `init ver.` satırı.
- **İlk açılış:** TruckersMP'nin kendi klasörü ilk açılışta oluşuyor. Ortak profil bağlantısı **ikinci açılışta** kurulur, yani ilk açılıştan sonra oyunu bir kez kapatıp yeniden aç.

---

## Takılma avı

Taşımadan sonra FPS kabul edilebilirdi ama oyunda **düzenli, rahatsız edici anlık kesilmeler** vardı. Sebep beklenmedik bir yerden çıktı. Tahmin yerine her adımda ölçüm yapıldı.

### 1. Ölçüm: takılmalar saat gibi
MangoHud ile 2 dakikalık kayıt alındı. 60 FPS'te akan oyunda 115 ms'lik takılmalar (yaklaşık 7 kare) **tam 30,0 saniye arayla** geliyordu: 14,7 · 44,7 · 74,7 · 104,7. saniyelerde. Ekran kartı yükü %91'di. Ölçeklemeyi %400'den %200'e indirmek FPS'i değiştirmemişti.

Rastgele değil düzenli bir takılma, oyunun kendisinden değil **sistemde zamanlayıcıyla çalışan bir şeyden** kaynaklanır.

### 2. Elenen şüpheliler

| Şüpheli | Nasıl elendi |
|---|---|
| Ölçekleme / ekran kartı | Takılma FPS'ten bağımsız, aralığı sabit. |
| Pil okuması (laptoplarda BIOS'un bütün işlemciyi durdurması bilinen bir sorun) | Pil okuması anlık (0,00 sn). Oyun kapalıyken 95 saniyede 30 ms'yi aşan tek bir sistem duraklaması bile yok. |
| Split lock cezası (Intel'de bazı Windows oyunlarını yavaşlatır) | `kernel.split_lock_mitigate = 0` (ceza zaten kapalı) ve oyun hiç split lock tuzağına düşmemiş. |
| Vitals eklentisi (`nvidia-smi` sorguları) | Her **5** saniyede sorguluyor, 30 değil. |
| thermald (Intel ısı servisi) | 30 saniyelik döngüsü takılmalara 0,1 sn farkla denk geliyordu. Durdurup tekrar test edildi: takılmalar sürdü. |
| MangoHud'un kendisi | İki ayrı oyun oturumunda takılmalar saatin **aynı saniyelerinde** (:17,6 ve :47,6) geldi. Oyun ya da MangoHud kaynaklı olsaydı her açılışta kayardı. Yani sebep sürekli çalışan bir şey. |

### 3. Asıl sebep: GNOME Shell donuyordu
Oyunun görüntüsünü ekrana GNOME Shell basıyor. Shell bir anlığına donarsa oyunun karesi de ekrana çıkamıyor; masaüstünde ise 100 ms'lik bir donma neredeyse fark edilmiyor. Shell'e D-Bus üzerinden saniyede onlarca kez küçük bir soru soran bir yoklayıcı yazıldı (`araclar/shell_yokla.py`). Sonuç:

```
GNOME Shell'in geç cevap verdiği anlar:  21:57:18.07  91 ms   ·   21:57:48.08  105 ms
```

Shell **her 30 saniyede bir yaklaşık 100 ms donuyordu**, oyundaki takılmalarla aynı anlarda.

### 4. Suçlu eklenti: eleme ve "sıra kayması" ipucu
Eklentilerin kodunda 30 saniyelik zamanlayıcılar arandı (`araclar/eklenti_tara.py`), ve şüpheliler tek tek kapatılıp yeniden ölçüldü:

- **glocalsend** kapatıldı → donmalar sürdü, ama saatin **:08 ve :38**'ine kaydı (önceden :18 ve :48'deydi). GNOME bir eklentiyi kapatınca **ondan sonra yüklenen eklentileri de yeniden başlatıyor.** Zamanlamanın kayması, suçlunun sıradaki eklentilerden biri olduğunu ve zamanlayıcısının sıfırlandığını gösterdi.
- **screen-time** kapatıldı (her 30 sn'de veri kaydediyor) → donmalar sürdü ve bu sefer **kaymadı**. Demek ki suçlu glocalsend ile screen-time arasında yüklenen eklentiydi.
- **public-ip-address** kapatıldı → **100 ms'lik donmalar tamamen kayboldu.**

**Sebep: [public-ip-address](https://extensions.gnome.org/) eklentisi.** Genel IP adresini en kısa **30 saniyede bir** (`refresh-rate`, izin verilen en düşük değer) sorguluyor ve her sorguda GNOME Shell yaklaşık 100 ms donuyordu. Windows'ta böyle bir eklenti olmadığı için orada takılma yoktu.

`teshis` ve `teshis --dene` komutları bu yöntemi otomatikleştiriyor. Araç suçluyu bu sistemde kendisi buldu:

```
80 ms üstü donma: önce 2, eklenti kapalıyken 0
✓ Suçlu bu: public-ip-address@theophilediot.github.io.
  Eklentiyi kullanmaya devam edip yalnızca oyunda kapatmak için: fedora-gnome-ets2 oyunda-kapat public-ip-address@theophilediot.github.io
```

**Çözüm:** Eklentiyi tamamen kapatmak yerine [yalnızca oyun açıkken kapatılıyor](#oyunda-takılma-yapan-eklentileri-kapatma). Masaüstünde açık, oyunda kapalı.

**Eklentinin neden takıldığına dair tahmin (ölçülmedi):** Eklenti her güncellemede iki HTTPS sorgusunun yanında VPN tünelini ve yerel IP'leri kontrol etmek için dört ayrı program da başlatıyor (`ip addr`, `ip route` ×2, `ip link`). Bunları GNOME Shell'in kendi süreci içinden başlatıyor. Shell büyük bir süreç olduğu için her yeni program başlatma onu bir anlığına durdurabiliyor.

Zamanlayıcı taraması tek başına yetmiyor: glocalsend ve screen-time'ın 30 saniyelik zamanlayıcısı olmasına rağmen ikisi de suçsuzdu. Her şüpheli **kapatılıp ölçülerek** doğrulanmalı. Geriye her 10 saniyede bir 26 ms'lik küçük gecikmeler kaldı. Aralığı day-progress eklentisinin 10 saniyelik zamanlayıcısına uyuyor, ama bu ölçülerek doğrulanmadı. En fazla tek bir kare kaybettiriyor ve hissedilmiyor.

---

## FPS sınırı ve 144 Hz

Takılmalar gittikten sonra kalan küçük dalgalanmanın sebebi, ekran kartının %200 ölçeklemede **%96 yükte**, yani sınırda çalışmasıydı. FPS 55-75 arasında gidip geliyordu.

- **VRR (G-Sync/FreeSync):** bu kurulumda yok. Monitör (ASUS VG249QE5A) 48 Hz alt sınır bildiriyor, ama NVIDIA HDMI üzerinden VRR'ı yalnızca HDMI 2.1 VRR ile açıyor. GNOME 50'de VRR deneysel bir özellik değil; destekleniyorsa Ayarlar → Ekranlar'da çıkıyor. Bu monitörde çıkmıyor.
- **Teori:** VRR yokken kare hızı yenileme hızına tam bölünmeli. 144 Hz için bu 72 ya da 48 demek; 60 bölünmüyor, çünkü kareler ekranda bazen 2, bazen 3 yenileme kalıyor.
- **Ölçüm:** Buna rağmen **60'a sabitlemek** en düzenli kare sürelerini verdi (aşağıdaki tabloda 4. test) ve oyunda en akıcı hissettiren buydu. Ekran kartında pay kalınca kareler eşit aralıklarla geliyor. 72'yi %200 ölçeklemede tutturmak mümkün değil, çünkü ortalama 65 FPS'ti.
- **Ayar:** varsayılan sınır 60. Sol Shift+F1 ile 72, 48 ve sınırsız denenebilir. Sınır MangoHud'da (`fps_limit_method=early`) uygulanıyor: kareleri oyunun kendi seçeneklerinden daha düzenli gönderiyor ve tuşla açılıp kapatılabiliyor. Oyunda dikey eşitleme açık kalmalı, yoksa ekranda yırtılma olur.

---

## Ölçüm sonuçları

Aynı yol, aynı ayarlar, 2 dakikalık MangoHud kayıtları (`./fedora-gnome-ets2 analiz`):

| Test | Ort. FPS | %1 en düşük | %0,1 en düşük | 25 ms'yi aşan kare | 50 ms'yi aşan kare | En uzun kare | Kare süresi sapması | Ardışık kare farkı | GPU yükü |
|---|---|---|---|---|---|---|---|---|---|
| 1. Başlangıç | 60,4 | 30,4 | 11,2 | 26 | 10 | 116 ms | 3,2 ms | 1,12 ms | %91 |
| 2. thermald kapalı | 64,2 | 30,9 | 11,7 | 28 | 11 | 123 ms | 3,1 ms | 1,06 ms | %94 |
| 3. public-ip-address kapalı | 65,2 | 41,4 | 24,8 | 15 | **0** | 48 ms | 1,9 ms | 0,93 ms | %96 |
| **4. + 60 FPS sınırı** | 59,4 | **47,6** | **39,4** | **2** | **0** | **38 ms** | **0,6 ms** | **0,16 ms** | %87 |

- **Ortalama FPS** neredeyse hiç değişmedi. Sorun hız değil düzensizlikti.
- **Akıcılığı belirleyen değerler** "%0,1 en düşük" (en kötü anlar) ve "ardışık kare farkı". Başlangıçtan son teste en kötü anlar 3,5 kat iyileşti, kareler arası fark 7 kat azaldı.

---

## Bilinen sorunlar

- **MangoHud 0.8.3-rc1 kayıt bitince oyunu kapatıyor.** Fedora 44'teki sürüm henüz kararlı değil (ön sürüm). Ekrandaki gösterge sorunsuz çalışıyor; yalnızca Shift+F2 kaydı bittiğinde oyun kapanıyor. Kayıt almadan önce oyunu kaydet. Alternatif olarak başlatma seçeneklerinde `mangohud` yerine `DXVK_HUD=fps,frametimes` kullanılabilir: kayıt almıyor ama ek bir program gerektirmiyor.
- **TruckersMP sürüm gecikmesi.** Yukarıya bak.
- **İlk sürüşlerde küçük takılmalar.** Gölgelendiriciler ilk kez görüldükleri yerde derleniyor. Oynadıkça önbelleğe giriyorlar ve takılmalar azalıyor.
- **GNOME + ArcMenu, kısayol dosyaları değişince çöküyor** (bu sistemde görülen, ETS2'den bağımsız bir sorun). ArcMenu'nun kullandığı gnome-menus kütüphanesi, bir `.desktop` dosyası değişirken menüyü yeniden okurken boş bir kayda takılıp GNOME Shell'i çökertebiliyor; oturum kapanıyor. Bu araç bir menü girişi yazdığı için (`truckersmp`), ArcMenu açıksa bu sırada oturum kapanabilir.

---

## Geri alma ve kaldırma

- **Steam ayarları:** `./fedora-gnome-ets2 geri-al`. Aracın ilk çalıştırılmasından önceki `config.vdf` ve `localconfig.vdf` yedeklerini geri yükler.
- **MangoHud ayarı:** `~/.config/MangoHud/ets2.conf`. Eski hâli `ets2.conf.yedek-*` dosyalarında.
- **TruckersMP:**
  ```bash
  pipx uninstall truckersmp-cli
  rm ~/.local/bin/truckersmp-ets2 ~/.local/share/applications/truckersmp-ets2.desktop
  rm -r ~/.local/share/truckersmp-cli   # TruckersMP'nin Proton klasörü; ortak profil bağlantı olduğu için profillerin silinmez
  ```
- **Oyunda eklenti kapatma:** `~/.config/gamemode.ini` içindeki `[custom]` satırlarını sil ve `~/.local/bin/oyun-eklentileri` ile `~/.config/oyun-eklentileri.conf` dosyalarını kaldır.

## Lisans

MIT
