"""Informational setup and risk calculations. No broker/execution code exists here."""

from __future__ import annotations
from typing import Dict, Optional
import math
from config import MAX_OPEN_RISK, MIN_RR, RISK_PER_TRADE, TP2_RR


def build_setup(price: float, atr: Optional[float], structure: Dict, direction: str, zones: Dict) -> Dict:
    if not (price > 0) or direction not in {"ACHAT", "VENTE"} or atr is None or not math.isfinite(atr) or atr <= 0:
        return {"valid": False, "reason": "Prix, direction ou ATR insuffisant."}
    swings = structure.get("swings", {})
    highs = swings.get("highs", [])
    lows = swings.get("lows", [])
    if direction == "ACHAT":
        structural = [x["price"] for x in lows[-3:]]
        sl = min([price - 1.2*atr] + [x - 0.15*atr for x in structural])
        risk_distance = price - sl
        obstacles = sorted(z["price"] for z in zones.get("resistances", []) if z["price"] > price)
        target_direction = 1
    else:
        structural = [x["price"] for x in highs[-3:]]
        sl = max([price + 1.2*atr] + [x + 0.15*atr for x in structural])
        risk_distance = sl - price
        obstacles = sorted((z["price"] for z in zones.get("supports", []) if z["price"] < price), reverse=True)
        target_direction = -1
    if risk_distance <= 0:
        return {"valid": False, "reason": "Distance Entry → SL invalide."}

    min_target = price + target_direction * MIN_RR * risk_distance
    if obstacles:
        first = obstacles[0]
        # An opposing zone between entry and the mandatory 2R target invalidates the setup.
        if (direction == "ACHAT" and first < min_target) or (direction == "VENTE" and first > min_target):
            return {"valid": False, "reason": "Une zone opposée importante bloque le R:R minimum de 1:2."}
    tp1 = min_target
    # Prefer a structural target when it remains at/above the requested R:R.
    if obstacles and ((direction == "ACHAT" and obstacles[0] >= min_target) or (direction == "VENTE" and obstacles[0] <= min_target)):
        tp1 = obstacles[0]
    min_tp2 = price + target_direction * TP2_RR * risk_distance
    farther = [x for x in obstacles[1:] if (x >= min_tp2 if direction == "ACHAT" else x <= min_tp2)]
    tp2 = farther[0] if farther else min_tp2
    rr1, rr2 = abs(tp1-price)/risk_distance, abs(tp2-price)/risk_distance
    if rr1 < MIN_RR:
        return {"valid": False, "reason": "Le R:R de TP1 est inférieur à 1:2."}
    return {"valid": True, "direction": direction, "entry": float(price), "sl": float(sl),
            "tp1": float(tp1), "tp2": float(tp2), "risk_distance": float(risk_distance),
            "rr1": float(rr1), "rr2": float(rr2)}


def position_size(capital: float, entry: float, sl: float, risk_fraction: float = RISK_PER_TRADE) -> Dict:
    if capital <= 0 or entry <= 0 or sl <= 0 or risk_fraction <= 0:
        return {"risk_amount": 0.0, "distance": 0.0, "units": 0.0}
    distance = abs(entry-sl)
    risk_amount = capital*risk_fraction
    units = risk_amount/distance if distance else 0.0
    return {"risk_amount": risk_amount, "distance": distance, "units": units}


def risk_summary(capital: float, entry: float, sl: float) -> Dict:
    sizing = position_size(capital, entry, sl)
    return {**sizing, "max_open_risk_amount": capital*MAX_OPEN_RISK, "risk_fraction": RISK_PER_TRADE,
            "max_open_risk_fraction": MAX_OPEN_RISK, "theoretical_loss": sizing["risk_amount"],
            "note": "Taille en unités théoriques de prix. Le lot broker réel dépend du contrat et de la valeur du point. Aucun ordre n'est envoyé."}
