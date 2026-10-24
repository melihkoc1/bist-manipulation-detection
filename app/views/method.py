"""Yöntem: sistemin nasıl çalıştığı."""

import streamlit as st

from ui_text import t

st.title(t("mt_title"))
st.markdown(t("mt_intro"))


def node(name: str, key: str, color: str) -> str:
    return f'{name} [label="{t(key)}", fillcolor="{color}"]'


st.graphviz_chart(
    "digraph { rankdir=LR; node [shape=box, style=\"rounded,filled\", fontname=\"Helvetica\", fontsize=11, "
    "color=\"#999999\"]; "
    + "; ".join([
        node("spk", "flow_spk", "#fde2c8"), node("pr", "flow_prices", "#d8efe9"), node("kap", "flow_kap", "#d8efe9"),
        node("lab", "flow_labels", "#fde2c8"), node("feat", "flow_features", "#d8efe9"),
        node("mod", "flow_models", "#e4dcef"), node("rank", "flow_rank", "#e4dcef"), node("ev", "flow_eval", "#f3d5d8"),
    ])
    + "; spk -> lab; pr -> feat; kap -> feat; lab -> mod; feat -> mod; mod -> rank; rank -> ev; lab -> ev }",
    width="stretch",
)

for k in ("labels", "features", "models", "eval"):
    st.subheader(t(f"mt_{k}_t"))
    st.markdown(t(f"mt_{k}"))

st.subheader(t("mt_lesson_t"))
st.info(t("mt_lesson"))
