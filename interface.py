"""Streamlit presentation layer and professional Plotly dashboard."""
from __future__ import annotations
from typing import Dict, Optional
import math
import plotly.graph_objects as go
import streamlit as st
from config import APP_NAME, APP_SUBTITLE, TIMEFRAMES
from risk import build_setup, build_step_up, risk_summary

def _fmt(v, digits=5):
    if v is None: return "—"
    try:
        if not math.isfinite(float(v)): return "—"
        return f"{float(v):,.{digits}f}"
    except (TypeError, ValueError): return "—"

def decision_badge(d):
    return {"ACHAT":"🟢 ACHAT","VENTE":"🔴 VENTE","ATTENDRE":"🟠 ATTENDRE","AUCUN SETUP":"⚪ AUCUN SETUP"}.get(d,d)

def decision_card(d):
    styles={"ACHAT":("#198754","rgba(25,135,84,.12)"),"VENTE":("#dc3545","rgba(220,53,69,.12)"),"ATTENDRE":("#fd7e14","rgba(253,126,20,.12)"),"AUCUN SETUP":("#6c757d","rgba(108,117,125,.12)")}
    color,bg=styles.get(d,("#6c757d","rgba(108,117,125,.12)"))
    st.markdown(f'''<div class="decision-card" style="border-color:{color};background:{bg}"><div class="decision-label">DÉCISION DU MOTEUR</div><div class="decision-value" style="color:{color}">{decision_badge(d)}</div><div class="decision-note">Trade préparé sur <b>M15</b> avec contexte D1/H4, confirmation H1 et validation M5.</div></div>''',unsafe_allow_html=True)

def apply_css():
    st.markdown("""<style>
    .block-container{max-width:1450px;padding-top:1rem;padding-bottom:3rem}.hero{padding:1.2rem 1.4rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin-bottom:1rem}.muted{opacity:.72;font-size:.9rem}
    .decision-card{border:2px solid;border-radius:18px;padding:1.2rem 1.4rem;margin:.6rem 0 1.2rem;text-align:center}.decision-label{font-size:.82rem;letter-spacing:.12em;opacity:.7;font-weight:700}.decision-value{font-size:2rem;font-weight:900;margin:.3rem 0}.decision-note{font-size:.92rem;opacity:.78}
    </style>""",unsafe_allow_html=True)

def render_chart(tf_result: Dict):
    df=tf_result.get("data")
    if df is None or df.empty: st.info("Pas assez de données pour afficher le graphique."); return
    fig=go.Figure(); fig.add_trace(go.Candlestick(x=df.index,open=df.open,high=df.high,low=df.low,close=df.close,name="Prix"))
    for col,name in [("ema20","EMA20"),("ema50","EMA50"),("sma200","SMA200")]:
        if col in df: fig.add_trace(go.Scatter(x=df.index,y=df[col],mode="lines",name=name))
    for col,name in [("bb_upper","BB Upper"),("bb_lower","BB Lower")]:
        if col in df: fig.add_trace(go.Scatter(x=df.index,y=df[col],mode="lines",name=name,line=dict(dash="dot")))
    zones=tf_result.get("zones",{})
    for z in zones.get("supports",[])[:4]: fig.add_hline(y=z["price"],line_dash="dot",annotation_text=f"S {_fmt(z['price'])}")
    for z in zones.get("resistances",[])[:4]: fig.add_hline(y=z["price"],line_dash="dot",annotation_text=f"R {_fmt(z['price'])}")
    for label,value in tf_result.get("fib",{}).get("levels",{}).items(): fig.add_hline(y=value,line_dash="dash",annotation_text=f"Fib {label}")
    sd=tf_result.get("structure_data",{}).get("data")
    if sd is not None and not sd.empty:
        sh=sd[sd["swing_high"]]; sl=sd[sd["swing_low"]]
        if not sh.empty: fig.add_trace(go.Scatter(x=sh.index,y=sh.high,mode="markers+text",text=sh.swing_label,name="Swing High",textposition="top center"))
        if not sl.empty: fig.add_trace(go.Scatter(x=sl.index,y=sl.low,mode="markers+text",text=sl.swing_label,name="Swing Low",textposition="bottom center"))
        for col in ["bos","choch"]:
            ev=sd[sd[col]!=""]
            if not ev.empty: fig.add_trace(go.Scatter(x=ev.index,y=ev.close,mode="markers+text",text=ev[col],name=col.upper(),textposition="top center"))
    fig.update_layout(height=650,xaxis_rangeslider_visible=False,hovermode="x unified",margin=dict(l=10,r=10,t=30,b=10),legend=dict(orientation="h"))
    st.plotly_chart(fig,use_container_width=True,config={"responsive":True,"displaylogo":False})

