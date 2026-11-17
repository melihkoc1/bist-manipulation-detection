# Canlı test protokolü (ileriye dönük değerlendirme)

Yazım: 17.11.2026, ilk haftalık liste kaydedilmeden önce. Linear: MEL-17.
Bu belge, sonuçlar görülmeden neyin nasıl ölçüleceğini sabitler. Sonradan değişiklik gerekirse
belgenin sonuna tarihli bir **ek** olarak yazılır; yukarıdaki maddeler silinmez.

## Neden?

Geriye dönük testler ne kadar dikkatli kurulsa da araştırmacının geleceği bir şekilde görmüş olma riski
taşır (ayar seçimi, gösterge seçimi, tekrarlanan denemeler). Canlı testte listeler, sonuç (SPK kararı)
henüz kimse tarafından bilinmezken kaydedilir ve sonradan değiştirilemez.

## Donmuş model

- Model: **Kural + PU** (ana model). Kural yarısı eğitim gerektirmez; PU yarısı (15 torbalı LightGBM,
  ana ayarlar) dondurma anına kadarki tüm veriyle ve o ana kadar açıklanmış tüm SPK vakalarıyla bir kez
  eğitildi (`scripts/live_freeze.py`).
- Kesim tarihleri, kod commit'i, gösterge listesi ve model dosyasının sha256 parmak izi:
  [model.json](model.json). Canlı test boyunca model, eşikler, gösterge kodu ve liste boyu (ilk 20)
  **değiştirilmez**.
- Doğrulama (kayıttan önce yapıldı): haftalık betiğin ürettiği göstergeler araştırma verisiyle birebir
  aynı; donmuş modelin listesi araştırmadaki dürüst 2026 modeliyle 3 örnek haftada sıra korelasyonu
  0,97–0,996, ilk 20'nin 17–19'u ortak.

## Haftalık kayıt

- Her hafta kapandıktan sonra `python scripts/live_week.py` çalıştırılır: fiyatlar İş Yatırım'dan
  indirilir, hafta donmuş modelle skorlanır, ilk 20 liste yerelde (`data/live/weeks/`) saklanır.
- Depoya yalnızca [kayit.csv](kayit.csv) satırı girer: hafta, kayıt zamanı, ilk 20 dosyasının sha256
  parmak izi, skorlanan hisse sayısı. **Hisse adları depoya veya internete konmaz.** Parmak izi, liste
  sonradan değişirse tutmaz; GitHub'a gönderilen commit'ler bağımsız bir zaman damgası sağlar.
- `python scripts/live_week.py --verify` kayıtlı tüm listelerin ve modelin parmak izlerini denetler.
- Bir hafta kaçırılırsa sonradan kaydedilir ve `gecikmeli = 1` olarak işaretlenir. Hiçbir hafta,
  içeriğine bakılarak atlanmaz veya silinmez.
- **Başlangıç:** model 17.11.2026'da donduruldu. 23.10–13.11.2026 haftaları (araştırma verisinin
  bittiği 16.10.2026 ile dondurma arası) aynı gün geriye doğru kaydedildi ve `gecikmeli` işaretli.
  Bu haftalarda hafta sonrası fiyatlar kayıt anında mevcuttu, ama model ve liste kuralı sabit olduğu
  için seçim yapılamaz; yine de duyarlılık analizinde bu haftalar çıkarılarak da raporlanır.

## Birincil sonuç: yeni SPK kararları

- **Ne zaman:** ilk değerlendirme Haziran 2027 (31.05.2027'ye kadar yayımlanan SPK bültenleri ve SPK
  API kayıtları). Sonra da güncellenebilir; her güncelleme tarihiyle raporlanır.
- **Vaka:** ilk SPK kararı dondurma tarihinden (17.11.2026) sonra olan ve işlem yasağı / suç duyurusu
  / idari para cezası içeren, araştırmadaki aynı kodla (`scripts/inventory.py`, `bistmd.labels`)
  çıkarılan vakalar. Manipülasyon dönemi araştırmadaki "kesin dönem" tanımıyla belirlenir; dönemi
  kaydedilmiş en az bir haftayla kesişen vakalar değerlendirmeye girer.
- **Ölçü:** yakalama@20 = bu vakalardan, dönemiyle kesişen kayıtlı haftaların en az birinde ilk 20'de
  yer alanların oranı. **Rastgele beklenti:** vaka başına 1 − Π(1 − 20 / o haftanın hisse sayısı);
  anlamlılık, vaka başına bu olasılıklarla Poisson-binom dağılımından (tek yönlü) hesaplanır.
- Beklenen vaka sayısı küçüktür. Geçmişte (2015+) ilk SPK kararlarının %63'ü manipülasyon döneminin
  bitişinden sonraki 6 ay, %79'u 12 ay içinde açıklandı. Sonuç vaka sayısıyla birlikte, güven aralığıyla
  ve "küçük örneklem" uyarısıyla raporlanır; 0 vaka da bir sonuçtur ve raporlanır.

## İkincil sonuçlar: olağan dışı hareket (erken ölçülebilir)

Her kayıtlı haftada ilk 20 ile aynı haftanın geri kalan hisseleri karşılaştırılır (hafta kümelemeli
bootstrap ile güven aralığı). Bunlar manipülasyon kanıtı **değildir**; listenin "olağan dışı hareket"
gösteren hisseleri seçip seçmediğini ölçer.

1. Haftayı izleyen 20 işlem gününde Borsa İstanbul'un istediği "olağan dışı fiyat ve miktar
   hareketi" açıklaması (KAP, araştırmadaki `unusual_move` sınıfı).
2. Haftayı izleyen 20 işlem gününde pay bazında devre kesici bildirimi (KAP, `circuit_breaker`).
3. Hafta kapanışından sonraki 60 işlem gününde kapanışa göre en büyük düşüş ≤ −%30 (sert çöküş).

## Yorum kuralları

- Listedeki bir hisse için "manipüle edildi" denmez. SPK kararı olmayan bir alarm "olağan dışı hareket"
  olarak tanımlanabilir; aklanmış veya "temiz" de denmez.
- Sonuçlar olumsuz çıksa da raporlanır.
