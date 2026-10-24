"""Zaman makinesi: seçilen haftanın şüpheli listesi ve sonradan gelen SPK kararları."""

import pandas as pd
import streamlit as st

import ui_data as D
from ui_text import MODELS, RULES, label, t

EXAMPLES = {"IZFAS · 06.2018": "2018-06-08", "SANEL · 05.2019": "2019-05-17", "KGYO · 07.2022": "2022-07-15"}

st.title(t("tm_title"))
st.markdown(t("tm_caption"))

model = st.radio(t("model"), D.LIST_MODELS, format_func=lambda m: label(MODELS, m), horizontal=True, key="tm_model")
wk = D.weekly_scores(model)
weeks = sorted(d.date() for d in wk["week_end"].unique())

if "tm_week" not in st.session_state:
    st.session_state["tm_week"] = pd.Timestamp(EXAMPLES["IZFAS · 06.2018"]).date()

ex_cols = st.columns([1.2] + [1] * len(EXAMPLES) + [3])
ex_cols[0].markdown(f"**{t('examples')}:**")
for col, (name, day) in zip(ex_cols[1:], EXAMPLES.items()):
    if col.button(name, width="stretch"):
        st.session_state["tm_week"] = pd.Timestamp(day).date()

c1, c2 = st.columns([4, 1])
week = c1.select_slider(t("week"), options=weeks, key="tm_week", format_func=lambda d: d.strftime("%d.%m.%Y"))
k = c2.select_slider(t("list_size"), options=[10, 20, 30, 50], value=20, key="tm_k")

this = wk[wk["week_end"].dt.date == week]
week_start, week_end = this["week_start"].iloc[0], this["week_end"].iloc[0]
top = this.nsmallest(k, "rank")
tickers = top["ticker"].tolist()
names = D.company_names()
rules = D.rules_fired(tickers, week_start, week_end)
links = D.spk_links(tickers, week_start, week_end)

def spk_text(tk: str) -> str:
    if tk not in links:
        return ""
    status, days = links[tk]
    return {"in_period": "✅ ", "in_period_before": "✅ ", "later": "🟡 "}[status] + t(f"spk_{status}", days=days)

table = pd.DataFrame({
    t("col_rank"): top["rank"].astype(int).to_numpy(),
    t("col_ticker"): tickers,
    t("col_spk"): [spk_text(x) for x in tickers],
    t("col_score"): (100 * top["pct"]).round(1).to_numpy(),
    t("col_rules"): [" · ".join(label(RULES, r) for r in rules.get(x, [])) for x in tickers],
    t("col_name"): [names.get(x, "") for x in tickers],
})

n_week = int(this["n_week"].iloc[0])
in_period = D.tickers_in_known_periods(week_start, week_end) & set(this["ticker"])
hits = sum(1 for x in tickers if x in in_period)
expected = k * len(in_period) / n_week
m1, m2, m3 = st.columns(3)
m1.metric(t("m_in_period"), f"{hits} / {k}", help=t("m_in_period_help"))
m1.caption(t("m_random", x=f"{expected:.1f}"))
m2.metric(t("m_stocks"), n_week)
m3.metric(t("week"), f"{week_start:%d.%m} – {week_end:%d.%m.%Y}")

st.caption(t("tm_click"))
event = st.dataframe(
    table, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
    column_config={
        t("col_rank"): st.column_config.NumberColumn(t("col_rank"), width=50),
        t("col_ticker"): st.column_config.TextColumn(t("col_ticker"), width=70),
        t("col_spk"): st.column_config.TextColumn(t("col_spk"), width="large"),
        t("col_score"): st.column_config.ProgressColumn(t("col_score"), min_value=0, max_value=100, format="%.1f",
                                                        width="small"),
        t("col_rules"): st.column_config.TextColumn(t("col_rules"), width="large"),
    },
    height=min(38 + 35 * len(table), 760),
)
st.caption(t("tm_note"))

if event.selection.rows:
    st.session_state["sd_ticker"] = tickers[event.selection.rows[0]]
    st.session_state["sd_focus"] = week_end
    st.switch_page("views/stock_detail.py")
