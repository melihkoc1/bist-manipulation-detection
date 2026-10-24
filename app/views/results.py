"""Sonuçlar: rastgeleye karşı başarı, SPK'ya göre zaman, tez soruları, vaka çalışmaları."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ui_data as D
from ui_text import CASES, MODELS, label, pct, t

st.title(t("rs_title"))
st.caption(t("rs_caption"))

res = D.results()
periods = ["2017–2026", "2017–2021", "2022–2026", "2012–2016", "2012–2026"]
period = st.segmented_control(t("rs_period"), periods, default="2017–2026", key="rs_period") or "2017–2026"
r = res[res["period"] == period].set_index("model")
best = r.loc["4_kural_pu"]
st.caption(t("rs_cases", n=int(best["n_cases"])))

m1, m2, m3, m4 = st.columns(4)
m1.metric(t("rs_caught"), pct(best["rec@20"]), help=t("rs_caught_help"))
m1.caption(t("rs_random", x=pct(best["rnd@20"])))
m2.metric(t("rs_auc"), f"{best['auc']:.2f}")
m3.metric(t("rs_before_peak"), pct(best["pre_peak@20"]))
m3.caption(t("rs_random", x=pct(best["pre_peak_rnd@20"])))
m4.metric(t("rs_lead"), t("rs_lead_val", d=int(best["lead_med@20"])))

st.subheader(t("rs_table"))
order = [m for m in MODELS if m in r.index]
tbl = pd.DataFrame({
    t("col_model"): [label(MODELS, m) for m in order],
    t("col_auc"): [f"{r.loc[m, 'auc']:.2f} [{r.loc[m, 'auc_lo']:.2f}–{r.loc[m, 'auc_hi']:.2f}]" for m in order],
    t("col_rec20"): [pct(r.loc[m, "rec@20"]) for m in order],
    t("col_rnd20"): [pct(r.loc[m, "rnd@20"]) for m in order],
    t("col_lift20"): [f"{r.loc[m, 'lift@20']:.1f}×" for m in order],
    t("col_peak"): [pct(r.loc[m, "pre_peak@20"]) for m in order],
    t("col_prec10"): [f"{r.loc[m, 'plift@10']:.1f}×" for m in order],
})
st.dataframe(tbl, hide_index=True, width="stretch")

st.subheader(t("rs_chart"))
names = [label(MODELS, m) for m in order]
fig = go.Figure([
    go.Bar(name=t("rs_series_model"), x=names, y=[100 * r.loc[m, "rec@20"] for m in order], marker_color="#2a9d8f",
           hovertemplate="%{x}<br>%{y:.0f}%<extra></extra>"),
    go.Bar(name=t("rs_series_random"), x=names, y=[100 * r.loc[m, "rnd@20"] for m in order], marker_color="#c9c9c9",
           hovertemplate="%{x}<br>%{y:.0f}%<extra></extra>"),
])
fig.update_layout(barmode="group", height=360, yaxis_title="%", margin=dict(l=10, r=10, t=10, b=10),
                  legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, width="stretch")

st.subheader(t("rs_spk"))
st.markdown(t("rs_spk_text", **D.spk_timing()))

st.subheader(t("rs_questions"))
for q in ("q1", "q2", "q3"):
    st.markdown(t(q))

st.subheader(t("rs_cases_title"))
tabs = st.tabs([c.split("-")[0] for c in CASES])
for tab, (cid, text) in zip(tabs, CASES.items()):
    with tab:
        st.markdown(label(CASES, cid))
        img = D.FIGURES / f"vaka_{cid}.png"
        if img.exists():
            st.image(str(img), width="stretch")

st.subheader(t("rs_limits"))
st.markdown(t("limits"))
