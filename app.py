"""Forex AI Analyst — Streamlit entry point."""
import logging
import streamlit as st
from analysis import analyze_multi_timeframe
from config import APP_NAME, CACHE_TTL_SECONDS, INSTRUMENTS
from data import fetch_instrument
from interface import apply_css, render_dashboard
logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title=APP_NAME,page_icon="📊",layout="wide",initial_sidebar_state="expanded")
apply_css()
@st.cache_data(ttl=CACHE_TTL_SECONDS,show_spinner=False)
def load_market(instrument): return fetch_instrument(instrument)
def main():
    st.sidebar.header("Paramètres"); instrument=st.sidebar.selectbox("Instrument",list(INSTRUMENTS.keys())); capital=st.sidebar.number_input("Capital de référence",min_value=0.0,value=1000.0,step=100.0)
    st.sidebar.caption("Risque par trade : 1% • Risque ouvert max : 2% • R:R minimum : 1:2"); st.sidebar.warning("Analyse uniquement. Aucun ordre automatique.")
    if st.sidebar.button("Actualiser les données"): load_market.clear(); st.session_state["analysis_started"]=False; st.rerun()
    st.markdown(f'<div class="hero"><h1>{APP_NAME}</h1><div class="muted">{INSTRUMENTS[instrument]["label"]} • Trade préparé en <b>M15</b> • Analyse D1 → H4 → H1 → M15 → M5</div></div>',unsafe_allow_html=True)
    if not st.session_state.get("analysis_started",False):
        st.info("Configure ton instrument et ton capital, puis démarre l'analyse. L'IA observe d'abord les unités supérieures avant de préparer le setup M15.")
        if st.button("🚀 DÉBUTER L'ANALYSE",type="primary",use_container_width=True): st.session_state["analysis_started"]=True; st.rerun()
        st.caption("Aucun signal n'est calculé avant l'appui sur le bouton."); return
    if st.button("🔄 Refaire l'analyse",use_container_width=True): load_market.clear(); st.rerun()
    try:
        with st.spinner("Analyse D1 → H4 → H1 → M15 → M5 en cours…"): frames,warnings,used_proxy=load_market(instrument)
        if used_proxy: st.warning("XAU/USD : GC=F est utilisé comme proxy futures. Ce n'est pas le spot XAU/USD.")
        for key,msg in warnings.items():
            if key!="global": st.info(msg)
        if not frames: st.error("Impossible de récupérer les données de marché. Vérifiez la connexion réseau/Yahoo Finance puis réessayez."); return
        result=analyze_multi_timeframe(frames); price=next((float(frames[tf]["close"].iloc[-1]) for tf in ["M5","M15","H1","H4","D1"] if tf in frames and not frames[tf].empty),None)
        if price is None: st.error("Aucun prix exploitable n'a été trouvé."); return
        render_dashboard(instrument,price,result,capital)
    except Exception:
        logging.exception("Unexpected application error"); st.error("Une erreur interne est survenue pendant l'analyse. L'interface reste disponible ; consultez les logs pour le diagnostic technique.")
if __name__=="__main__": main()
