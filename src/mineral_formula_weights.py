"""Formula masses for Kelsey (1965) normative minerals.

The registry separates:
1. The normative mineral formula.
2. Formula mass in g/mol.
3. Conversion from the engine's stored mineral amount to formula units.

The stored amount is not always a formula-unit count. In particular:
- ap is stored on the P2O5 molecular-proportion basis.
- hi is stored on the Na2O-equivalent basis.

Ideal Kelsey equivalent-component conventions are retained for Mn/Ni
and Ba/Sr. These are not measured-element substitution corrections.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from config.oxide_config import OXIDE_CONFIG


ATOMIC_WEIGHTS = {
    "O": 15.999,
    "Na": 22.98976928,
    "Mg": 24.305,
    "Al": 26.9815385,
    "Si": 28.085,
    "P": 30.973761998,
    "S": 32.06,
    "Cl": 35.45,
    "C": 12.011,
    "K": 39.0983,
    "Ca": 40.078,
    "Ti": 47.867,
    "Cr": 51.9961,
    "Fe": 55.845,
    "Zr": 91.224,
    "Ni": 58.6934,
    "Ba": 137.327,
    "Sr": 87.62,
    "F": 18.998403163,
}

# Use the project's canonical oxide molecular weights for all
# oxide-equivalent mass calculations in composition-dependent minerals.
OXIDE_MASSES = {
    oxide: OXIDE_CONFIG[oxide]["molecular_weight"]
    for oxide in ("SiO2", "MgO", "FeO", "CaO", "P2O5")
}


@dataclass(frozen=True)
class MineralFormula:
    symbol: str
    name: str
    formula: str
    atoms: Mapping[str, float] | None
    formula_units_per_internal_amount: float = 1.0
    mg_fe_oxide_units: float = 0.0
    fixed_oxide_mass: float = 0.0


def _formula_mass(atoms: Mapping[str, float]) -> float:
    total = 0.0
    for element, count in atoms.items():
        if element not in ATOMIC_WEIGHTS:
            raise ValueError(f"Unknown element in formula: {element}")
        if not math.isfinite(float(count)) or count < 0:
            raise ValueError(f"Invalid atom count for {element}")
        total += ATOMIC_WEIGHTS[element] * count
    return total


def _entry(
    symbol: str,
    name: str,
    formula: str,
    atoms: Mapping[str, float],
    factor: float = 1.0,
) -> MineralFormula:
    return MineralFormula(
        symbol=symbol,
        name=name,
        formula=formula,
        atoms=dict(atoms),
        formula_units_per_internal_amount=factor,
    )


MINERAL_FORMULAE: dict[str, MineralFormula] = {
    "q": _entry("q", "Quartz", "SiO2", {"Si": 1, "O": 2}),
    "c": _entry("c", "Corundum", "Al2O3", {"Al": 2, "O": 3}),
    "z": _entry("z", "Zircon", "ZrSiO4", {"Zr": 1, "Si": 1, "O": 4}),
    "or": _entry(
        "or", "Orthoclase", "K2O.Al2O3.6SiO2",
        {"K": 2, "Al": 2, "Si": 6, "O": 16},
    ),
    "ab": _entry(
        "ab", "Albite", "Na2O.Al2O3.6SiO2",
        {"Na": 2, "Al": 2, "Si": 6, "O": 16},
    ),
    "an": _entry(
        "an", "Anorthite", "CaO.Al2O3.2SiO2",
        {"Ca": 1, "Al": 2, "Si": 2, "O": 8},
    ),
    "lc": _entry(
        "lc", "Leucite", "K2O.Al2O3.4SiO2",
        {"K": 2, "Al": 2, "Si": 4, "O": 12},
    ),
    "ne": _entry(
        "ne", "Nepheline", "Na2O.Al2O3.2SiO2",
        {"Na": 2, "Al": 2, "Si": 2, "O": 8},
    ),
    "kp": _entry(
        "kp", "Kaliophilite", "K2O.Al2O3.2SiO2",
        {"K": 2, "Al": 2, "Si": 2, "O": 8},
    ),
    # Kelsey stores hi = Cl/2 on the Na2O-equivalent basis.
    "hi": _entry("hi", "Halite", "NaCl", {"Na": 1, "Cl": 1}, 2.0),
    "th": _entry(
        "th", "Thenardite", "Na2SO4",
        {"Na": 2, "S": 1, "O": 4},
    ),
    "nc": _entry(
        "nc", "Sodium carbonate", "Na2CO3",
        {"Na": 2, "C": 1, "O": 3},
    ),
    "ac": _entry(
        "ac", "Acmite", "Na2O.Fe2O3.4SiO2",
        {"Na": 2, "Fe": 2, "Si": 4, "O": 12},
    ),
    "ns": _entry(
        "ns", "Sodium metasilicate", "Na2SiO3",
        {"Na": 2, "Si": 1, "O": 3},
    ),
    "ks": _entry(
        "ks", "Potassium metasilicate", "K2SiO3",
        {"K": 2, "Si": 1, "O": 3},
    ),
    "wo": _entry(
        "wo", "Wollastonite", "CaSiO3",
        {"Ca": 1, "Si": 1, "O": 3},
    ),
    "cs": _entry(
        "cs", "Dicalcium silicate", "Ca2SiO4",
        {"Ca": 2, "Si": 1, "O": 4},
    ),
    "mt": _entry(
        "mt", "Magnetite", "Fe3O4",
        {"Fe": 3, "O": 4},
    ),
    "cm": _entry(
        "cm", "Chromite", "FeCr2O4",
        {"Fe": 1, "Cr": 2, "O": 4},
    ),
    "il": _entry(
        "il", "Ilmenite", "FeTiO3",
        {"Fe": 1, "Ti": 1, "O": 3},
    ),
    "hm": _entry(
        "hm", "Hematite", "Fe2O3",
        {"Fe": 2, "O": 3},
    ),
    "tn": _entry(
        "tn", "Titanite (sphene)", "CaTiSiO5",
        {"Ca": 1, "Ti": 1, "Si": 1, "O": 5},
    ),
    "pf": _entry(
        "pf", "Perovskite", "CaTiO3",
        {"Ca": 1, "Ti": 1, "O": 3},
    ),
    "ru": _entry(
        "ru", "Rutile", "TiO2",
        {"Ti": 1, "O": 2},
    ),
    # Kelsey (1965) convention: 3CaO.P2O5.(1/3)CaF.
    # Internal amount is one P2O5 molecular proportion. The formula
    # mass varies with the amount of F actually allocated in Rule 5.
    "ap": MineralFormula(
        symbol="ap",
        name="Apatite (Kelsey 1965 convention)",
        formula="3CaO.P2O5.(1/3)CaF",
        atoms=None,
        formula_units_per_internal_amount=1.0,
        fixed_oxide_mass=(
            (10.0 / 3.0) * OXIDE_MASSES["CaO"]
            + OXIDE_MASSES["P2O5"]
        ),
    ),
    "fr": _entry(
        "fr", "Fluorite", "CaF2",
        {"Ca": 1, "F": 2},
    ),
    "pr": _entry(
        "pr", "Pyrite", "FeS2",
        {"Fe": 1, "S": 2},
    ),
    "cc": _entry(
        "cc", "Calcite", "CaCO3",
        {"Ca": 1, "C": 1, "O": 3},
    ),
}

# These minerals contain the Rule 19 residual Mg-Fe component.
# Their formula masses are calculated from the actual Mg and Fe fractions.
MINERAL_FORMULAE.update({
    "di": MineralFormula(
        symbol="di",
        name="Diopside",
        formula="Ca(Mg,Fe)Si2O6",
        atoms=None,
        mg_fe_oxide_units=1.0,
        fixed_oxide_mass=(
            OXIDE_MASSES["CaO"] + 2.0 * OXIDE_MASSES["SiO2"]
        ),
    ),
    "hy": MineralFormula(
        symbol="hy",
        name="Hypersthene",
        formula="(Mg,Fe)SiO3",
        atoms=None,
        mg_fe_oxide_units=1.0,
        fixed_oxide_mass=OXIDE_MASSES["SiO2"],
    ),
    "ol": MineralFormula(
        symbol="ol",
        name="Olivine",
        formula="(Mg,Fe)2SiO4",
        atoms=None,
        mg_fe_oxide_units=2.0,
        fixed_oxide_mass=OXIDE_MASSES["SiO2"],
    ),
})


def get_formula_weight(
    symbol: str,
    *,
    mg_fraction: float | None = None,
    fe_fraction: float | None = None,
    apatite_fluorine_fraction: float = 0.0,
) -> float:
    """Return mineral formula weight in g/mol.

    For diopside, hypersthene and olivine, Rule 19 Mg-Fe fractions
    are required and must sum to one.
    """
    if symbol not in MINERAL_FORMULAE:
        raise ValueError(f"Unsupported normative mineral: {symbol}")

    entry = MINERAL_FORMULAE[symbol]

    if symbol == "ap":
        if (
            isinstance(apatite_fluorine_fraction, bool)
            or not isinstance(apatite_fluorine_fraction, (int, float))
            or not math.isfinite(float(apatite_fluorine_fraction))
            or apatite_fluorine_fraction < 0
            or apatite_fluorine_fraction > (1.0 / 3.0) + 1e-10
        ):
            raise ValueError(
                "apatite_fluorine_fraction must be between 0 and 1/3"
            )
        # Kelsey apatite is represented on the P2O5 basis:
        # 10/3 CaO + P2O5, with each allocated F replacing one
        # CaO-equivalent component by CaF. Use the project's canonical
        # CaO molecular weight so the correction remains consistent
        # with OXIDE_MASSES even if it differs slightly from Ca + O.
        ca_f_minus_cao_mass = (
            ATOMIC_WEIGHTS["Ca"]
            + ATOMIC_WEIGHTS["F"]
            - OXIDE_MASSES["CaO"]
        )
        return (
            entry.fixed_oxide_mass
            + float(apatite_fluorine_fraction) * ca_f_minus_cao_mass
        )

    if apatite_fluorine_fraction != 0.0:
        raise ValueError(
            "apatite_fluorine_fraction is only valid for apatite"
        )

    # Quartz is represented by one SiO2 molecular proportion.
    # Use the canonical oxide molecular weight so conversion
    # and normative mineral mass calculations share one basis.
    if symbol == "q":
        return OXIDE_MASSES["SiO2"]

    if entry.atoms is not None:
        return _formula_mass(entry.atoms)

    if mg_fraction is None or fe_fraction is None:
        raise ValueError(
            f"{symbol} requires Rule 19 mg_fraction and fe_fraction"
        )

    for name, value in (
        ("mg_fraction", mg_fraction),
        ("fe_fraction", fe_fraction),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric")
        if not math.isfinite(float(value)) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative")

    if not math.isclose(
        float(mg_fraction) + float(fe_fraction),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-8,
    ):
        raise ValueError("Mg and Fe fractions must sum to 1")

    mean_mgo_feo_mass = (
        float(mg_fraction) * OXIDE_MASSES["MgO"]
        + float(fe_fraction) * OXIDE_MASSES["FeO"]
    )

    return (
        entry.fixed_oxide_mass
        + entry.mg_fe_oxide_units * mean_mgo_feo_mass
    )


def mineral_mass_from_amount(
    symbol: str,
    internal_amount: float,
    *,
    mg_fraction: float | None = None,
    fe_fraction: float | None = None,
    apatite_fluorine_fraction: float = 0.0,
) -> float:
    """Convert an engine mineral amount to mass in grams per mole basis."""
    if isinstance(internal_amount, bool) or not isinstance(
        internal_amount, (int, float)
    ):
        raise TypeError("internal_amount must be numeric")

    amount = float(internal_amount)
    if not math.isfinite(amount) or amount < 0:
        raise ValueError("internal_amount must be finite and non-negative")

    entry = MINERAL_FORMULAE.get(symbol)
    if entry is None:
        raise ValueError(f"Unsupported normative mineral: {symbol}")

    formula_weight = get_formula_weight(
        symbol,
        mg_fraction=mg_fraction,
        fe_fraction=fe_fraction,
        apatite_fluorine_fraction=apatite_fluorine_fraction,
    )

    return (
        amount
        * entry.formula_units_per_internal_amount
        * formula_weight
    )


def calculate_mineral_masses(
    minerals: Mapping[str, float],
    *,
    mg_fraction: float,
    fe_fraction: float,
    apatite_fluorine_amount: float = 0.0,
) -> dict[str, float]:
    """Calculate masses for a mineral dictionary without normalization."""
    if not isinstance(minerals, Mapping):
        raise TypeError("minerals must be a mapping")

    unknown = set(minerals) - set(MINERAL_FORMULAE)
    if unknown:
        raise ValueError(f"Unsupported normative minerals: {sorted(unknown)}")

    apatite_amount = float(minerals.get("ap", 0.0))
    if (
        isinstance(apatite_fluorine_amount, bool)
        or not isinstance(apatite_fluorine_amount, (int, float))
        or not math.isfinite(float(apatite_fluorine_amount))
        or apatite_fluorine_amount < 0
    ):
        raise ValueError("apatite_fluorine_amount must be finite and non-negative")
    if apatite_amount <= 0 and apatite_fluorine_amount > 0:
        raise ValueError("Apatite fluorine was supplied without normative apatite")
    if apatite_fluorine_amount > apatite_amount / 3.0 + 1e-10:
        raise ValueError(
            "Apatite fluorine exceeds the Kelsey (1965) Rule 5 limit"
        )
    apatite_fluorine_fraction = (
        float(apatite_fluorine_amount) / apatite_amount
        if apatite_amount > 0 else 0.0
    )

    masses = {}
    for symbol, amount in minerals.items():
        masses[symbol] = mineral_mass_from_amount(
            symbol,
            amount,
            mg_fraction=mg_fraction,
            fe_fraction=fe_fraction,
            apatite_fluorine_fraction=(
                apatite_fluorine_fraction if symbol == "ap" else 0.0
            ),
        )
    return masses
