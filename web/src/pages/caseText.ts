// Vaka metinleri: docs/vaka_calismalari.md'deki bulguların kısa hâli (TR, EN).
type T = [string, string];
export interface CaseText { title: T; card: T; saw: T[]; lesson: T; caution?: T }

export const CASE_TEXT: Record<string, CaseText> = {
  "IZFAS-0": {
    title: ["Klasik pompala-boşalt", "Textbook pump-and-dump"],
    card: ["Fiyat 3 ayda 2 katından fazla arttı; alarm yükselişin %59'u henüz gerçekleşmemişken geldi.", "The price more than doubled in 3 months; the alarm came before 59% of the rise."],
    saw: [
      ["Hisse Haziran'da haftalık listede 1. sıraya çıktı.", "It reached #1 on the weekly list in June."],
    ],
    lesson: ["Hacim patlaması ile kesintisiz yükseliş birlikte görüldüğünde sinyal güçleniyor. Alarm, SPK'nın ilk kararından (işlem yasağı) 55 gün, ilk cezadan 230 gün önce geldi.",
             "A volume surge together with a steady rise makes the signal strong. The alarm came 55 days before SPK's first decision (a trading ban) and 230 days before the first sanction."],
    caution: ["Sistem aynı hisseyi Aralık 2017'de de listeye almıştı. O dönem SPK kararlarında geçmiyor: ya yanlış alarm ya da SPK'nın incelemediği bir hareket.",
              "The system had also listed this stock in December 2017. That period is not in any SPK decision: either a false alarm or a move SPK did not pursue."],
  },
  "SANEL-0": {
    title: ["Kısa, hacim ağırlıklı bir vaka", "Short, volume-driven case"],
    card: ["İki aylık bir vaka; alarm SPK'nın ilk tedbirinden 6,5 ay önce geldi.", "A two-month case; the alarm came 6.5 months before SPK's first measure."],
    saw: [
      ["Mayıs 2019'da haftalık listede 1. sıraya çıktı.", "It reached #1 on the weekly list in May 2019."],
    ],
    lesson: ["Kısa vakaları rastgele bir listenin yakalama olasılığı düşüktür (%41). Burada sistemin uyarısı, SPK'nın ilk tedbirinden 202 gün, cezadan 551 gün önce geliyor.",
             "Short cases are hard to hit by chance (41%). Here the warning came 202 days before SPK's first measure and 551 days before the fine."],
  },
  "KGYO-0": {
    title: ["Zor dönemde erken uyarı", "Early warning in a hard period"],
    card: ["2022'nin genel yükselişinde hisse 5 kat arttı; sistem yükselişin %85'inden önce uyardı.", "During the 2022 market rally the stock rose 5×; the system warned before 85% of the rise."],
    saw: [
      ["Temmuz 2022'de haftalık listede 2. sıraya çıktı.", "It reached #2 on the weekly list in July 2022."],
    ],
    lesson: ["Pek çok hissenin birlikte yükseldiği bir yılda bile ani ayrışma yakalandı. Ancak Ağustos–Ekim arasında yükseliş sürerken sıra 50–400'e düştü: sistem en çok başlangıçtaki ani değişimi görüyor.",
             "Even in a year when many stocks rose together, the sudden break-out was caught. But from August to October, while the rise continued, the rank fell to 50–400: the system mainly sees the initial sudden change."],
  },
  "KONYA-0": {
    title: ["Piyasayla birlikte yükseliş", "Rising with the market"],
    card: ["Bütün piyasa yükselirken yavaş ve istikrarlı bir yükseliş; en iyi sıra 47.", "A slow, steady rise while the whole market rallied; best rank 47."],
    saw: [
      ["BIST 100 de 20 günde %23'e varan oranda yükseldi; hissenin endeks üstü getirisi ortalama %16'da kaldı (kural eşiği %30).", "The BIST 100 itself rose up to 23% in 20 days; the stock's excess return averaged 16% (rule threshold 30%)."],
      ["Hacim kendi geçmişine göre ortalama 2,3 kat arttı: ani patlama değil, kademeli artış.", "Volume averaged 2.3× its own history: a gradual increase, not a sudden surge."],
      ["Tavan serisi yok, kapanışlar günün tepesinde değil.", "No limit-up streak; closes not near the daily high."],
    ],
    lesson: ["Genel bir yükseliş döneminde, yavaş ve istikrarlı yapılan manipülasyon günlük fiyat-hacim verisinde diğer hisselerden ayrışmıyor.",
             "In a market-wide rally, a slow and steady manipulation does not stand out from other stocks in daily price-volume data."],
  },
  "KUYAS-0": {
    title: ["Sessiz manipülasyon", "A quiet manipulation"],
    card: ["Ölçülü bir hareket: tavan yok, hacim yalnızca ~2 kat; en iyi sıra 70.", "A measured move: no limit-ups, volume only ~2×; best rank 70."],
    saw: [
      ["20 günlük getiri en fazla %34; hiç tavan yok.", "20-day return at most 34%; no limit-ups."],
      ["Hacim normalin en fazla 3,6 katı, ortalama 2 katı.", "Volume at most 3.6× normal, 2× on average."],
      ["Kâğıt üzerinde \"biraz hareketli bir hisse\" gibi görünüyor.", "On paper it looks like \"a somewhat active stock\"."],
    ],
    lesson: ["SPK'nın tespiti muhtemelen hesap bazlı işlem verisine (kimin kime sattığı) dayanıyor. Bu tür vakalar için aracı kurum dağılımı (AKD) gibi işlem tarafı verisi gerekir; projenin sonraki adımı bu.",
             "SPK's finding likely relied on account-level trade data (who sold to whom). Cases like this need trade-side data such as broker distribution (AKD), the project's next step."],
  },
};
