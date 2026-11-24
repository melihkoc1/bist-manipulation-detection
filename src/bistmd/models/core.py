"""Karşılaştırılan modeller. Hepsi aynı arayüzü uygular: fit(X, y) → score(X) (yüksek = şüpheli).

0a  RuleScore      — Borsa gözetim kurallarına benzeyen eşik sayımı (VBTS benzeri)
0c  RuleScoreVWAP  — 0a + kapanış fiyatı oyunu (VWAP) kuralı
0b  SimpleScore    — getiri z-skoru × hacim oranı (akıl sağlığı kontrolü)
1   IForest        — gözetimsiz; etiket kullanılmaz
2   Supervised     — LightGBM; etiketsiz günler negatif sayılır
3a  PUWeighted     — Elkan–Noto (2008) ağırlıklı yeniden eğitim
3b  PUBagging      — Mordelet & Vert (2014) bagging PU
2b  LogisticSupervised — lojistik regresyon, etiketsiz = negatif (MEL-81)
3c  PULogistic     — PU bagging, taban öğrenici lojistik regresyon (MEL-81)

Not (tez için): Elkan–Noto'nun yalnızca olasılığı c'ye bölen temel hali sıralamayı
değiştirmez; sıralama metriklerinde gözetimli modelle aynı sonucu verir. Bu yüzden
sıralamayı değiştiren iki PU varyantı kullanılır.
"""

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Zaman içinde durağan olmayan (TL enflasyonu, veri başlangıcına bağlı) sütunlar modele girmez
EXCLUDE = {"ticker", "date", "log_mcap", "log_float_mcap", "log_value", "log_price", "days_listed"}

LGB_PARAMS = dict(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50,
                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                  verbose=-1, n_jobs=-1)


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in EXCLUDE and pd.api.types.is_numeric_dtype(df[c])
            and not c.startswith(("pos_", "ignore_", "case_", "tier_"))]


class RuleScore:
    """Kaç şüphe kuralının aynı anda sağlandığı (+ eşitlik bozmak için küçük getiri terimi)."""
    name = "0a_kural"
    RULES = {
        "excess_ret_20": 0.30, "value_ratio_5d_60": 3.0, "close_loc_5": 0.70,
        "limit_up_10": 2, "float_turnover_ratio_60": 3.0, "up_days_10": 7,
    }

    def fit(self, X, y=None):
        return self

    def score(self, X):
        s = sum((X[c] >= t).astype(float) for c, t in self.RULES.items())
        return s + 0.01 * np.tanh(X["ret_20_z"].fillna(0))


class RuleScoreVWAP(RuleScore):
    """0a + kapanış oyunu kuralı: son 10 günün ≥6'sında kapanış VWAP'ın %0,5+ üstünde.
    Eşik etiketlere bakılmadan, dağılımdan seçildi (günlerin ~%5,6'sı; diğer kurallar kadar seyrek)."""
    name = "0c_kural_vwap"
    RULES = {**RuleScore.RULES, "close_above_vwap_10": 6}


class SimpleScore:
    name = "0b_basit"

    def fit(self, X, y=None):
        return self

    def score(self, X):
        return X["ret_20_z"].clip(lower=0).fillna(0) * np.log1p(X["value_ratio_5d_60"].fillna(1))


class IForest:
    name = "1_iforest"

    def __init__(self, max_samples=200_000, seed=0):
        self.max_samples, self.seed = max_samples, seed

    def fit(self, X, y=None):
        self.cols = feature_columns(X)
        Xt = X[self.cols].fillna(X[self.cols].median())
        self.medians = Xt.median()
        self.model = IsolationForest(n_estimators=300, max_samples=min(self.max_samples, len(Xt)),
                                     random_state=self.seed, n_jobs=-1).fit(Xt)
        return self

    def score(self, X):
        return -self.model.decision_function(X[self.cols].fillna(self.medians))


