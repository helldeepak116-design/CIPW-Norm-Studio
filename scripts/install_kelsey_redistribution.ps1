
@'
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
    # 1 Or releases 2 SiO2 and forms 0.5 Lc.
    before = d
    converted = min(minerals["or"], d / 2.0)
    if converted > tolerance:
        minerals["or"] -= converted
        lc_formed = converted / 2.0
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
'@ | Set-Content -Encoding UTF8 .\src\kelsey_silica_deficiency.py

@'
import pytest

from src.kelsey_silica_deficiency import redistribute_silica


def test_rule_22_hypersthene_to_olivine():
    result = redistribute_silica({"hy": 1.0}, 0.2)
    assert result.minerals["hy"] == pytest.approx(0.6)
    assert result.minerals["ol"] == pytest.approx(0.2)
    assert result.final_deficiency == 0.0


def test_rule_23_sphene_to_perovskite():
    result = redistribute_silica({"tn": 1.0}, 0.3)
    assert result.minerals["tn"] == pytest.approx(0.7)
    assert result.minerals["pf"] == pytest.approx(0.3)


def test_rule_24_albite_to_nepheline():
    result = redistribute_silica({"ab": 1.0}, 2.0)
    assert result.minerals["ab"] == pytest.approx(0.5)
    assert result.minerals["ne"] == pytest.approx(0.5)


def test_rule_25_orthoclase_to_leucite_uses_half_mole_factor():
    result = redistribute_silica({"or": 1.0}, 1.0)
    assert result.minerals["or"] == pytest.approx(0.5)
    assert result.minerals["lc"] == pytest.approx(0.25)
    assert result.lc_prime_remaining == pytest.approx(0.25)


def test_rule_26_wollastonite_to_dicalcium_silicate():
    result = redistribute_silica({"wo": 1.0}, 0.2)
    assert result.minerals["wo"] == pytest.approx(0.6)
    assert result.minerals["cs"] == pytest.approx(0.2)


def test_rule_27_diopside_products():
    result = redistribute_silica({"di": 1.0}, 0.4)
    assert result.minerals["di"] == pytest.approx(0.6)
    assert result.minerals["cs"] == pytest.approx(0.2)
    assert result.minerals["ol"] == pytest.approx(0.2)


def test_rule_28_kaliophilite_uses_provisional_leucite_only():
    result = redistribute_silica({"or": 1.0, "lc": 0.4}, 2.0)
    # Rule 25 converts all Or: 0.5 Or -> 0.25 provisional Lc.
    # Rule 28 consumes only that 0.25, not the independent 0.4 input Lc.
    assert result.minerals["or"] == pytest.approx(0.0)
    assert result.minerals["kp"] == pytest.approx(0.25)
    assert result.minerals["lc"] == pytest.approx(0.4)
    assert result.lc_prime_remaining == pytest.approx(0.0)


def test_rule_order_is_preserved():
    result = redistribute_silica(
        {"hy": 0.2, "tn": 0.2, "ab": 0.2},
        1.0,
    )
    assert [step["rule"] for step in result.steps] == [22, 23, 24]


def test_unresolved_deficiency_is_reported():
    result = redistribute_silica({"hy": 0.1}, 1.0)
    assert result.status == "UNRESOLVED_DEFICIENCY"
    assert result.final_deficiency > 0


def test_zero_deficiency_does_not_change_minerals():
    result = redistribute_silica({"hy": 1.0, "ab": 0.5}, 0.0)
    assert result.minerals["hy"] == pytest.approx(1.0)
    assert result.minerals["ab"] == pytest.approx(0.5)
    assert result.steps == []


def test_negative_deficiency_rejected():
    with pytest.raises(ValueError):
        redistribute_silica({"hy": 1.0}, -0.1)


def test_negative_mineral_amount_rejected():
    with pytest.raises(ValueError):
        redistribute_silica({"hy": -1.0}, 0.1)


def test_non_finite_values_rejected():
    with pytest.raises(ValueError):
        redistribute_silica({"hy": float("nan")}, 0.1)
'@ | Set-Content -Encoding UTF8 .\tests\test_kelsey_silica_deficiency.py

Write-Host "`nCompiling corrected Kelsey redistribution module..." -ForegroundColor Cyan
python -m py_compile .\src\kelsey_silica_deficiency.py .\tests\test_kelsey_silica_deficiency.py
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

Write-Host "`nRunning corrected Kelsey Rules 22-28 tests..." -ForegroundColor Cyan
python -m pytest .\tests\test_kelsey_silica_deficiency.py -v
if ($LASTEXITCODE -ne 0) { throw "Kelsey redistribution tests failed." }

Write-Host "`nRunning complete project test suite..." -ForegroundColor Cyan
python -m pytest .\tests -q
if ($LASTEXITCODE -ne 0) { throw "Full project test suite failed." }

Write-Host "`nCorrected Kelsey module installed and tested." -ForegroundColor Green
