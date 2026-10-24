"""Arayüz metinleri (Türkçe / İngilizce). t("anahtar") seçili dilde metni döndürür."""

import streamlit as st

TEXT = {
    # Genel
    "app_title": ("BIST Manipülasyon Tespiti", "BIST Manipulation Detection"),
    "lang": ("Dil", "Language"),
    "disclaimer": (
        "Skorlar istatistiksel anomali sinyalidir, **suçlama değildir**. SPK vakaları kamuya açık SPK "
        "kararlarına dayanır. Yatırım tavsiyesi değildir.",
        "Scores are statistical anomaly signals, **not accusations**. SPK cases are based on public "
        "regulator decisions. Not investment advice.",
    ),
    "nav_tm": ("Zaman makinesi", "Time machine"),
    "nav_stock": ("Hisse detayı", "Stock detail"),
    "nav_results": ("Sonuçlar", "Results"),
    "nav_method": ("Yöntem", "Method"),
    "model": ("Model", "Model"),
    "missing_data": (
        "Gerekli veri bulunamadı: {path}. Önce README'deki 'Projeyi baştan çalıştırma' adımlarını uygulayın.",
        "Required data not found: {path}. Run the steps under 'Reproducing' in the README first.",
    ),

    # Zaman makinesi
    "tm_title": ("Zaman makinesi", "Time machine"),
    "tm_caption": (
        "Geçmişte herhangi bir hafta seçin: sistemin **o hafta** üreteceği en şüpheli hisse listesi. "
        "Model her yıl yalnızca o yıldan önce bilinen veri ve SPK kararlarıyla eğitildi; liste geleceği görmez. "
        "SPK sütunu ise **sonradan** ne olduğunu gösterir.",
        "Pick any past week: the most suspicious stocks the system would have listed **that week**. "
        "Each year's model was trained only on data and SPK decisions known before that year; the list does "
        "not see the future. The SPK column shows what happened **afterwards**.",
    ),
    "week": ("Hafta (cuma)", "Week (Friday)"),
    "examples": ("Örnek haftalar", "Example weeks"),
    "list_size": ("Liste uzunluğu", "List length"),
    "col_rank": ("Sıra", "Rank"),
    "col_ticker": ("Hisse", "Ticker"),
    "col_name": ("Şirket", "Company"),
    "col_score": ("Şüphe yüzdeliği", "Suspicion percentile"),
    "col_rules": ("Tetiklenen kurallar (o hafta)", "Rules triggered (that week)"),
    "col_spk": ("Sonradan SPK", "SPK afterwards"),
    "spk_in_period": ("SPK manipülasyon dönemi · ilk karar {days} gün sonra",
                      "SPK manipulation period · first decision {days} days later"),
    "spk_in_period_before": ("SPK manipülasyon dönemi · karar önceden açıklanmıştı",
                             "SPK manipulation period · decision already published"),
    "spk_later": ("SPK kararı {days} gün sonra (dönem yazmıyor)",
                  "SPK decision {days} days later (period not stated)"),
    "m_in_period": ("SPK manipülasyon dönemindeki hisse", "Stocks inside an SPK manipulation period"),
    "m_in_period_help": (
        "Listedeki hisselerden kaçı, SPK'nın sonradan kararında belirttiği manipülasyon döneminin içindeydi. "
        "Rastgele beklenti: aynı hafta rastgele seçilen aynı sayıda hissede beklenen sayı.",
        "How many listed stocks were inside a manipulation period that SPK later named in a decision. "
        "Random expectation: the expected number for the same number of randomly picked stocks that week.",
    ),
    "m_random": ("rastgele beklenti {x}", "random expectation {x}"),
    "m_stocks": ("O hafta puanlanan hisse", "Stocks scored that week"),
    "tm_click": ("Bir satıra tıklayınca hissenin detay sayfası açılır.",
                 "Click a row to open the stock's detail page."),
    "tm_note": (
        "Not: Listedeki SPK bağlantısı olmayan hisseler masum anlamına gelmez, suçlu anlamına da gelmez; "
        "sistem bir önceliklendirme aracıdır.",
        "Note: stocks without an SPK link are not proven innocent, nor guilty; the system is a triage tool.",
    ),

    # Hisse detayı
    "sd_title": ("Hisse detayı", "Stock detail"),
    "sd_pick": ("Hisse", "Stock"),
    "sd_range": ("Tarih aralığı", "Date range"),
    "sd_price": ("Fiyat (düzeltilmiş, TL)", "Price (adjusted, TRY)"),
    "sd_volume": ("Hacim (mn TL)", "Volume (TRY mn)"),
    "sd_rank": ("Haftalık sıra", "Weekly rank"),
    "sd_top20": ("ilk 20 (alarm)", "top 20 (alarm)"),
    "sd_period": ("SPK manipülasyon dönemi", "SPK manipulation period"),
    "sd_decision": ("SPK kararı", "SPK decision"),
    "sd_focus": ("Seçilen hafta", "Selected week"),
    "sd_best": ("En iyi haftalık sıra", "Best weekly rank"),
    "sd_alarm_weeks": ("İlk 20'de geçen hafta", "Weeks in top 20"),
    "sd_n_decisions": ("SPK kararı (tüm dönem)", "SPK decisions (all time)"),
    "sd_decisions": ("SPK kararları", "SPK decisions"),
    "sd_no_decisions": ("Bu hisse hakkında SPK kararı yok.", "No SPK decisions for this stock."),
    "sd_kap": ("KAP bildirimleri (seçili aralık)", "KAP disclosures (selected range)"),
    "sd_kap_search": ("Bildirimlerde ara", "Search disclosures"),
    "col_date": ("Tarih", "Date"),
    "col_type": ("Karar türü", "Decision type"),
    "col_period": ("Belirtilen dönem", "Stated period"),
    "col_ref": ("Bülten / karar no", "Bulletin / decision no"),
    "col_subject": ("Konu", "Subject"),
    "col_summary": ("Özet", "Summary"),

    # Sonuçlar
    "rs_title": ("Sonuçlar", "Results"),
    "rs_caption": (
        "Dürüst değerlendirme: her yıl, o yıldan önce bilinen veriyle eğitilen modelle puanlandı. "
        "Vakalar: SPK'nın kararında manipülasyon dönemini yazdığı vakalar.",
        "Honest evaluation: each year scored by a model trained on data known before that year. "
        "Cases: those where SPK's decision states the manipulation period.",
    ),
    "rs_period": ("Dönem", "Period"),
    "rs_cases": ("{n} vaka", "{n} cases"),
    "rs_caught": ("Haftalık ilk 20'de yakalanan vaka", "Cases caught in weekly top 20"),
    "rs_caught_help": ("En iyi model (kural + PU). Parantez: rastgele sıralamada beklenen.",
                       "Best model (rules + PU). In brackets: expected under random ranking."),
    "rs_random": ("rastgele: {x}", "random: {x}"),
    "rs_auc": ("AUC (0,5 = rastgele)", "AUC (0.5 = random)"),
    "rs_before_peak": ("Fiyat zirvesinden önce yakalanan", "Caught before the price peak"),
    "rs_lead": ("İlk alarm (dönem başından)", "First alarm (from period start)"),
    "rs_lead_val": ("medyan {d} gün", "median {d} days"),
    "rs_table": ("Modeller", "Models"),
    "col_model": ("Model", "Model"),
    "col_auc": ("AUC [%95 GA]", "AUC [95% CI]"),
    "col_rec20": ("İlk 20'de yakalama", "Caught in top 20"),
    "col_rnd20": ("Rastgele", "Random"),
    "col_lift20": ("Rastgeleye oran", "× random"),
    "col_peak": ("Zirveden önce", "Before peak"),
    "col_prec10": ("İlk 10 isabeti (× rastgele)", "Top-10 precision (× random)"),
    "rs_chart": ("Yakalama oranı ve rastgele beklenti", "Catch rate vs random expectation"),
    "rs_series_model": ("Model", "Model"),
    "rs_series_random": ("Rastgele beklenti", "Random expectation"),
    "rs_spk": ("SPK'ya göre zaman", "Timing vs the regulator"),
    "rs_spk_text": (
        "Yakalanan {n} vakada (2017–2026) alarm, SPK'nın **ilk** kararından (çoğu zaman işlem yasağı) "
        "%{pct_first} oranında önce geldi; medyan **{d_first} gün** önce. İlk **ceza veya suç duyurusundan** "
        "medyan **{d_sanction} gün** önce.",
        "For the {n} caught cases (2017–2026), the alarm came before SPK's **first** action (often a trading "
        "ban) in {pct_first}% of cases, a median **{d_first} days** earlier; and a median **{d_sanction} days** "
        "before the first **fine or criminal complaint**.",
    ),
    "rs_questions": ("Tez soruları", "Thesis questions"),
    "q1": ("**1. Günlük veriyle erken tespit mümkün mü?** Evet — rastgelenin yaklaşık 3 katı, çoğunlukla fiyat zirvesinden önce.",
           "**1. Can manipulation be detected early from daily data?** Yes — about 3× random, mostly before the price peak."),
    "q2": ("**2. PU öğrenme daha iyi mi?** Kısmen evet — gözetimli öğrenmeden anlamlı biçimde iyi; kurallarla birleşince en iyi model.",
           "**2. Is PU learning better?** Partly — significantly better than supervised learning; best when combined with rules."),
    "q3": ("**3. 'Habersiz hareket' özellikleri işe yarıyor mu?** Hayır — anlamlı katkı yok.",
           "**3. Do 'moves without news' features help?** No — no significant gain."),
    "rs_cases_title": ("Vaka çalışmaları", "Case studies"),
    "rs_limits": ("Sınırlılıklar", "Limitations"),
    "limits": (
        "- Yalnızca kararında dönem yazan vakalar değerlendirilebiliyor (413 ana vakanın 184'ü).\n"
        "- Yavaş, sessiz ya da piyasa geneliyle birlikte yükselen manipülasyonlar günlük veride normal görünüyor; "
        "bunlar için aracı kurum (AKD) verisi gerekir.\n"
        "- Listedeki pek çok hisse SPK vakası değil: sistem hüküm değil, önceliklendirme aracıdır.",
        "- Only cases whose decision states the period can be evaluated (184 of 413 core cases).\n"
        "- Slow, quiet manipulations, or ones riding a market-wide rally, look normal in daily data; "
        "these need broker-level (AKD) data.\n"
        "- Many listed stocks are not SPK cases: the system is a triage tool, not a verdict.",
    ),

    # Yöntem
    "mt_title": ("Yöntem", "Method"),
    "mt_intro": (
        "Sistem dört adımda çalışır: SPK kararlarından etiket çıkarma, günlük veriden özellik üretme, "
        "modelleme ve geleceği görmeyen bir protokolle değerlendirme.",
        "The system works in four steps: extracting labels from SPK decisions, building features from "
        "daily data, modelling, and evaluation with a look-ahead-free protocol.",
    ),
    "mt_labels_t": ("1. Etiketler: SPK kararları", "1. Labels: SPK decisions"),
    "mt_labels": (
        "~1.000 haftalık SPK bülteni (2009–2026) ve SPK yaptırımlar API'si okunur. 2012 öncesi bültenlerde "
        "hisse kodu yerine şirket unvanı geçer; unvanlar kodlara eşlenir. Her karardan hisse, karar türü ve "
        "(varsa) manipülasyon dönemi çıkarılır; aynı olaya ait kararlar tek vakada birleştirilir: **657 vaka**, "
        "elle kontrolde %94 isabet. İçerden öğrenenlerin ticareti ve yalnızca bildirim ihlalleri kapsam dışı.",
        "~1,000 weekly SPK bulletins (2009–2026) and the SPK sanctions API are parsed. Pre-2012 bulletins name "
        "companies by legal title rather than ticker; titles are matched to tickers. Each decision yields the "
        "stock, decision type and (if stated) manipulation period; decisions about one episode are merged into "
        "a case: **657 cases**, 94% precision on a manual check. Insider trading and disclosure-only cases are excluded.",
    ),
    "mt_features_t": ("2. Özellikler: günlük veri", "2. Features: daily data"),
    "mt_features": (
        "Hisse × gün başına ~60 özellik: endeks üstü getiri ve z-skorları, hissenin kendi geçmişine göre hacim "
        "ve halka açık kısma göre devir hızı, tavan serileri, yükselen gün sayısı, kapanışın gün içi konumu, "
        "kapanış/VWAP. KAP bildirimleri içeriğe göre sınıflandırılır (%93 doğruluk). Her özellik yalnızca o güne "
        "kadarki veriyi kullanır; bu birim testlerle doğrulanır.",
        "~60 features per stock-day: excess returns and z-scores, volume vs the stock's own history, free-float "
        "turnover, limit-up streaks, up-day counts, close location, close vs VWAP. KAP disclosures are classified "
        "by content (93% accuracy). Every feature uses only data up to that day, verified by unit tests.",
    ),
    "mt_models_t": ("3. Modeller", "3. Models"),
    "mt_models": (
        "| Model | Fikir |\n|---|---|\n"
        "| Kurallar | Borsa gözetimi tarzı 6 eşik: kaçı aynı anda sağlanıyor? |\n"
        "| Isolation Forest | Etiketsiz: alışılmadık davranışı bul |\n"
        "| LightGBM | Gözetimli: etiketsiz günleri 'temiz' say |\n"
        "| PU öğrenme | Etiketsiz günler 'temiz' değil, 'bilinmiyor' (Elkan–Noto, Mordelet–Vert) |\n"
        "| **Kural + PU** | İki sıralamanın eşit ağırlıklı ortalaması — en iyi model |",
        "| Model | Idea |\n|---|---|\n"
        "| Rules | 6 surveillance-style thresholds: how many hold at once? |\n"
        "| Isolation Forest | Unsupervised: find unusual behaviour |\n"
        "| LightGBM | Supervised: treat unlabeled days as clean |\n"
        "| PU learning | Unlabeled days are 'unknown', not clean (Elkan–Noto, Mordelet–Vert) |\n"
        "| **Rules + PU** | Equal-weight average of both rankings — best model |",
    ),
    "mt_eval_t": ("4. Dürüst değerlendirme", "4. Honest evaluation"),
    "mt_eval": (
        "- **Geleceği görmeme:** Modeller her yıl yeniden eğitilir ve yalnızca o yıldan önce **yayımlanmış** "
        "SPK kararlarını bilir (SPK vakaları çoğu zaman 1–2 yıl sonra açıklar).\n"
        "- **Gerçekçi senaryo:** Bir analist her hafta ~550 hisseden en şüpheli 20'sine bakarsa hangi vakaları yakalar?\n"
        "- **Rastgele taban:** Her vaka için şans eseri yakalanma olasılığı hesaplanır: "
        "1 − Π(1 − k/Nₜ). Uzun vakalar rastgele seçimle bile kolay \"yakalanır\"; sonuçlar buna göre okunur.\n"
        "- **İstatistik:** Güven aralıkları vaka bazlı bootstrap ile; modeller aynı vakalar üzerinde eşleştirilmiş testle karşılaştırılır.",
        "- **No look-ahead:** models are retrained yearly and only know SPK decisions **published** before that "
        "year (SPK often announces cases 1–2 years later).\n"
        "- **Realistic scenario:** if an analyst checked the 20 most suspicious of ~550 stocks every week, which cases would they catch?\n"
        "- **Random baseline:** each case's chance of being caught by luck is computed: 1 − Π(1 − k/Nₜ). "
        "Long cases are easy to 'catch' at random; results are read against this.\n"
        "- **Statistics:** confidence intervals by case-level bootstrap; models compared with paired tests on the same cases.",
    ),
    "mt_lesson_t": ("Önce yanlış yaptığımız", "What we got wrong first"),
    "mt_lesson": (
        "İlk sürüm \"vakaların %40–47'si yakalandı\" diyordu. Rastgele taban hesaplanınca bunun şanstan iyi "
        "olmadığı görüldü; sonuç geri çekildi ve değerlendirme baştan kuruldu. Bugünkü sonuçlar bu dersin ürünü.",
        "The first version reported \"40–47% of cases caught\". Once the random baseline was computed, that "
        "turned out to be no better than chance; the result was retracted and the evaluation rebuilt. "
        "Today's results are the product of that lesson.",
    ),
    "flow_spk": ("SPK bültenleri\n2009–2026", "SPK bulletins\n2009–2026"),
    "flow_prices": ("Günlük fiyatlar\n(işlemden kalkanlar dahil)", "Daily prices\n(incl. delisted)"),
    "flow_kap": ("KAP bildirimleri\n~775 bin", "KAP disclosures\n~775k"),
    "flow_labels": ("Etiketler\n657 vaka", "Labels\n657 cases"),
    "flow_features": ("~60 özellik\nhisse × gün", "~60 features\nstock × day"),
    "flow_models": ("Kurallar · IForest\nLightGBM · PU", "Rules · IForest\nLightGBM · PU"),
    "flow_rank": ("Haftalık sıralama\n~550 hisse", "Weekly ranking\n~550 stocks"),
    "flow_eval": ("Rastgeleye karşı\ndeğerlendirme", "Evaluation\nvs random"),
}