class Supervised:
    name = "2_lightgbm"

    def __init__(self, seed=0):
        self.seed = seed

    def fit(self, X, y, sample_weight=None):
        self.cols = feature_columns(X)
        pos_rate = y.mean()
        self.model = lgb.LGBMClassifier(**LGB_PARAMS, random_state=self.seed,
                                        scale_pos_weight=(1 - pos_rate) / max(pos_rate, 1e-9))
        self.model.fit(X[self.cols], y, sample_weight=sample_weight)
        return self

    def score(self, X):
        return self.model.predict_proba(X[self.cols])[:, 1]


class PUWeighted:
    """Elkan & Noto (2008), 'ağırlıklı' varyant.

    1) g(x) = P(etiketli | x) modelini eğit; c = ortalama g(x), ayrılmış pozitiflerde.
    2) Her etiketsiz örnek için w = P(y=1 | x, etiketsiz) = (1-c)/c · g/(1-g).
    3) Etiketsiz örnekleri w ağırlıkla pozitif, (1-w) ağırlıkla negatif olarak çoğaltıp
       yeniden eğit. Böylece "muhtemelen yakalanmamış manipülasyon" günleri negatif
       muamelesi görmez.
    """
    name = "3a_pu_agirlikli"

    def __init__(self, holdout=0.2, seed=0):
        self.holdout, self.seed = holdout, seed

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        pos_idx = np.flatnonzero(y.to_numpy() == 1)
        held = rng.choice(pos_idx, size=max(1, int(len(pos_idx) * self.holdout)), replace=False)
        mask = np.ones(len(y), bool)
        mask[held] = False
        g = Supervised(self.seed).fit(X[mask], y[mask])
        # scale_pos_weight olasılıkları şişirir; c tahmini için dengesiz olmayan model gerekir
        g.model.set_params(scale_pos_weight=1.0)
        g.model.fit(X.loc[mask, g.cols], y[mask])
        gx = g.model.predict_proba(X[g.cols])[:, 1]
        self.c = float(np.clip(gx[held].mean(), 1e-4, 1.0))
        unl = y.to_numpy() == 0
        w = np.clip((1 - self.c) / self.c * gx / np.clip(1 - gx, 1e-6, None), 0, 1)
        Xu = X[unl]
        X2 = pd.concat([X[~unl], Xu, Xu], ignore_index=True)
        y2 = pd.Series(np.r_[np.ones((~unl).sum()), np.ones(unl.sum()), np.zeros(unl.sum())])
        sw = np.r_[np.ones((~unl).sum()), w[unl], 1 - w[unl]]
        self.model = Supervised(self.seed).fit(X2, y2, sample_weight=sw)
        return self

    def score(self, X):
        return self.model.score(X)


class PUBagging:
    """Mordelet & Vert (2014): her torbada tüm pozitifler + etiketsizlerden rastgele bir
    alt örneklem; skor = torba modellerinin ortalaması (eğitimde out-of-bag)."""
    name = "3b_pu_bagging"

    def __init__(self, n_bags=15, unl_ratio=20, seed=0):
        self.n_bags, self.unl_ratio, self.seed = n_bags, unl_ratio, seed

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        self.cols = feature_columns(X)
        pos = np.flatnonzero(y.to_numpy() == 1)
        unl = np.flatnonzero(y.to_numpy() == 0)
        size = min(len(unl), len(pos) * self.unl_ratio)
        self.models = []
        params = {**LGB_PARAMS, "n_estimators": 250}
        for b in range(self.n_bags):
            u = rng.choice(unl, size=size, replace=False)
            idx = np.r_[pos, u]
            m = lgb.LGBMClassifier(**params, random_state=self.seed + b)
            m.fit(X.iloc[idx][self.cols], np.r_[np.ones(len(pos)), np.zeros(size)])
            self.models.append(m)
        return self

    def score(self, X):
        return np.mean([m.predict_proba(X[self.cols])[:, 1] for m in self.models], axis=0)


