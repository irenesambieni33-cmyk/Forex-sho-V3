"""Multi-timeframe technical scoring, confluence and decision engine."""

from __future__ import annotations
from typing import Dict, List
import math
import numpy as np
import pandas as pd
from config import TIMEFRAME_WEIGHTS
from fibonacci import calculate_fibonacci, confluence
from indicators import add_indicators
from structure import analyze_structure
from support_resistance import detect_zones

INDICATOR_KEYS = ["ema20","ema50","sma200","rsi14","macd","macd_signal","macd_hist","atr14","adx14","di_plus","di_minus","stoch_k","stoch_d","bb_upper","bb_lower","bb_mid"]


def _last(df, key):
    s = df[key].dropna() if key in df else pd.Series(dtype=float)
    return float(s.iloc[-1]) if not s.empty else math.nan


def analyze_timeframe(df: pd.DataFrame, timeframe: str) -> Dict:
    base = {"timeframe": timeframe, "available": False, "direction": "NEUTRE", "score": 0.0, "confidence": 0.0,
            "trend": "RANGE / NEUTRE", "structure": "RANGE / NEUTRE", "indicators": {}, "structure_data": {},
            "zones": {}, "fib": {}, "confluence": {}, "reasons": []}
    if df is None or df.empty:
        return base
    work = add_indicators(df)
    structure = analyze_structure(work)
    work = structure["data"]
    zones = detect_zones(work)
    fib = calculate_fibonacci(work, structure)
    price = _last(work, "close")
    ind = {k: _last(work, k) for k in INDICATOR_KEYS}
    score = 0.0
    possible = 0.0
    reasons: List[str] = []

    def feature(value: float | None, maximum: float, reason: str = ""):
        nonlocal score, possible
        if value is None or not math.isfinite(value):
            return
        score += value
        possible += maximum
        if reason and abs(value) > 0.01:
            reasons.append(reason)

    ema = 1.0 if ind["ema20"] > ind["ema50"] else -1.0 if ind["ema20"] < ind["ema50"] else 0.0 if np.isfinite(ind["ema20"]) and np.isfinite(ind["ema50"]) else None
    feature(ema, 1.0, "EMA20 > EMA50" if ema == 1 else "EMA20 < EMA50" if ema == -1 else "")
    if np.isfinite(ind["sma200"]):
        feature(1.0 if price > ind["sma200"] else -1.0, 1.0, "Prix au-dessus de SMA200" if price > ind["sma200"] else "Prix sous SMA200")
    if np.isfinite(ind["rsi14"]):
        rsi_score = 1.0 if 52 <= ind["rsi14"] <= 68 else -1.0 if 32 <= ind["rsi14"] <= 48 else 0.0
        feature(rsi_score, 1.0, "RSI favorable aux acheteurs" if rsi_score > 0 else "RSI favorable aux vendeurs" if rsi_score < 0 else "")
    if np.isfinite(ind["macd_hist"]):
        feature(1.0 if ind["macd_hist"] > 0 else -1.0 if ind["macd_hist"] < 0 else 0.0, 1.0, "MACD positif" if ind["macd_hist"] > 0 else "MACD négatif")
    if np.isfinite(ind["adx14"]) and np.isfinite(ind["di_plus"]) and np.isfinite(ind["di_minus"]):
        if ind["adx14"] >= 20:
            dscore = 1.0 if ind["di_plus"] > ind["di_minus"] else -1.0 if ind["di_minus"] > ind["di_plus"] else 0.0
        else:
            dscore = 0.0
        feature(dscore, 1.0, "ADX/DI acheteurs" if dscore > 0 else "ADX/DI vendeurs" if dscore < 0 else "")
    if np.isfinite(ind["stoch_k"]) and np.isfinite(ind["stoch_d"]):
        feature(0.5 if ind["stoch_k"] > ind["stoch_d"] else -0.5 if ind["stoch_k"] < ind["stoch_d"] else 0.0, 0.5,
                "Stochastique haussier" if ind["stoch_k"] > ind["stoch_d"] else "Stochastique baissier")
    if np.isfinite(ind["bb_upper"]) and np.isfinite(ind["bb_lower"]):
        bb_score = -0.5 if price > ind["bb_upper"] else 0.5 if price < ind["bb_lower"] else 0.0
        feature(bb_score, 0.5, "Prix au-dessus de la bande supérieure" if bb_score < 0 else "Prix sous la bande inférieure" if bb_score > 0 else "")

    trend = structure["trend"]
    feature(1.5 if trend == "HAUSSIÈRE" else -1.5 if trend == "BAISSIÈRE" else 0.0, 1.5, "Structure haussière" if trend == "HAUSSIÈRE" else "Structure baissière" if trend == "BAISSIÈRE" else "")
    recent_bos = structure.get("bos", [])[-1:] + structure.get("choch", [])[-1:]
    if any("HAUSSIER" in x for x in recent_bos):
        feature(1.0, 1.0, "BOS/CHoCH haussier récent")
    elif any("BAISSIER" in x for x in recent_bos):
        feature(-1.0, 1.0, "BOS/CHoCH baissier récent")
    else:
        feature(0.0, 1.0)

    conf = confluence(fib, zones, price, ind["atr14"])
    if conf["bull"] > conf["bear"]:
        feature(1.0, 1.0, "Confluence support/Fibonacci favorable aux achats")
    elif conf["bear"] > conf["bull"]:
        feature(-1.0, 1.0, "Confluence résistance/Fibonacci favorable aux ventes")
    else:
        feature(0.0, 1.0)

    normalized = 100.0 * score / possible if possible else 0.0
    if normalized >= 20:
        direction = "ACHAT"
    elif normalized <= -20:
        direction = "VENTE"
    else:
        direction = "NEUTRE"
    # Confidence measures both directional strength and data completeness.
    completeness = min(1.0, possible / 10.5)
    confidence = min(100.0, abs(normalized) * completeness)
    return {"timeframe": timeframe, "available": True, "data": work, "price": price, "direction": direction,
            "score": normalized, "confidence": confidence, "trend": trend, "structure": trend,
            "indicators": ind, "structure_data": structure, "zones": zones, "fib": fib, "confluence": conf, "reasons": reasons}


