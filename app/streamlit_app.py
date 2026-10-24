"""BIST manipülasyon tespiti — tanıtım arayüzü.

Çalıştırma (proje kökünden):  streamlit run app/streamlit_app.py
Önkoşul: README'deki veri hattı (veritabanı, özellikler, skorlar, sonuçlar) çalıştırılmış olmalı.
"""

import streamlit as st

import ui_data as D
from ui_text import t

st.set_page_config(page_title="BIST Manipulation Detection", page_icon="📈", layout="wide")

with st.sidebar:
    # Dil adres çubuğunda da tutulur (?lang=en), sayfa yenilense de korunur.
    # Seçim kaldırılırsa (None) metinler Türkçe kalır; bkz. ui_text.lang_index
    if "lang" not in st.session_state:
        st.session_state["lang"] = "English" if st.query_params.get("lang") == "en" else "Türkçe"
    st.segmented_control("Dil / Language", ["Türkçe", "English"], key="lang")
    st.query_params["lang"] = "en" if st.session_state.get("lang") == "English" else "tr"

pages = [
    st.Page("views/time_machine.py", title=t("nav_tm"), icon="🕰️", default=True),
    st.Page("views/stock_detail.py", title=t("nav_stock"), icon="🔎"),
    st.Page("views/results.py", title=t("nav_results"), icon="📊"),
    st.Page("views/method.py", title=t("nav_method"), icon="🧭"),
]
nav = st.navigation(pages)

with st.sidebar:
    st.markdown(f"### {t('app_title')}")
    st.caption(t("disclaimer"))
    st.caption("Melih Erdem Koçoğlu · [GitHub](https://github.com/melihkoc1/bist-manipulation-detection)")

missing = D.missing_inputs()
if missing:
    st.error(t("missing_data", path=", ".join(missing)))
    st.stop()

nav.run()