RULES = {
    "excess_ret_20": ("20 günde endeksin ≥%30 üstü getiri", "20-day return ≥30% above index"),
    "value_ratio_5d_60": ("5 günlük hacim normalin ≥3 katı", "5-day volume ≥3× normal"),
    "close_loc_5": ("Kapanışlar günün tepesine yakın", "Closes near the daily high"),
    "limit_up_10": ("Son 10 günde ≥2 tavan", "≥2 limit-up days in last 10"),
    "float_turnover_ratio_60": ("Halka açık kısımda devir ≥3 kat", "Free-float turnover ≥3× normal"),
    "up_days_10": ("Son 10 günün ≥7'si yükseliş", "≥7 up days in last 10"),
}

MODELS = {
    "random": ("Rastgele", "Random"),
    "0a_kural": ("Kurallar", "Rules"),
    "1_iforest": ("Isolation Forest", "Isolation Forest"),
    "2_lightgbm": ("LightGBM (gözetimli)", "LightGBM (supervised)"),
    "3a_pu_agirlikli": ("PU öğrenme (ağırlıklı)", "PU learning (weighted)"),
    "3b_pu_bagging": ("PU öğrenme (bagging)", "PU learning (bagging)"),
    "4_kural_pu": ("Kural + PU (en iyi)", "Rules + PU (best)"),
}