def _same_direction(results, tfs, direction):
    usable = [results.get(tf, {}) for tf in tfs if results.get(tf, {}).get("available")]
    return len(usable) >= 2 and all(r.get("direction") == direction for r in usable)


def analyze_multi_timeframe(frames: Dict[str, pd.DataFrame]) -> Dict:
    results = {}
    for tf in TIMEFRAME_WEIGHTS:
        try:
            results[tf] = analyze_timeframe(frames.get(tf, pd.DataFrame()), tf)
        except Exception as exc:
            results[tf] = {"timeframe": tf, "available": False, "direction": "NEUTRE", "score": 0.0, "confidence": 0.0,
                           "trend": "RANGE / NEUTRE", "structure": "RANGE / NEUTRE", "error": str(exc)}

    total_w = sum(w for tf, w in TIMEFRAME_WEIGHTS.items() if results.get(tf, {}).get("available"))
    global_score = sum(results[tf]["score"] * w for tf, w in TIMEFRAME_WEIGHTS.items() if results.get(tf, {}).get("available")) / total_w if total_w else 0.0
    major_bull = _same_direction(results, ["D1","H4","H1"], "ACHAT")
    major_bear = _same_direction(results, ["D1","H4","H1"], "VENTE")
    m15 = results.get("M15", {}); m5 = results.get("M5", {})
    lower_complete = m15.get("available") and m5.get("available")
    lower_bull = lower_complete and m15.get("direction") == "ACHAT" and m5.get("direction") == "ACHAT"
    lower_bear = lower_complete and m15.get("direction") == "VENTE" and m5.get("direction") == "VENTE"

    if major_bull and lower_bull and global_score >= 35:
        decision = "ACHAT"
    elif major_bear and lower_bear and global_score <= -35:
        decision = "VENTE"
    elif abs(global_score) >= 18:
        decision = "ATTENDRE"
    else:
        decision = "AUCUN SETUP"

    available = sum(bool(r.get("available")) for r in results.values())
    alignment = sum(1 for tf in ["D1","H4","H1"] if results.get(tf, {}).get("available") and results[tf].get("direction") in {"ACHAT","VENTE"})
    confirmation = sum(1 for tf in ["M15","M5"] if results.get(tf, {}).get("available") and results[tf].get("direction") in {"ACHAT","VENTE"})
    data_factor = available / 5
    alignment_factor = alignment / 3
    confirmation_factor = confirmation / 2
    confluence_factor = np.mean([results[tf].get("confluence", {}).get("score", 0.0) for tf in results if results[tf].get("available")]) if available else 0
    confidence = min(100.0, abs(global_score) * 0.55 + alignment_factor*20 + confirmation_factor*15 + min(1.0, confluence_factor/2)*10)
    confidence *= 0.65 + 0.35*data_factor
    if decision == "ACHAT" and not lower_complete or decision == "VENTE" and not lower_complete:
        decision = "ATTENDRE"
        confidence = min(confidence, 65.0)
    if decision == "ATTENDRE":
        confidence = min(confidence, 70.0)
    elif decision == "AUCUN SETUP":
        confidence = min(confidence, 50.0)

    def reason_line():
        parts=[]
        for tf in ["D1","H4","H1","M15","M5"]:
            r=results.get(tf,{})
            if r.get("available"):
                parts.append(f"{tf} {r.get('direction','NEUTRE').lower()}")
            else:
                parts.append(f"{tf} indisponible")
        return ", ".join(parts) + "."

    if decision == "ACHAT":
        explanation = f"{reason_line()} Les timeframes de contexte et de confirmation sont alignés à la hausse. La confluence et le risque doivent encore valider le setup avant présentation finale."
    elif decision == "VENTE":
        explanation = f"{reason_line()} Les timeframes de contexte et de confirmation sont alignés à la baisse. La confluence et le risque doivent encore valider le setup avant présentation finale."
    elif decision == "ATTENDRE":
        explanation = f"{reason_line()} Le biais existe, mais la confirmation ou la confluence reste insuffisante. Le moteur refuse de forcer un signal."
    else:
        explanation = f"{reason_line()} Les conditions ne forment pas actuellement une configuration suffisamment convergente. Aucun setup n'est forcé."
    return {"timeframes": results, "score": global_score, "confidence": confidence, "decision": decision,
            "explanation": explanation, "available_count": available}