def render_dashboard(instrument: str, price: float, result: Dict, capital: float):
    st.markdown(f'<div class="hero"><h1>{APP_NAME}</h1><div class="muted">{APP_SUBTITLE}</div></div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4); c1.metric("Instrument",instrument); c2.metric("Prix actuel",_fmt(price)); c3.metric("Score",f'{result["score"]:+.1f}'); c4.metric("Confiance",f'{result["confidence"]:.0f}%')
    st.subheader("ANALYSE MULTI-TIMEFRAME"); st.caption("Trade exécuté/préparé en M15 : D1/H4 = contexte, H1 = confirmation, M5 = validation de l'entrée.")
    cols=st.columns(len(TIMEFRAMES))
    for col,tf in zip(cols,TIMEFRAMES):
        r=result["timeframes"].get(tf,{})
        with col:
            st.markdown(f"**{tf}**")
            if not r.get("available"): st.warning("Indisponible"); continue
            st.write(f"Direction : **{r['direction']}**"); st.write(f"Score : **{r['score']:+.1f}**"); st.write(f"Confiance : **{r['confidence']:.0f}%**"); st.write(f"Tendance : **{r['trend']}**")
            sd=r.get("structure_data",{}); st.caption(f"Structure : {r['structure']} • HH {sd.get('hh',0)} • HL {sd.get('hl',0)} • LH {sd.get('lh',0)} • LL {sd.get('ll',0)}")
            ind=r.get("indicators",{}); st.caption(f"RSI {_fmt(ind.get('rsi14'),1)} • ADX {_fmt(ind.get('adx14'),1)} • MACD {_fmt(ind.get('macd_hist'),5)}")
    m15=result["timeframes"].get("M15",{}); setup=None; setup_source="M15"
    # The M15 setup must use the latest M15 price, not the latest lower-timeframe price (M5).
    setup_price = m15.get("price") if m15.get("available") else price
    if result["decision"] in {"ACHAT","VENTE"} and m15.get("available"):
        setup=build_setup(setup_price,m15.get("indicators",{}).get("atr14"),m15.get("structure_data",{}),result["decision"],m15.get("zones",{}))
        if not setup.get("valid"): setup=None
    if not setup and result["decision"] in {"ACHAT","VENTE"} and not m15.get("available"):
        h1=result["timeframes"].get("H1",{})
        if h1.get("available"):
            setup_source="H1 (fallback)"; setup=build_setup(h1.get("price", price),h1.get("indicators",{}).get("atr14"),h1.get("structure_data",{}),result["decision"],h1.get("zones",{}))
            if not setup.get("valid"): setup=None
    st.subheader("GRAPHIQUE")
    available=[tf for tf in TIMEFRAMES if result["timeframes"].get(tf,{}).get("available")]
    if not available: st.error("Aucun timeframe exploitable."); return
    default_index=available.index("M15") if "M15" in available else (available.index("H1") if "H1" in available else 0)
    chart_tf=st.selectbox("Timeframe du graphique",available,index=default_index); render_chart(result["timeframes"][chart_tf])
    st.subheader("🎯 PLAN DE TRADE M15")
    if setup:
        a,b,c,d,e=st.columns(5); a.metric("ENTRY",_fmt(setup["entry"])); b.metric("STOP LOSS",_fmt(setup["sl"])); c.metric("TAKE PROFIT 1",_fmt(setup["tp1"])); d.metric("TAKE PROFIT 2",_fmt(setup["tp2"])); e.metric("R:R",f"1:{setup['rr1']:.1f} / 1:{setup['rr2']:.1f}")
        st.caption(f"Setup source : **{setup_source}** • R:R minimum : 1:2 • Aucun ordre automatique.")
    else: st.info("Aucun plan M15 valide : Entry, Stop Loss et Take Profits ne sont affichés que lorsqu'un setup respecte les conditions minimales.")
    st.subheader("📈 STEP-UP / GESTION DE POSITION")
    if setup:
        for step in build_step_up(setup)["steps"]:
            st.markdown(f"**{step['name']} — {step['trigger_text']} : {_fmt(step['trigger'])}**"); st.write(f"SL de référence : **{_fmt(step['sl'])}** • {step['action']}")
        st.caption("Les STEP-UP sont théoriques : aucun déplacement de SL ni ordre broker n'est exécuté automatiquement.")
    else: st.info("Les STEP-UP apparaîtront avec un setup M15 valide.")
    decision_card(result["decision"])
    st.subheader("STRUCTURE DU MARCHÉ")
    chart_result=result["timeframes"][chart_tf]; sd=chart_result.get("structure_data",{}); a,b,c,d=st.columns(4); a.metric("HH",sd.get("hh",0)); b.metric("HL",sd.get("hl",0)); c.metric("LH",sd.get("lh",0)); d.metric("LL",sd.get("ll",0)); st.write("**BOS :**",", ".join(sd.get("bos",[])) or "Aucun récent"); st.write("**CHoCH :**",", ".join(sd.get("choch",[])) or "Aucun récent")
    st.subheader("SUPPORT / RÉSISTANCE")
    z=chart_result.get("zones",{}); st.dataframe({"Support":[_fmt(x["price"]) for x in z.get("supports",[])],"Touches support":[x["touches"] for x in z.get("supports",[])],"Résistance":[_fmt(x["price"]) for x in z.get("resistances",[])],"Touches résistance":[x["touches"] for x in z.get("resistances",[])]},use_container_width=True,hide_index=True)
    st.subheader("FIBONACCI"); fib=chart_result.get("fib",{})
    if fib.get("levels"): st.dataframe({"Niveau":list(fib["levels"].keys()),"Prix":[_fmt(v) for v in fib["levels"].values()]},use_container_width=True,hide_index=True); st.write("Niveau le plus proche :",fib.get("nearest"))
    else: st.info("Pas assez de swings significatifs pour calculer Fibonacci.")
    st.subheader("GESTION DU RISQUE")
    if setup:
        rs=risk_summary(capital,setup["entry"],setup["sl"]); a,b,c,d=st.columns(4); a.metric("Capital",f"{capital:,.2f}"); b.metric("Risque autorisé",f"{rs['risk_amount']:,.2f}"); c.metric("Distance Entry → SL",_fmt(rs["distance"])); d.metric("Unités théoriques",f"{rs['units']:,.2f}"); st.caption(f"Risque ouvert maximum configuré : {rs['max_open_risk_amount']:,.2f} ({rs['max_open_risk_fraction']:.0%}). {rs['note']}")
    else: st.info("La gestion du risque détaillée sera affichée lorsqu'un setup valide existe.")
    st.subheader("POURQUOI CETTE DÉCISION ?"); st.write(result["explanation"])
    if result.get("available_count",0)<len(TIMEFRAMES): st.warning("Certains timeframes sont indisponibles. La confiance est réduite et aucun signal complet n'est forcé.")
