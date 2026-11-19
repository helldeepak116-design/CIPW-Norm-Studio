from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


@dataclass
class RedistributionResult:
    minerals: dict[str, float]
    initial_deficiency: float
    final_deficiency: float
    lc_prime_remaining: float
    steps: list[dict[str, Any]] = field(default_factory=list)
    status: str = "COMPLETED"


def redistribute_silica(
    provisional: dict[str, float],
    deficiency: float,
    tolerance: float = 1e-10,
) -> RedistributionResult:
    """
    Kelsey (1965), silica-deficiency redistribution, Rules 22-28.

    All mineral amounts and silica deficiency are molecular proportions.
    Rules are applied in the original prescribed order.

    The input 'lc' amount, if supplied, is retained independently.
    Rule 25 generates provisional leucite (lc_prime); Rule 28 can
    consume only this provisional leucite.

    This module does not calculate Rules 1-21.
    """

    if not isinstance(provisional, dict):
        raise TypeError("provisional must be a dictionary")

    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool):
        raise TypeError("tolerance must be numeric")
    if not math.isfinite(float(tolerance)) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")

    minerals: dict[str, float] = {}
    for name, value in provisional.items():
        if not isinstance(name, str):
            raise TypeError("Mineral names must be strings")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if value < -tolerance:
            raise ValueError(f"{name} cannot be negative")
        minerals[name] = max(0.0, value)

    for name in ("hy", "tn", "ab", "or", "wo", "di", "lc"):
        minerals.setdefault(name, 0.0)

    if isinstance(deficiency, bool) or not isinstance(deficiency, (int, float)):
        raise TypeError("deficiency must be numeric")
    deficiency = float(deficiency)
    if not math.isfinite(deficiency):
        raise ValueError("deficiency must be finite")
    if deficiency < -tolerance:
        raise ValueError("Silica deficiency cannot be negative")

    initial = max(0.0, deficiency)
    d = initial
    lc_prime = 0.0
    steps: list[dict[str, Any]] = []

    def record(
        rule: int,
        reaction: str,
        before: float,
        converted: float,
        after: float,
        products: dict[str, float],
    ) -> None:
        steps.append({
            "rule": rule,
            "reaction": reaction,
            "deficiency_before": before,
            "provisional_amount_converted": converted,
            "deficiency_after": after,
            "products_formed": products.copy(),
        })

    # Rule 22: Hypersthene -> Olivine.
    # 1 Hy releases 0.5 SiO2 and forms 0.5 Ol.
    before = d
    converted = min(minerals["hy"], 2.0 * d)
    if converted > tolerance:
        ol = converted / 2.0
        minerals["hy"] -= converted
        minerals["ol"] = minerals.get("ol", 0.0) + ol
        d = max(0.0, d - converted / 2.0)
        record(22, "hypersthene -> olivine", before, converted, d, {"ol": ol})

    # Rule 23: Sphene -> Perovskite.
    # 1 Tn releases 1 SiO2 and forms 1 Pf.
    before = d
    converted = min(minerals["tn"], d)
    if converted > tolerance:
        minerals["tn"] -= converted
        minerals["pf"] = minerals.get("pf", 0.0) + converted
        d = max(0.0, d - converted)
        record(23, "sphene -> perovskite", before, converted, d, {"pf": converted})

    # Rule 24: Albite -> Nepheline.
    # 1 Ab releases 4 SiO2 and forms 1 Ne.
    before = d
    converted = min(minerals["ab"], d / 4.0)
    if converted > tolerance:
        minerals["ab"] -= converted
        minerals["ne"] = minerals.get("ne", 0.0) + converted
        d = max(0.0, d - 4.0 * converted)
        record(24, "albite -> nepheline", before, converted, d, {"ne": converted})

    # Rule 25: Orthoclase -> Leucite.
    # 1 Or releases 2 SiO2 and forms 1 Lc.
    before = d
    converted = min(minerals["or"], d / 2.0)
    if converted > tolerance:
        minerals["or"] -= converted
        lc_formed = converted
        lc_prime += lc_formed
        minerals["lc"] += lc_formed
        d = max(0.0, d - 2.0 * converted)
        record(
            25,
            "orthoclase -> provisional leucite",
            before,
            converted,
            d,
            {"lc_prime": lc_formed},
        )

    # Rule 26: Wollastonite -> Dicalcium silicate.
    # 1 Wo releases 0.5 SiO2 and forms 0.5 Cs.
    before = d
    converted = min(minerals["wo"], 2.0 * d)
    if converted > tolerance:
        cs = converted / 2.0
        minerals["wo"] -= converted
        minerals["cs"] = minerals.get("cs", 0.0) + cs
        d = max(0.0, d - converted / 2.0)
        record(
            26,
            "wollastonite -> dicalcium silicate",
            before,
            converted,
            d,
            {"cs": cs},
        )

    # Rule 27: Diopside -> Dicalcium silicate + Olivine.
    # 1 Di releases 1 SiO2 and forms 0.5 Cs + 0.5 Ol.
    before = d
    converted = min(minerals["di"], d)
    if converted > tolerance:
        product_amount = converted / 2.0
        minerals["di"] -= converted
        minerals["cs"] = minerals.get("cs", 0.0) + product_amount
        minerals["ol"] = minerals.get("ol", 0.0) + product_amount
        d = max(0.0, d - converted)
        record(
            27,
            "diopside -> dicalcium silicate + olivine",
            before,
            converted,
            d,
            {"cs": product_amount, "ol": product_amount},
        )

    # Rule 28: Provisional Leucite -> Kaliophilite.
    # 1 Lc releases 2 SiO2 and forms 1 Kp.
    # Only leucite generated by Rule 25 is eligible.
    before = d
    converted = min(lc_prime, d / 2.0)
    if converted > tolerance:
        lc_prime -= converted
        minerals["lc"] -= converted
        minerals["kp"] = minerals.get("kp", 0.0) + converted
        d = max(0.0, d - 2.0 * converted)
        record(
            28,
            "provisional leucite -> kaliophilite",
            before,
            converted,
            d,
            {"kp": converted},
        )

    if abs(d) <= tolerance:
        d = 0.0
    if abs(lc_prime) <= tolerance:
        lc_prime = 0.0

    return RedistributionResult(
        minerals=minerals,
        initial_deficiency=initial,
        final_deficiency=d,
        lc_prime_remaining=lc_prime,
        steps=steps,
        status="COMPLETED" if d == 0.0 else "UNRESOLVED_DEFICIENCY",
    )



