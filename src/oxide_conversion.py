
"""Molecular conversion utilities for CIPW Norm calculations."""

from __future__ import annotations

import pandas as pd

from config.oxide_config import OXIDE_CONFIG, OXIDE_ORDER
from src.data_validation import validate_oxide_composition


def convert_oxides_to_molecular_proportions(
    composition: dict,
    *,
    volatile_free: bool = False,
) -> dict:
    """Convert oxide wt.% into molecular, cation and oxygen proportions.

    Molecular proportion = oxide wt.% / oxide molecular weight

    Cation proportion = molecular proportion * cations per oxide formula

    Oxygen proportion = molecular proportion * oxygens per oxide formula

    If volatile_free=True, the listed oxides are explicitly normalized
    to a total of 100 wt.% before molecular conversion. This does not
    add or infer volatile components.
    """
    validation = validate_oxide_composition(composition)

    if not validation["valid"]:
        raise ValueError(
            "Invalid oxide composition: "
            + "; ".join(validation["errors"])
        )

    values = {
        oxide: float(composition[oxide])
        for oxide in OXIDE_ORDER
    }

    original_total = sum(values.values())

    if original_total <= 0:
        raise ValueError("The sum of oxide concentrations must be positive.")

    if volatile_free:
        values = {
            oxide: value * 100.0 / original_total
            for oxide, value in values.items()
        }

    records = {}

    for oxide in OXIDE_ORDER:
        config = OXIDE_CONFIG[oxide]
        wt_percent = values[oxide]
        molecular_proportion = wt_percent / config["molecular_weight"]

        records[oxide] = {
            "wt_percent": wt_percent,
            "molecular_weight": config["molecular_weight"],
            "molecular_proportion": molecular_proportion,
            "cation_proportion": (
                molecular_proportion * config["cations"]
            ),
            "oxygen_proportion": (
                molecular_proportion * config["oxygens"]
            ),
        }

    result = pd.DataFrame.from_dict(records, orient="index")
    result.index.name = "oxide"

    return {
        "oxide_table": result,
        "original_analytical_total": original_total,
        "conversion_total": sum(values.values()),
        "volatile_free": volatile_free,
    }
