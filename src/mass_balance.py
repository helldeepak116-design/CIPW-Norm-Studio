from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


@dataclass
class MassBalanceResult:
    balanced: bool
    component_differences: dict[str, float]
    expected_silica_deficit: float
    max_non_silica_error: float
    silica_error: float
    tolerance: float
    status: str
    messages: list[str] = field(default_factory=list)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _add(target: dict[str, float], component: str, amount: float) -> None:
    target[component] = target.get(component, 0.0) + amount


def mineral_oxide_equivalents(
    minerals: dict[str, float],
    mg_fraction: float,
    fe_fraction: float,
    sulfur_component: str = "S",
    apatite_fluorine_amount: float = 0.0,
) -> dict[str, float]:
    """
    Convert normative mineral molecular amounts into oxide-equivalent
    component amounts.

    Mineral amounts follow the molecular conventions used by the
    project's Kelsey allocation and silica redistribution modules.
    """

    if sulfur_component not in {"S", "SO3"}:
        raise ValueError("sulfur_component must be S or SO3")

    mg_fraction = _number(mg_fraction, "mg_fraction")
    fe_fraction = _number(fe_fraction, "fe_fraction")

    if mg_fraction < 0 or fe_fraction < 0:
        raise ValueError("Mg and Fe fractions cannot be negative")

    if not math.isclose(
        mg_fraction + fe_fraction, 1.0, rel_tol=0.0, abs_tol=1e-8
    ):
        if mg_fraction == 0.0 and fe_fraction == 0.0:
            pass
        else:
            raise ValueError("Mg and Fe fractions must sum to 1")

    allowed = {
        "z", "ap", "fr", "hi", "th", "pr", "nc", "cc", "cm",
        "il", "or", "ks", "ab", "ac", "ns", "an", "c", "tn",
        "ru", "mt", "hm", "di", "wo", "hy", "q", "ol", "pf",
        "ne", "lc", "cs", "kp",
    }
    unknown = set(minerals) - allowed
    if unknown:
        raise ValueError(f"Unsupported normative minerals: {sorted(unknown)}")

    m: dict[str, float] = {}

    def amount(name: str) -> float:
        value = _number(minerals.get(name, 0.0), f"mineral {name}")
        if value < -1e-10:
            raise ValueError(f"Mineral {name} cannot be negative")
        return max(0.0, value)

    def add(name: str, component: str, coefficient: float = 1.0) -> None:
        _add(m, component, amount(name) * coefficient)

    # Accessory minerals and volatile-bearing components.
    add("z", "ZrO2")
    add("z", "SiO2")

    add("ap", "P2O5")
    add("ap", "CaO", 10.0 / 3.0)
    apatite_amount = amount("ap")
    apatite_fluorine_amount = _number(
        apatite_fluorine_amount, "apatite_fluorine_amount"
    )
    if apatite_fluorine_amount < 0:
        raise ValueError("apatite_fluorine_amount cannot be negative")
    if apatite_fluorine_amount > apatite_amount / 3.0 + 1e-10:
        raise ValueError(
            "Apatite fluorine exceeds the Kelsey (1965) Rule 5 limit"
        )
    _add(m, "F", apatite_fluorine_amount)

    add("fr", "CaO")
    add("fr", "F", 2.0)

    # Halite amount is recorded on the Na2O molecular-equivalent basis.
    add("hi", "Cl", 2.0)
    add("hi", "Na2O")

    add("th", "SO3")
    add("th", "Na2O")

    add("pr", "FeO")
    add("pr", sulfur_component, 2.0)

    add("nc", "CO2")
    add("nc", "Na2O")

    add("cc", "CO2")
    add("cc", "CaO")

    add("cm", "Cr2O3")
    add("cm", "FeO")

    # Major silicate and oxide minerals.
    add("il", "FeO")
    add("il", "TiO2")

    add("or", "K2O")
    add("or", "Al2O3")
    add("or", "SiO2", 6.0)

    add("ks", "K2O")
    add("ks", "SiO2")

    add("ab", "Na2O")
    add("ab", "Al2O3")
    add("ab", "SiO2", 6.0)

    add("ac", "Na2O")
    add("ac", "Fe2O3")
    add("ac", "SiO2", 4.0)

    add("ns", "Na2O")
    add("ns", "SiO2")

    add("an", "Al2O3")
    add("an", "CaO")
    add("an", "SiO2", 2.0)

    add("c", "Al2O3")

    add("tn", "CaO")
    add("tn", "TiO2")
    add("tn", "SiO2")

    add("ru", "TiO2")

    add("mt", "FeO")
    add("mt", "Fe2O3")

    add("hm", "Fe2O3")

    # Diopside and hypersthene contain the Mg-Fe ferromagnesian component.
    add("di", "CaO")
    add("di", "MgO", mg_fraction)
    add("di", "FeO", fe_fraction)
    add("di", "SiO2", 2.0)

    add("wo", "CaO")
    add("wo", "SiO2")

    add("hy", "MgO", mg_fraction)
    add("hy", "FeO", fe_fraction)
    add("hy", "SiO2")

    # Silica-deficiency redistribution products.
    add("ol", "MgO", 2.0 * mg_fraction)
    add("ol", "FeO", 2.0 * fe_fraction)
    add("ol", "SiO2")

    add("pf", "CaO")
    add("pf", "TiO2")

    add("ne", "Na2O")
    add("ne", "Al2O3")
    add("ne", "SiO2", 2.0)

    add("lc", "K2O")
    add("lc", "Al2O3")
    add("lc", "SiO2", 4.0)

    add("cs", "CaO", 2.0)
    add("cs", "SiO2")

    add("kp", "K2O")
    add("kp", "Al2O3")
    add("kp", "SiO2", 2.0)

    add("q", "SiO2")

    return m


