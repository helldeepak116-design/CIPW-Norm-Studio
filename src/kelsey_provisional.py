from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import math


MAJOR_OXIDES = (
    "SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO",
    "MnO", "MgO", "CaO", "Na2O", "K2O", "P2O5",
)

OPTIONAL_COMPONENTS = (
    "NiO", "BaO", "SrO", "ZrO2", "F", "Cl",
    "SO3", "S", "CO2", "Cr2O3",
)


class KelseyAllocationError(ValueError):
    """Raised when a Kelsey allocation cannot be completed safely."""


@dataclass
class ProvisionalResult:
    molecular_proportions: dict[str, float]
    residual_oxides: dict[str, float]
    minerals: dict[str, float]
    silica_requirement: float
    silica_excess: float
    silica_deficiency: float
    mg_fraction: float
    fe_fraction: float
    steps: list[dict[str, Any]] = field(default_factory=list)
    apatite_fluorine_amount: float = 0.0
    method: str = "Kelsey (1965), provisional allocation Rules 1-21"
    status: str = "PROVISIONAL_COMPLETE"
    completion_stage: str = "PROVISIONAL_RULES_1_21"


def calculate_kelsey_provisional(
    major_oxide_moles: dict[str, float],
    optional_component_moles: dict[str, float],
    *,
    sulfur_basis: str = "none",
    carbonate_mode: str = "none",
    tolerance: float = 1e-10,
) -> ProvisionalResult:
    """
    Provisional allocation based on Kelsey (1965), Rules 1-21.

    Inputs are molecular proportions, not weight percentages.
    Convert analytical weight percentages to molecular proportions
    before calling this function.

    Every optional component must be explicitly supplied, including
    zero when confirmed absent.

    sulfur_basis:
        "none" - no sulfur allocation
        "SO3"  - Rule 8, thenardite
        "S"    - Rule 9, pyrite

    carbonate_mode:
        "none"
        "cancrinite" - Rule 10a
        "calcite"    - Rule 10b

    The function returns molecular amounts. It does not calculate
    final normative weight percentages or execute Rules 22-28.
    """

    if sulfur_basis not in {"none", "SO3", "S"}:
        raise KelseyAllocationError(
            "sulfur_basis must be none, SO3, or S"
        )

    if carbonate_mode not in {"none", "cancrinite", "calcite"}:
        raise KelseyAllocationError(
            "carbonate_mode must be none, cancrinite, or calcite"
        )

    if not isinstance(major_oxide_moles, dict):
        raise KelseyAllocationError("Major oxide input must be a dictionary")

    if not isinstance(optional_component_moles, dict):
        raise KelseyAllocationError(
            "Optional components must be supplied explicitly as a dictionary"
        )

    missing_major = set(MAJOR_OXIDES) - set(major_oxide_moles)
    extra_major = set(major_oxide_moles) - set(MAJOR_OXIDES)

    if missing_major:
        raise KelseyAllocationError(
            f"Missing major oxides: {sorted(missing_major)}"
        )
    if extra_major:
        raise KelseyAllocationError(
            f"Unsupported major oxides: {sorted(extra_major)}"
        )

    missing_optional = set(OPTIONAL_COMPONENTS) - set(optional_component_moles)
    extra_optional = set(optional_component_moles) - set(OPTIONAL_COMPONENTS)

    if missing_optional:
        raise KelseyAllocationError(
            "Optional components must be explicit, including zero values. "
            f"Missing: {sorted(missing_optional)}"
        )
    if extra_optional:
        raise KelseyAllocationError(
            f"Unsupported optional components: {sorted(extra_optional)}"
        )

    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool):
        raise KelseyAllocationError("Tolerance must be numeric")
    if not math.isfinite(float(tolerance)) or tolerance <= 0:
        raise KelseyAllocationError("Tolerance must be finite and positive")

    oxides: dict[str, float] = {}

    for name, value in {
        **major_oxide_moles,
        **optional_component_moles,
    }.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise KelseyAllocationError(f"{name} must be numeric")
        value = float(value)
        if not math.isfinite(value) or value < -tolerance:
            raise KelseyAllocationError(
                f"{name} must be finite and non-negative"
            )
        oxides[name] = max(0.0, value)

    original = oxides.copy()
    minerals: dict[str, float] = {}
    steps: list[dict[str, Any]] = []
    y = 0.0

    def take(name: str, amount: float, rule: int, product: str) -> None:
        nonlocal oxides

        amount = max(0.0, float(amount))
        available = oxides[name]

        if amount > available + tolerance:
            raise KelseyAllocationError(
                f"Rule {rule}: insufficient {name}; "
                f"requires {amount:.12g}, available {available:.12g}"
            )

        amount = min(amount, available)
        oxides[name] = max(0.0, available - amount)

        if product:
            minerals[product] = minerals.get(product, 0.0) + amount

        steps.append({
            "rule": rule,
            "component": name,
            "amount_removed": amount,
            "mineral": product or None,
            "residual": oxides[name],
        })

    def add_mineral(name: str, amount: float, rule: int) -> None:
        minerals[name] = minerals.get(name, 0.0) + amount
        steps.append({
            "rule": rule,
            "mineral": name,
            "amount_formed": amount,
        })

    def add_silica(rule: int, amount: float, reason: str) -> None:
        nonlocal y
        y += amount
        steps.append({
            "rule": rule,
            "silica_added_to_Y": amount,
            "reason": reason,
            "Y": y,
        })

    def allocate_pair(
        first: str,
        second: str,
        mineral: str,
        rule: int,
    ) -> float:
        amount = min(oxides[first], oxides[second])
        take(first, amount, rule, "")
        take(second, amount, rule, "")
        add_mineral(mineral, amount, rule)
        return amount

    # Rule 1: inputs are already expressed as molecular proportions.
    steps.append({
        "rule": 1,
        "description": "Molecular proportions supplied to allocation engine",
        "components": len(oxides),
    })

    # Rule 2: MnO + NiO are added to FeO.
    feo_original = oxides["FeO"]
    mno_added = oxides["MnO"]
    nio_added = oxides["NiO"]
    feo_equivalent_added = mno_added + nio_added

    oxides["FeO"] += feo_equivalent_added

    steps.append({
        "rule": 2,
        "description": "MnO and NiO combined with FeO",
        "FeO_original": feo_original,
        "MnO_added": mno_added,
        "NiO_added": nio_added,
        "FeO_equivalent_added": feo_equivalent_added,
        "FeO_after_adjustment": oxides["FeO"],
    })

    oxides["MnO"] = 0.0
    oxides["NiO"] = 0.0

    # Rule 3: BaO + SrO are added to CaO.
    cao_original = oxides["CaO"]
    bao_added = oxides["BaO"]
    sro_added = oxides["SrO"]
    cao_equivalent_added = bao_added + sro_added

    oxides["CaO"] += cao_equivalent_added

    steps.append({
        "rule": 3,
        "description": "BaO and SrO combined with CaO",
        "CaO_original": cao_original,
        "BaO_added": bao_added,
        "SrO_added": sro_added,
        "CaO_equivalent_added": cao_equivalent_added,
        "CaO_after_adjustment": oxides["CaO"],
    })

    oxides["BaO"] = 0.0
    oxides["SrO"] = 0.0

    # Rule 4: zircon.
    z = oxides["ZrO2"]
    minerals["z"] = z
    oxides["ZrO2"] = 0.0
    add_silica(4, z, "ZrO2 allocated to zircon")

    # Rule 5: apatite using the original Kelsey (1965) convention.
    # Kelsey expresses apatite as 3CaO.P2O5.(1/3)CaF:
    #   ap = P2O5
    #   CaO equivalent consumed = (10/3) * ap
    #   maximum F allocated to apatite = ap / 3
    # Apatite allocation is controlled by P2O5 and CaO, not by F.
    # Any F beyond the amount actually assigned to apatite proceeds
    # to Rule 6 (fluorite).
    p2o5_available = oxides["P2O5"]
    f_available = oxides["F"]

    ap = p2o5_available
    ca_for_apatite = (10.0 / 3.0) * ap
    f_required_for_apatite = ap / 3.0
    f_used_for_apatite = min(f_available, f_required_for_apatite)

    if ca_for_apatite > oxides["CaO"] + tolerance:
        raise KelseyAllocationError(
            "Rule 5: insufficient CaO for the Kelsey apatite allocation"
        )

    take("P2O5", ap, 5, "ap")
    take("CaO", ca_for_apatite, 5, "")
    take("F", f_used_for_apatite, 5, "")

    steps.append({
        "rule": 5,
        "description": "Kelsey apatite allocation",
        "apatite": ap,
        "P2O5_allocated": ap,
        "P2O5_unallocated": oxides["P2O5"],
        "CaO_used": ca_for_apatite,
        "F_required": f_required_for_apatite,
        "F_used": f_used_for_apatite,
        "F_unallocated_for_rule_6": oxides["F"],
    })

    # Rule 6: fluorite from remaining fluorine.
    fr = oxides["F"] / 2.0
    if fr > oxides["CaO"] + tolerance:
        raise KelseyAllocationError(
            "Rule 6: insufficient CaO for remaining fluorine"
        )
    take("F", 2.0 * fr, 6, "")
    take("CaO", fr, 6, "fr")

    # Rule 7: halite.
    hi = oxides["Cl"]
    na_for_halite = hi / 2.0
    if na_for_halite > oxides["Na2O"] + tolerance:
        raise KelseyAllocationError(
            "Rule 7: insufficient Na2O for halite"
        )
    take("Cl", hi, 7, "")
    take("Na2O", na_for_halite, 7, "hi")

    # Rule 8: thenardite when sulphur is reported as SO3.
    if sulfur_basis == "SO3":
        th = oxides["SO3"]
        if th > oxides["Na2O"] + tolerance:
            raise KelseyAllocationError(
                "Rule 8: insufficient Na2O for thenardite"
            )
        take("SO3", th, 8, "th")
        take("Na2O", th, 8, "")

    # Rule 9: pyrite when sulphur is reported as S.
    if sulfur_basis == "S":
        if oxides["S"] > tolerance and oxides["SO3"] > tolerance:
            raise KelseyAllocationError(
                "Rule 9: supply sulfur as either S or SO3, not both"
            )

        sulfur_component = "S" if oxides["S"] > tolerance else "SO3"
        sulfur_amount = oxides[sulfur_component]
        pr = sulfur_amount / 2.0

        if pr > oxides["FeO"] + tolerance:
            raise KelseyAllocationError(
                "Rule 9: insufficient FeO for pyrite"
            )

        take(sulfur_component, sulfur_amount, 9, "")
        take("FeO", pr, 9, "pr")

    # Rule 10: carbonate treatment is a user-selected branch.
    if carbonate_mode == "cancrinite":
        nc = oxides["CO2"]
        if nc > oxides["Na2O"] + tolerance:
            raise KelseyAllocationError(
                "Rule 10a: insufficient Na2O for cancrinite"
            )
        take("CO2", nc, 10, "nc")
        take("Na2O", nc, 10, "")

    elif carbonate_mode == "calcite":
        cc = oxides["CO2"]
        if cc > oxides["CaO"] + tolerance:
            raise KelseyAllocationError(
                "Rule 10b: insufficient CaO for calcite"
            )
        take("CO2", cc, 10, "cc")
        take("CaO", cc, 10, "")

    # Rule 11: chromite.
    cm = oxides["Cr2O3"]
    if cm > oxides["FeO"] + tolerance:
        raise KelseyAllocationError(
            "Rule 11: insufficient FeO for chromite"
        )
    take("Cr2O3", cm, 11, "cm")
    take("FeO", cm, 11, "")

    # Rule 12: ilmenite.
    il = allocate_pair("FeO", "TiO2", "il", 12)

    # Rule 13: orthoclase and potassium metasilicate.
    or_amount = min(oxides["Al2O3"], oxides["K2O"])
    take("Al2O3", or_amount, 13, "")
    take("K2O", or_amount, 13, "")
    add_mineral("or", or_amount, 13)
    add_silica(13, 6.0 * or_amount, "Orthoclase")

    ks = oxides["K2O"]
    if ks > 0:
        take("K2O", ks, 13, "ks")
        add_silica(13, ks, "Potassium metasilicate")

    # Rule 14: albite.
    ab = min(oxides["Al2O3"], oxides["Na2O"])
    take("Al2O3", ab, 14, "")
    take("Na2O", ab, 14, "")
    add_mineral("ab", ab, 14)
    add_silica(14, 6.0 * ab, "Albite")

    # Rule 15: acmite and sodium metasilicate.
    ac = min(oxides["Na2O"], oxides["Fe2O3"])
    take("Na2O", ac, 15, "")
    take("Fe2O3", ac, 15, "")
    add_mineral("ac", ac, 15)
    add_silica(15, 4.0 * ac, "Acmite")

    ns = oxides["Na2O"]
    if ns > 0:
        take("Na2O", ns, 15, "ns")
        add_silica(15, ns, "Sodium metasilicate")

    # Rule 16: anorthite and corundum.
    an = min(oxides["Al2O3"], oxides["CaO"])
    take("Al2O3", an, 16, "")
    take("CaO", an, 16, "")
    add_mineral("an", an, 16)
    add_silica(16, 2.0 * an, "Anorthite")

    cor = oxides["Al2O3"]
    if cor > 0:
        take("Al2O3", cor, 16, "c")

    # Rule 17: sphene and rutile.
    tn = min(oxides["CaO"], oxides["TiO2"])
    take("CaO", tn, 17, "")
    take("TiO2", tn, 17, "")
    add_mineral("tn", tn, 17)
    add_silica(17, tn, "Sphene")

    ru = oxides["TiO2"]
    if ru > 0:
        take("TiO2", ru, 17, "ru")

    # Rule 18: magnetite and hematite.
    mt = min(oxides["FeO"], oxides["Fe2O3"])
    take("FeO", mt, 18, "")
    take("Fe2O3", mt, 18, "")
    add_mineral("mt", mt, 18)

    hm = oxides["Fe2O3"]
    if hm > 0:
        take("Fe2O3", hm, 18, "hm")

    # Rule 19: Mg-Fe proportions in the ferromagnesian component.
    mg = oxides["MgO"]
    fe = oxides["FeO"]
    mgfe = mg + fe

    mg_fraction = mg / mgfe if mgfe > tolerance else 0.0
    fe_fraction = fe / mgfe if mgfe > tolerance else 0.0

    steps.append({
        "rule": 19,
        "description": "Mg-Fe proportions in ferromagnesian component",
        "MgO": mg,
        "FeO": fe,
        "MgFe_total": mgfe,
        "Mg_fraction": mg_fraction,
        "Fe_fraction": fe_fraction,
    })

    # Rule 20: provisional diopside, wollastonite or hypersthene.
    ca = oxides["CaO"]
    di = min(ca, mgfe)
    add_mineral("di", di, 20)

    ca_remaining = max(0.0, ca - di)
    mgfe_remaining = max(0.0, mgfe - di)

    wo = ca_remaining
    hy = mgfe_remaining

    if wo > 0:
        add_mineral("wo", wo, 20)
    if hy > 0:
        add_mineral("hy", hy, 20)

    oxides["CaO"] = 0.0
    oxides["MgO"] = 0.0
    oxides["FeO"] = 0.0

    add_silica(20, 2.0 * di, "Diopside")
    add_silica(20, wo, "Wollastonite")
    add_silica(20, hy, "Hypersthene")

    # Rule 21: silica excess or deficiency.
    silica = oxides["SiO2"]
    excess = max(0.0, silica - y)
    deficiency = max(0.0, y - silica)

    if excess > tolerance:
        minerals["q"] = excess
        status = "SILICA_EXCESS"
    elif deficiency > tolerance:
        status = "SILICA_DEFICIENCY"
    else:
        excess = 0.0
        deficiency = 0.0
        status = "SILICA_BALANCED"

    steps.append({
        "rule": 21,
        "SiO2_available": silica,
        "Y": y,
        "silica_excess": excess,
        "silica_deficiency": deficiency,
        "status": status,
    })

    # Keep residual oxide values non-negative within tolerance.
    for name, value in oxides.items():
        if value < -tolerance:
            raise KelseyAllocationError(
                f"Negative residual {name}: {value}"
            )
        if abs(value) <= tolerance:
            oxides[name] = 0.0

    return ProvisionalResult(
        molecular_proportions=original,
        residual_oxides=oxides,
        minerals=minerals,
        silica_requirement=y,
        silica_excess=excess,
        silica_deficiency=deficiency,
        mg_fraction=mg_fraction,
        fe_fraction=fe_fraction,
        steps=steps,
        apatite_fluorine_amount=f_used_for_apatite,
        status=status,
    )