DECISION_TYPES = {
    "suc_duyurusu": ("Suç duyurusu", "Criminal complaint"),
    "idari_para_cezasi": ("İdari para cezası", "Administrative fine"),
    "islem_yasagi": ("İşlem yasağı", "Trading ban"),
    "diger_tedbir": ("Tedbir", "Precautionary measure"),
    "piyasa_tedbiri": ("Piyasa tedbiri", "Market measure"),
}

CASES = {
    "IZFAS-0": (
        "**Klasik pompala-boşalt.** Fiyat 3 ayda 2 katından fazla arttı. Sistem dönemin 45. gününde, yükselişin "
        "%59'u henüz gerçekleşmemişken alarm verdi ve hisseyi haftanın 1 numarası yaptı. SPK işlem yasağından "
        "sonra fiyat %87 düştü.",
        "**Textbook pump-and-dump.** The price more than doubled in 3 months. The system alarmed on day 45, "
        "before 59% of the rise, and ranked it #1 of the week. After SPK's trading ban the price fell 87%.",
    ),
    "SANEL-0": (
        "**Erken uyarı.** Kısa, hacim ağırlıklı bir vaka. Alarm, SPK'nın ilk kararından 202 gün, cezadan 551 gün önce geldi.",
        "**Early warning.** A short, volume-driven case. The alarm came 202 days before SPK's first decision and 551 days before the fine.",
    ),
    "KGYO-0": (
        "**Zor dönemde başarı.** 2022'deki genel yükselişte hisse 5 kat yükseldi; sistem, yükselişin %85'i "
        "gerçekleşmeden uyardı.",
        "**Success in a hard period.** During the 2022 market rally the stock rose 5×; the system warned before 85% of the rise.",
    ),
    "KONYA-0": (
        "**Kaçırıldı.** Bütün piyasa yükselirken yavaş ve istikrarlı bir yükseliş; diğer hisselerden ayrışmadı (en iyi sıra 47).",
        "**Missed.** A slow, steady rise while the whole market rallied; it did not stand out (best rank 47).",
    ),
    "KUYAS-0": (
        "**Kaçırıldı.** Ölçülü, 'sessiz' bir manipülasyon: tavan yok, hacim yalnızca ~2 kat. Tespit için işlem "
        "tarafı verisi (AKD) gerekir.",
        "**Missed.** A measured, 'quiet' manipulation: no limit-ups, volume only ~2×. Detecting it needs trade-side (AKD) data.",
    ),
}


def lang_index() -> int:
    return 1 if st.session_state.get("lang", "Türkçe") == "English" else 0


def t(key: str, **kw) -> str:
    s = TEXT[key][lang_index()]
    return s.format(**kw) if kw else s


def label(table: dict, key: str) -> str:
    v = table.get(key)
    return v[lang_index()] if v else key


def pct(x: float) -> str:
    """Oranı yüzde olarak yazar: Türkçede %67, İngilizcede 67%."""
    v = f"{100 * x:.0f}"
    return f"%{v}" if lang_index() == 0 else f"{v}%"