def check_mass_balance(
    major_oxide_moles: dict[str, float],
    optional_component_moles: dict[str, float],
    provisional_result: Any,
    redistribution_result: Any | None = None,
    *,
    sulfur_basis: str = "none",
    tolerance: float = 1e-8,
) -> MassBalanceResult:
    """
    Independently check component conservation for the Kelsey workflow.

    Rules 2 and 3 are checked on the Kelsey-equivalent basis:
      FeO-equivalent = FeO + MnO + NiO
      CaO-equivalent = CaO + BaO + SrO

    Silica is checked against the expected remaining deficiency.
    Residual SiO2 is deliberately excluded because the provisional
    engine retains it while quartz (q) represents silica excess.
    """

    if sulfur_basis not in {"none", "S", "SO3"}:
        raise ValueError("sulfur_basis must be none, S, or SO3")

    tolerance = _number(tolerance, "tolerance")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    if not isinstance(major_oxide_moles, dict):
        raise TypeError("major_oxide_moles must be a dictionary")
    if not isinstance(optional_component_moles, dict):
        raise TypeError("optional_component_moles must be a dictionary")

    original: dict[str, float] = {}
    for name, value in {**major_oxide_moles, **optional_component_moles}.items():
        number = _number(value, name)
        if number < -tolerance:
            raise ValueError(f"{name} cannot be negative")
        original[name] = max(0.0, number)

    required_major = {
        "SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "MnO",
        "MgO", "CaO", "Na2O", "K2O", "P2O5",
    }
    required_optional = {
        "NiO", "BaO", "SrO", "ZrO2", "F", "Cl",
        "SO3", "S", "CO2", "Cr2O3",
    }

    if required_major - set(major_oxide_moles):
        raise ValueError(
            f"Missing major components: {sorted(required_major - set(major_oxide_moles))}"
        )
    if required_optional - set(optional_component_moles):
        raise ValueError(
            f"Missing optional components: {sorted(required_optional - set(optional_component_moles))}"
        )

    # Kelsey-equivalent input basis after Rules 2 and 3.
    initial = original.copy()
    initial["FeO"] += initial["MnO"] + initial["NiO"]
    initial["MnO"] = 0.0
    initial["NiO"] = 0.0

    initial["CaO"] += initial["BaO"] + initial["SrO"]
    initial["BaO"] = 0.0
    initial["SrO"] = 0.0

    if sulfur_basis == "S":
        if initial["S"] > tolerance and initial["SO3"] > tolerance:
            raise ValueError("Supply sulfur as either S or SO3, not both")
        sulfur_component = "S" if initial["S"] > tolerance else "SO3"
    else:
        sulfur_component = "S"

    if redistribution_result is None:
        minerals = _get(provisional_result, "minerals")
        expected_deficit = _number(
            _get(provisional_result, "silica_deficiency", 0.0),
            "silica_deficiency",
        )
    else:
        minerals = _get(redistribution_result, "minerals")
        expected_deficit = _number(
            _get(redistribution_result, "final_deficiency", 0.0),
            "final_deficiency",
        )

    residual = _get(provisional_result, "residual_oxides")

    if not isinstance(minerals, dict):
        raise TypeError("Result minerals must be a dictionary")
    if not isinstance(residual, dict):
        raise TypeError("Result residual_oxides must be a dictionary")
    if expected_deficit < -tolerance:
        raise ValueError("Expected silica deficit cannot be negative")

    mg_fraction = _number(_get(provisional_result, "mg_fraction"), "mg_fraction")
    fe_fraction = _number(_get(provisional_result, "fe_fraction"), "fe_fraction")

    mineral_components = mineral_oxide_equivalents(
        minerals,
        mg_fraction,
        fe_fraction,
        sulfur_component=sulfur_component,
        apatite_fluorine_amount=_number(
            _get(provisional_result, "apatite_fluorine_amount", 0.0),
            "apatite_fluorine_amount",
        ),
    )

    accounted = mineral_components.copy()

    # Residual components are retained; SiO2 is excluded to avoid
    # counting it twice alongside quartz and the normative silicates.
    for name, value in residual.items():
        if name == "SiO2":
            continue
        value = _number(value, f"residual {name}")
        _add(accounted, name, value)

    components = set(initial) | set(accounted)
    differences = {
        name: initial.get(name, 0.0) - accounted.get(name, 0.0)
        for name in sorted(components)
    }

    silica_difference = differences.get("SiO2", 0.0)
    silica_error = silica_difference + max(0.0, expected_deficit)

    non_silica = [
        abs(value)
        for name, value in differences.items()
        if name != "SiO2"
    ]
    max_non_silica_error = max(non_silica, default=0.0)

    messages: list[str] = []
    if max_non_silica_error > tolerance:
        messages.append("One or more non-silica components are not conserved.")
    if abs(silica_error) > tolerance:
        messages.append("Silica balance differs from the expected remaining deficiency.")
    if expected_deficit > tolerance:
        messages.append(
            f"Unresolved silica deficiency remains: {expected_deficit:.12g} molecular proportions."
        )

    balanced = (
        max_non_silica_error <= tolerance
        and abs(silica_error) <= tolerance
    )

    if not balanced:
        status = "IMBALANCE"
    elif expected_deficit > tolerance:
        status = "BALANCED_WITH_UNRESOLVED_SILICA_DEFICIENCY"
    else:
        status = "BALANCED"

    return MassBalanceResult(
        balanced=balanced,
        component_differences=differences,
        expected_silica_deficit=max(0.0, expected_deficit),
        max_non_silica_error=max_non_silica_error,
        silica_error=silica_error,
        tolerance=tolerance,
        status=status,
        messages=messages,
    )
