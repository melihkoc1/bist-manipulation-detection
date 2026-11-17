"""Canlı test (MEL-17): PU modelini bir kez eğitip dondurur.

Model, ana değerlendirmedeki PU bagging ile aynı ayarlarda (15 torba, unl_ratio 20, tohum 0) ve
o güne kadarki tüm veriyle eğitilir. Etiket: dondurma anında SPK'nın açıklamış olduğu tüm vakalar.
Kural yarısı (0a_kural) eğitim gerektirmez. Canlı testte bu model bir daha DEĞİŞTİRİLMEZ.

Kullanım: python scripts/live_freeze.py
Çıktı:  data/live/model/pu_bagging.pkl (gitignore)
        docs/canli_test/model.json (depoda: kesim tarihleri, commit, model sha256)
"""

import hashlib
import json
import pickle
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from run_experiment import load, training_target  # noqa: E402
from score_v2 import WINDOW, prepare  # noqa: E402

from bistmd.models.core import LGB_PARAMS, PUBagging, RuleScore  # noqa: E402
from bistmd.paths import INTERIM  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = INTERIM.parent / "live" / "model"
MODEL_PATH = MODEL_DIR / "pu_bagging.pkl"
MANIFEST = ROOT / "docs" / "canli_test" / "model.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if MODEL_PATH.exists() or MANIFEST.exists():
        sys.exit("Model zaten dondurulmuş; canlı test boyunca yeniden eğitilmez.")
    t0 = time.time()
    df, cases = load(WINDOW)
    df = prepare(df, "none")
    data_end = df["date"].max()
    label_cutoff = cases["first_decision"].max()
    y = training_target(df, cases, WINDOW, False, label_cutoff)
    train = df[f"ignore_{WINDOW}m"].fillna(0) == 0
    model = PUBagging().fit(df.loc[train], y[train])
    print(f"eğitim: {int(train.sum()):,} satır, pozitif {int(y[train].sum()):,} ({time.time() - t0:.0f}s)")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as fh:
        pickle.dump(model, fh)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    manifest = {
        "dondurma_zamani_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kod_commit": commit,
        "veri_son_gun": f"{data_end:%Y-%m-%d}",
        "etiket_kesimi_son_spk_karari": f"{label_cutoff:%Y-%m-%d}",
        "egitim_satir": int(train.sum()),
        "egitim_pozitif_satir": int(y[train].sum()),
        "bilinen_vaka": int(cases.loc[cases["first_decision"] <= label_cutoff, "case_id"].nunique()),
        "model": "Kural + PU: 0a_kural ve 3b_pu_bagging haftalık yüzdeliklerinin ortalaması",
        "pu_ayarlari": {"n_bags": model.n_bags, "unl_ratio": model.unl_ratio, "seed": model.seed,
                        "lgb": {**LGB_PARAMS, "n_estimators": 250}},
        "kural_esikleri": RuleScore.RULES,
        "ozellikler": model.cols,
        "model_sha256": sha256(MODEL_PATH),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"donduruldu: {MODEL_PATH} sha256={manifest['model_sha256'][:12]}… → {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
