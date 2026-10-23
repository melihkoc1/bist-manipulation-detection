# Detecting Stock Manipulation on Borsa Istanbul

[![tests](https://github.com/melihkoc1/bist-manipulation-detection/actions/workflows/tests.yml/badge.svg)](https://github.com/melihkoc1/bist-manipulation-detection/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**English** | [Türkçe](README.tr.md)

An early-warning system for **pump-and-dump manipulation** in Borsa Istanbul (BIST) stocks,
built from daily market data, company disclosures (KAP) and 17 years of regulator decisions
(SPK). Every week it ranks ~550 stocks by how suspicious their trading looks. It is evaluated
against real enforcement cases with a strict, look-ahead-free protocol.

*Undergraduate thesis project · Melih Erdem Koçoğlu · 2026–2027*

> Scores are **statistical anomaly signals, not accusations**. Companies named in this
> repository appear only because the Capital Markets Board of Turkey (SPK) published a
> decision about trading in their shares. Nothing here is investment advice.

## Key results

The evaluation covers 125 SPK cases from 2017–2026 with a known manipulation period. In the
"honest" setup, each year is scored by a model trained only on data and SPK decisions
available before that year:

| Model | AUC | Cases caught in weekly top 20 | Caught before price peak | Top-10 precision vs random |
|---|---|---|---|---|
| Random ranking | 0.50 | 22% (expected 23%) | 21% | 1.0× |
| Surveillance-style rules | 0.81 | 65% | 64% | 2.4× |
| PU learning (bagging) | 0.83 | 62% | 60% | 3.5× |
| **Rules + PU ensemble** | **0.85** | **67%** | **66%** | **3.4×** |

- **Detection is about 3× better than random.** The first alarm comes a median of 8 days after
  the manipulation starts.
- **Lead over the regulator.** For caught cases, the alarm precedes SPK's first action
  (often a trading ban) in 94% of cases, by a median of 28 days. It precedes the first fine or
  criminal complaint by a median of **13 months**.
- **PU learning helps.** It significantly beats ordinary supervised learning (AUC +0.03,
  paired case bootstrap). Combined with rules, it beats both rules and PU alone.
- **Extending the history helps.** Adding older regulator bulletins (2009–2015) grew the label
  set from 335 to 413 cases. This significantly improved the ML models (LightGBM AUC +0.05),
  which confirms they were limited by the number of labels, not by model capacity.
- **Older years.** Including 2012–2016 (184 cases in total), the ensemble catches 71% of cases,
  against 29% for random.

Full tables: [docs/sonuclar_v2.md](docs/sonuclar_v2.md) · interpretation: [docs/yorum_v2.md](docs/yorum_v2.md)
(both in Turkish).

### Example: a textbook pump-and-dump (IZFAS, 2018)

![IZFAS case](docs/figures/vaka_IZFAS-0.png)

**Price.** The price more than doubled in three months. After SPK imposed a trading ban, the
stock lost 87% of its value.

**What the system saw.** The ensemble flagged the stock on day 45 of the manipulation, before
59% of the rise, and ranked it #1 of ~550 stocks in June. The rules that fired that week:
- 34% return above the index over 20 days
- free-float turnover 3.3× its normal level
- 8 up days out of 10

More cases are covered in [docs/vaka_calismalari.md](docs/vaka_calismalari.md), including two
the system missed and why.

## How it works

```mermaid
flowchart LR
    A[SPK bulletins 2009–2026<br/>+ sanctions API] --> L[Labels: 657 cases<br/>manipulation periods]
    B[Daily prices<br/>incl. delisted stocks] --> F[~60 features<br/>per stock-day]
    C[KAP disclosures<br/>~775k records, classified] --> F
    F --> M[Rules · Isolation Forest<br/>LightGBM · PU learning]
    L --> M
    M --> W[Weekly ranking<br/>~550 stocks]
    W --> E[Evaluation vs random<br/>case-level bootstrap]
```

### Labels: regulator decisions turned into cases

- **Parsing.** The parser reads ~1,000 weekly SPK bulletins in two formats:
  - pre-2012 bulletins name companies by legal title, not ticker, under the old law (art. 47/I-A-2);
  - newer bulletins have a structured sanctions section.
- **Case extraction.** It pulls out tickers, decision types and the manipulation period stated
  in the decision. Decisions about the same episode are merged into one case.
- **Scope.** Insider-trading, disclosure-only and warrant cases are excluded.
- **Accuracy.** A manual check of a sample found 94% label precision.

### Features (no look-ahead; every feature uses data up to day t only, unit-tested)

- **Returns:** return z-scores and excess return over the index.
- **Volume and turnover:** volume and free-float turnover relative to the stock's own history.
- **Price action:** limit-up streaks, up-day counts, close location, closing price vs VWAP.
- **Disclosures:** company disclosures classified by content into real news, price-reaction
  statements, rumors, etc. (93% accuracy on a held-out sample). This is used to test
  "price moves without news".

### Models

| Model | Type |
|---|---|
| Rule score | Count of surveillance-style thresholds |
| Isolation Forest | Unsupervised |
| LightGBM | Supervised; unlabeled days treated as negatives |
| PU learning | Positive-unlabeled; Elkan–Noto reweighting and Mordelet–Vert bagging |
| Rules + PU ensemble | Equal-weight average of weekly ranks, fixed before looking at results |

## Evaluation design and a note on rigor

**Protocol.** Models are retrained every year. Each year uses only data and SPK decisions
published before it, because SPK often announces cases years later. A walk-forward split that
ignored this would leak future labels into training.

**Metrics.** The question is practical: *if an analyst checked the top-k stocks every week,
which cases would they catch?* Results are reported with:
- **Random baseline:** an analytic one per case, P(caught at random) = 1 − Π(1 − k/Nₜ).
- **Confidence intervals:** case-cluster bootstrap.
- **Model comparisons:** paired bootstrap tests on the same cases.

**What we got wrong first.** A first version reported "40–47% of cases detected" without
comparing against chance. Once the random baseline was computed, that figure turned out to be
**no better than random**, because long label windows are easy to hit by luck. The result was
retracted and the whole evaluation was rebuilt. The retracted analysis is kept in
[docs/arsiv_v1/](docs/arsiv_v1/) for transparency.

**Other pitfalls found and fixed:**
- **Profile features let the model memorize which stocks had been manipulated before.** These
  were company size and free-float level. They were removed.
- **"Price moves without news" was distorted.** It counted the companies' own statements
  about unusual price moves as news. Fixed with content classification of disclosures.

## Thesis questions

| Question | Answer |
|---|---|
| 1. Can manipulation be detected early from daily data? | **Yes.** About 3× random, mostly before the price peak, over 15 years. |
| 2. Is PU learning better than supervised / unsupervised methods? | **Yes, partly.** Significantly better than supervised; tied with rules alone, better when combined. |
| 3. Do "moves without news" features help? | **No.** No significant gain. Adding all disclosure features even slightly hurts. |

## Limitations

- **Evaluable cases.** Only cases whose decision states the manipulation period can be
  evaluated: 184 of 413 core cases.
- **Slow manipulations are missed.** Slow, quiet manipulations, or ones riding a market-wide
  rally, look normal in daily data. Catching them likely needs broker-level data
  ("AKD", the next planned step).
- **False alarms.** Many flagged stocks are not SPK cases. Some may be manipulation SPK never
  pursued, but most are probably genuine volatility. The system is a triage tool, not a verdict.
- **Delisted companies.** Some delisted companies from early bulletins could not be matched
  to price data.

## Reproducing

The repository contains no data. Everything is downloaded from public sources, which takes
several hours in total.

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"   # Windows paths

# 1. Labels
python -m bistmd.ingest.spk_api --start 2016 --end 2026
python -m bistmd.ingest.spk_bulletins --start 2009 --end 2026
python -m bistmd.ingest.universe
python scripts/inventory.py                          # merge decisions → cases, fetch prices for case stocks

# 2. Market data
python -c "from bistmd.ingest import universe, prices_isyatirim as p; p.download(sorted(universe.load().ticker))"
python -m bistmd.ingest.kap_disclosures --start 2010-01-01
python -m bistmd.db                                  # → data/db/bist.duckdb
python scripts/build_features.py --start 2010-04-01

# 3. Models and evaluation
python scripts/score_v2.py --mode honest             # all models, yearly honest retraining
python scripts/score_v2.py --mode loyo --models 2_lightgbm,3b_pu_bagging
python scripts/ensemble_v2.py
python scripts/evaluate_v2.py                        # → docs/sonuclar_v2.md
python scripts/compare_v2.py                         # paired tests
python scripts/case_studies.py IZFAS-0 SANEL-0 KGYO-0 KONYA-0 KUYAS-0

python -m pytest
```

Some paired comparisons in `compare_v2.py` reference earlier score snapshots
(`scores_v2_before`, `scores_v2_novwap`). They are skipped when those folders are missing.

## Repository layout

```
src/bistmd/
  ingest/     SPK API & bulletins, İş Yatırım prices, KAP disclosures, company list
  labels/     bulletin parsing (old and new formats), ticker resolution, cases, label windows
  features/   price/volume features, KAP content classification and features
  models/     rules, Isolation Forest, LightGBM, PU learning
  eval/       weekly ranking metrics, random baseline, bootstrap
scripts/      pipeline entry points (scoring, ensemble, evaluation, case studies)
tests/        68 unit tests (no data needed), incl. look-ahead tests for features
docs/         results, interpretation, validation, case studies (Turkish)
```

## Data sources

| Data | Source |
|---|---|
| Enforcement decisions | SPK weekly bulletins (2009–2026) and SPK sanctions API |
| Daily prices, market cap, free float | İş Yatırım (includes delisted stocks, avoiding survivorship bias) |
| Company disclosures | KAP (Public Disclosure Platform) |

**Data handling.**
- Raw data is not redistributed.
- Personal data in SPK decisions (names, ID numbers) is never stored in processed tables.

## Türkçe

Bu belgenin tam Türkçe sürümü: [README.tr.md](README.tr.md). Ayrıntılı sonuç ve yorum belgeleri
(`docs/`) Türkçedir.

## License

[MIT](LICENSE) © 2026 Melih Erdem Koçoğlu
