"""Hisse detayı: fiyat, hacim, haftalık sıra; SPK dönemleri ve kararları; KAP bildirimleri."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import ui_data as D
from ui_text import DECISION_TYPES, label, t

st.title(t("sd_title"))

names = D.company_names()
wk = D.weekly_scores("4_kural_pu")
tickers = sorted(wk["ticker"].unique())
default = st.session_state.get("sd_ticker", "IZFAS")
ticker = st.selectbox(t("sd_pick"), tickers, index=tickers.index(default) if default in tickers else 0,
                      format_func=lambda x: f"{x} — {names.get(x, '')}")
if ticker != st.session_state.get("sd_ticker"):
    st.session_state["sd_ticker"] = ticker
    st.session_state.pop("sd_focus", None)

p = D.prices(ticker)
if p.empty:
    st.warning("—")
    st.stop()
lo_all, hi_all = p["date"].min().date(), p["date"].max().date()
focus = st.session_state.get("sd_focus")
if focus is not None:
    f = pd.Timestamp(focus)
    default_range = (max(lo_all, (f - pd.DateOffset(months=9)).date()), min(hi_all, (f + pd.DateOffset(months=9)).date()))
else:
    default_range = (max(lo_all, (pd.Timestamp(hi_all) - pd.DateOffset(years=3)).date()), hi_all)
lo, hi = st.slider(t("sd_range"), min_value=lo_all, max_value=hi_all, value=default_range, format="DD.MM.YYYY",
                   key=f"sd_range_{ticker}_{focus}")
lo, hi = pd.Timestamp(lo), pd.Timestamp(hi)

p = p[p["date"].between(lo, hi)]
w = wk[(wk["ticker"] == ticker) & wk["week_end"].between(lo, hi)]
cases = D.cases()
cases = cases[(cases["ticker"] == ticker) & cases["known_period"] & (cases["start"] <= hi) & (cases["end"] >= lo)]
dec_all = D.decisions()
dec_all = dec_all[dec_all["ticker"] == ticker]
dec = dec_all[dec_all["decision_date"].between(lo, hi)]

m1, m2, m3 = st.columns(3)
m1.metric(t("sd_best"), int(w["rank"].min()) if len(w) else "—")
m2.metric(t("sd_alarm_weeks"), int((w["rank"] <= 20).sum()))
m3.metric(t("sd_n_decisions"), len(dec_all))

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.55, 0.2, 0.25])
fig.add_trace(go.Scatter(x=p["date"], y=p["close"], name=t("sd_price"), line=dict(color="#264653", width=1.6),
                         hovertemplate="%{x|%d.%m.%Y}<br>%{y:.3f}<extra></extra>"), row=1, col=1)
fig.add_trace(go.Bar(x=p["date"], y=p["value_try"] / 1e6, name=t("sd_volume"), marker_color="#2a9d8f",
                     hovertemplate="%{x|%d.%m.%Y}<br>%{y:.1f}<extra></extra>"), row=2, col=1)
fig.add_trace(go.Scatter(x=w["week_end"], y=w["rank"], name=t("sd_rank"), mode="lines+markers",
                         line=dict(color="#6d597a", width=1.2), marker=dict(size=4),
                         hovertemplate="%{x|%d.%m.%Y}<br>#%{y}<extra></extra>"), row=3, col=1)
fig.add_hline(y=20, line=dict(color="#e63946", dash="dash", width=1), row=3, col=1,
              annotation_text=t("sd_top20"), annotation_position="top left", annotation_font_color="#e63946")
for _, c in cases.iterrows():
    fig.add_vrect(x0=c["start"], x1=c["end"], fillcolor="#f4a261", opacity=0.25, line_width=0, row="all", col=1)
if len(cases):
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=t("sd_period"),
                             marker=dict(size=12, symbol="square", color="rgba(244,162,97,0.5)")), row=1, col=1)
for _, d in dec.iterrows():
    fig.add_vline(x=d["decision_date"], line=dict(color="black", dash="dot", width=1))
if len(dec):
    top_y = p["close"].max()
    fig.add_trace(go.Scatter(
        x=dec["decision_date"], y=[top_y] * len(dec), mode="markers", name=t("sd_decision"),
        marker=dict(symbol="triangle-down", size=11, color="black"),
        text=[label(DECISION_TYPES, x) for x in dec["decision_type"]],
        hovertemplate="%{x|%d.%m.%Y}<br>%{text}<extra></extra>"), row=1, col=1)
if focus is not None and lo <= pd.Timestamp(focus) <= hi:
    fig.add_vline(x=pd.Timestamp(focus), line=dict(color="#e63946", width=1.5))
fig.update_xaxes(tickformat="%m.%Y")
fig.update_yaxes(title_text=t("sd_price"), row=1, col=1)
fig.update_yaxes(title_text=t("sd_volume"), row=2, col=1)
fig.update_yaxes(title_text=t("sd_rank"), type="log", autorange=False, range=[2.8, -0.1],
                 tickvals=[1, 5, 20, 100, 500], row=3, col=1)
fig.update_layout(height=640, margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
                  legend=dict(orientation="h", y=1.06, x=0), bargap=0)
st.plotly_chart(fig, width="stretch")

st.subheader(t("sd_decisions"))
if dec_all.empty:
    st.info(t("sd_no_decisions"))
else:
    def period(r):
        if pd.isna(r["period_start"]):
            return ""
        return f"{r['period_start']:%d.%m.%Y} – {r['period_end']:%d.%m.%Y}"
    st.dataframe(pd.DataFrame({
        t("col_date"): dec_all["decision_date"].dt.strftime("%d.%m.%Y"),
        t("col_type"): [label(DECISION_TYPES, x) for x in dec_all["decision_type"]],
        t("col_period"): [period(r) for _, r in dec_all.iterrows()],
        t("col_ref"): dec_all["ref"],
    }), hide_index=True, width="stretch")

st.subheader(t("sd_kap"))
k = D.kap(ticker, lo, hi)
q = st.text_input(t("sd_kap_search"), key=f"kap_q_{ticker}")
if q:
    mask = k["subject"].fillna("").str.contains(q, case=False) | k["summary"].fillna("").str.contains(q, case=False)
    k = k[mask]
st.dataframe(pd.DataFrame({
    t("col_date"): k["published_at"].dt.strftime("%d.%m.%Y %H:%M"),
    t("col_subject"): k["subject"],
    t("col_summary"): k["summary"],
}), hide_index=True, width="stretch", height=320)
