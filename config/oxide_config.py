
"""Oxide molecular weights and stoichiometric configuration.

Molecular weights are expressed in g/mol.
Cation and oxygen counts refer to one mole of the oxide.
"""

OXIDE_CONFIG = {
    "SiO2": {
        "name": "Silicon dioxide",
        "molecular_weight": 60.0843,
        "cations": 1,
        "oxygens": 2,
    },
    "TiO2": {
        "name": "Titanium dioxide",
        "molecular_weight": 79.8660,
        "cations": 1,
        "oxygens": 2,
    },
    "Al2O3": {
        "name": "Aluminium oxide",
        "molecular_weight": 101.9613,
        "cations": 2,
        "oxygens": 3,
    },
    "Fe2O3": {
        "name": "Ferric oxide",
        "molecular_weight": 159.6882,
        "cations": 2,
        "oxygens": 3,
    },
    "FeO": {
        "name": "Ferrous oxide",
        "molecular_weight": 71.8440,
        "cations": 1,
        "oxygens": 1,
    },
    "MnO": {
        "name": "Manganese oxide",
        "molecular_weight": 70.9374,
        "cations": 1,
        "oxygens": 1,
    },
    "MgO": {
        "name": "Magnesium oxide",
        "molecular_weight": 40.3044,
        "cations": 1,
        "oxygens": 1,
    },
    "CaO": {
        "name": "Calcium oxide",
        "molecular_weight": 56.0774,
        "cations": 1,
        "oxygens": 1,
    },
    "Na2O": {
        "name": "Sodium oxide",
        "molecular_weight": 61.9789,
        "cations": 2,
        "oxygens": 1,
    },
    "K2O": {
        "name": "Potassium oxide",
        "molecular_weight": 94.1960,
        "cations": 2,
        "oxygens": 1,
    },
    "P2O5": {
        "name": "Phosphorus pentoxide",
        "molecular_weight": 141.9445,
        "cations": 2,
        "oxygens": 5,
    },
}

OXIDE_ORDER = list(OXIDE_CONFIG.keys())


def get_molecular_weight(oxide: str) -> float:
    """Return the molecular weight of a supported oxide."""
    if oxide not in OXIDE_CONFIG:
        raise ValueError(f"Unsupported oxide: {oxide}")

    return OXIDE_CONFIG[oxide]["molecular_weight"]


def get_supported_oxides() -> list[str]:
    """Return supported oxide names in calculation order."""
    return OXIDE_ORDER.copy()