class _LogReg:
    """Lojistik regresyon için ön işleme + model (MEL-81). Eksikler eğitim medyanıyla doldurulur,
    değerler eğitimdeki %1–%99 aralığına kırpılır, standartlaştırılır. Ayar yapılmaz (C = 1)."""

    def __init__(self, cols, balanced):
        self.cols, self.balanced = cols, balanced

    def fit(self, X, y):
        from sklearn.linear_model import LogisticRegression
        A = X[self.cols].to_numpy(dtype="float64")
        self.med = np.nanmedian(A, axis=0)
        A = np.where(np.isnan(A), self.med, A)
        self.lo, self.hi = np.percentile(A, 1, axis=0), np.percentile(A, 99, axis=0)
        A = np.clip(A, self.lo, self.hi)
        self.mu, self.sd = A.mean(0), A.std(0)
        self.sd[self.sd == 0] = 1.0
        self.model = LogisticRegression(C=1.0, max_iter=2000,
                                        class_weight="balanced" if self.balanced else None)
        self.model.fit((A - self.mu) / self.sd, np.asarray(y))
        return self

    def transform(self, X):
        A = X[self.cols].to_numpy(dtype="float64")
        A = np.clip(np.where(np.isnan(A), self.med, A), self.lo, self.hi)
        return (A - self.mu) / self.sd

    def decision(self, X):
        return self.model.decision_function(self.transform(X))


class LogisticSupervised:
    """2b: lojistik regresyon, etiketsiz günler negatif (2_lightgbm'in doğrusal karşılığı)."""
    name = "2b_lojistik"

    def fit(self, X, y):
        self.m = _LogReg(feature_columns(X), balanced=True).fit(X, y)
        return self

    def score(self, X):
        return self.m.decision(X)


class PULogistic(PUBagging):
    """3c: PU bagging kurgusu, taban öğrenici lojistik regresyon (3b'nin doğrusal karşılığı)."""
    name = "3c_pu_lojistik"

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        self.cols = feature_columns(X)
        pos = np.flatnonzero(y.to_numpy() == 1)
        unl = np.flatnonzero(y.to_numpy() == 0)
        size = min(len(unl), len(pos) * self.unl_ratio)
        self.models = []
        for _ in range(self.n_bags):
            idx = np.r_[pos, rng.choice(unl, size=size, replace=False)]
            self.models.append(_LogReg(self.cols, balanced=False).fit(
                X.iloc[idx], np.r_[np.ones(len(pos)), np.zeros(size)]))
        return self

    def score(self, X):
        return np.mean([m.decision(X) for m in self.models], axis=0)


class _PUForest(PUBagging):
    """PU bagging, taban öğrenici sklearn ormanı (MEL-83 deneyi). Eksikler eğitim medyanıyla doldurulur."""
    trees = 10

    def _forest(self, seed):
        raise NotImplementedError

    def fit(self, X, y):
        rng = np.random.default_rng(self.seed)
        self.cols = feature_columns(X)
        A = X[self.cols].to_numpy(dtype="float32")
        self.med = np.nanmedian(A, axis=0)
        A = np.where(np.isnan(A), self.med, A)
        pos = np.flatnonzero(y.to_numpy() == 1)
        unl = np.flatnonzero(y.to_numpy() == 0)
        size = min(len(unl), len(pos) * self.unl_ratio)
        self.models = []
        for b in range(self.n_bags):
            idx = np.r_[pos, rng.choice(unl, size=size, replace=False)]
            self.models.append(self._forest(self.seed + b).fit(A[idx], np.r_[np.ones(len(pos)), np.zeros(size)]))
        return self

    def score(self, X):
        A = X[self.cols].to_numpy(dtype="float32")
        A = np.where(np.isnan(A), self.med, A)
        return np.mean([m.predict_proba(A)[:, 1] for m in self.models], axis=0)


class PURandomForest(_PUForest):
    name = "3f_pu_rf"

    def _forest(self, seed):
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=self.trees, min_samples_leaf=50, max_features="sqrt",
                                      max_samples=0.3, n_jobs=-1, random_state=seed)


class PUExtraTrees(_PUForest):
    name = "3g_pu_et"

    def _forest(self, seed):
        from sklearn.ensemble import ExtraTreesClassifier
        return ExtraTreesClassifier(n_estimators=self.trees, min_samples_leaf=50, max_features="sqrt",
                                    n_jobs=-1, random_state=seed)


ALL_MODELS = [RuleScore, RuleScoreVWAP, SimpleScore, IForest, Supervised, PUWeighted, PUBagging,
              LogisticSupervised, PULogistic, PURandomForest, PUExtraTrees]
