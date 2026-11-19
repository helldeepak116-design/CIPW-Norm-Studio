# CIPW Norm Studio

**A scientific application for CIPW normative mineral calculation, interpretation, and visualization.**

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67.0-FF4B4B.svg)](https://streamlit.io/)
[![Method](https://img.shields.io/badge/Method-Kelsey%20%281965%29-green.svg)](https://doi.org/10.1180/minmag.1965.034.268.23)
[![Tests](https://img.shields.io/badge/Tests-331%20recorded-brightgreen.svg)]()

---

## Overview

**CIPW Norm Studio** is a Python-based scientific software project designed to calculate and interpret normative mineral assemblages from whole-rock major-element geochemical compositions.

The project implements the classical CIPW normative calculation procedure following **Kelsey (1965)**, with measured ferrous iron (FeO) and ferric iron (Fe₂O₃) handled independently.

The objective is to provide a transparent and reproducible environment for geochemical calculations, including calculation intermediates, mineral molecular proportions, normative mineral masses, mass-balance checks, and scientific validation.

> **Development status:** The calculation engine, supporting modules, and regression tests are under active development. The current Streamlit landing page is an initial interface and does not yet execute normative calculations directly.

## Scientific methodology

### Calculation procedure

The selected calculation method is:

**Classical CIPW Norm — Kelsey (1965)**

The calculation framework uses major-element oxide compositions expressed in weight percent.

Supported major oxides:

| Oxide | Chemical formula |
|---|---|
| Silica | SiO₂ |
| Titanium dioxide | TiO₂ |
| Aluminium oxide | Al₂O₃ |
| Ferric oxide | Fe₂O₃ |
| Ferrous oxide | FeO |
| Manganese oxide | MnO |
| Magnesium oxide | MgO |
| Calcium oxide | CaO |
| Sodium oxide | Na₂O |
| Potassium oxide | K₂O |
| Phosphorus pentoxide | P₂O₅ |

### Iron handling

The project uses measured iron values:

- FeO is retained independently.
- Fe₂O₃ is retained independently.
- No automatic iron oxidation ratio is silently imposed.

This distinction is important because iron allocation affects normative mineral proportions.

### Calculation transparency

The implementation is designed to retain calculation intermediates rather than exposing only final normative mineral percentages.

The project also includes component mass-balance checks and numerical validation.

### Optional components

Optional geochemical components are represented using explicit measurement-status records.

The distinction between the following states is important:

- `measured`: a measured concentration is supplied.
- `measured_zero`: the component was measured and reported as zero.
- `not_measured`: no measurement is available.

Unmeasured components must not automatically be interpreted as measured zero. Exploratory calculations that assume unmeasured components are absent must be identified as conditional.

## Technology stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Application framework | Streamlit |
| Numerical computation | NumPy, SciPy |
| Data processing | Pandas |
| Visualization | Plotly, Matplotlib |
| Spreadsheet support | OpenPyXL |
| PDF reporting | ReportLab |
| Automated testing | Pytest |

## Project structure

```text
CIPW-Norm-Studio/
│
├── app.py
├── requirements.txt
├── .gitignore
├── .gitattributes
│
├── config/
│   ├── __init__.py
│   ├── oxide_config.py
│   └── settings.py
│
├── docs/
│   ├── REFERENCE_BENCHMARK_REGISTRY.md
│   └── SCIENTIFIC_VALIDATION_REPORT.md
│
├── pages/
│   └── 01_Geochemical_Input.py
│
├── scripts/
│   ├── audit_apatite_fluorine.py
│   ├── run_kelsey_bostonite_validation.py
│   ├── run_reference_validation.py
│   └── run_tholeiitic_basalt_diagnostic.py
│
├── src/
│   ├── cipw_engine.py
│   ├── data_validation.py
│   ├── kelsey_provisional.py
│   ├── kelsey_silica_deficiency.py
│   ├── mass_balance.py
│   ├── mineral_formula_weights.py
│   ├── norm_calculation.py
│   ├── optional_components.py
│   └── oxide_conversion.py
│
└── tests/
    ├── test_cipw_engine.py
    ├── test_formula_stoichiometry_audit.py
    ├── test_kelsey_bostonite_regression.py
    ├── test_kelsey_provisional.py
    ├── test_kelsey_rule5_rule9.py
    ├── test_kelsey_silica_deficiency.py
    ├── test_mass_balance.py
    ├── test_mass_balance_integration.py
    ├── test_mineral_formula_weights.py
    ├── test_mineral_mass_validation.py
    ├── test_norm_calculation.py
    ├── test_optional_components.py
    ├── test_oxide_conversion.py
    ├── test_oxide_mass_consistency.py
    ├── test_reference_benchmarks.py
    ├── test_reference_benchmarks_extended.py
    └── test_winter_basalt_norm_regression.py
```

## Installation

### Prerequisites

- Python installed and available through the command line.
- Git.
- Windows PowerShell, Command Prompt, or a compatible terminal.

### 1. Clone the repository

```powershell
git clone https://github.com/helldeepak116-design/CIPW-Norm-Studio.git

cd CIPW-Norm-Studio
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

### 5. Launch the application

```powershell
streamlit run app.py
```

The application will be available at the local address printed by Streamlit, typically:

```text
http://localhost:8501
```

**Note:** The current landing page is an initial interface. It does not yet provide end-to-end normative calculation through the graphical interface.

## Scientific validation

Scientific validation is treated as a distinct part of the development process.

The project maintains a reference benchmark registry and a detailed validation report:

- `docs/SCIENTIFIC_VALIDATION_REPORT.md`
- `docs/REFERENCE_BENCHMARK_REGISTRY.md`

### Current validation evidence

| Benchmark | Evidence category | Recorded result |
|---|---|---|
| Kelsey (1965) Bostonite, Table III | Rounded published worked-example comparison | 3 dedicated regression tests passed |
| Winter (2014) Mid-Atlantic Ridge tholeiitic basalt | Modified-CIPW diagnostic comparison | 2 dedicated regression tests passed |
| Idaho Batholith, sample 134.15 | Different-procedure reference comparison | Existing reference tests passed |
| Apatite-fluorine audit | Synthetic rule and formula-mass audit | Low-F and excess-F cases passed |
| Internal mass balance | Component-conservation audit | Recorded benchmark runs balanced |

### Kelsey Bostonite benchmark

The Bostonite example from Kelsey (1965), Table III, is the principal published worked-example comparison for the selected calculation procedure.

The recorded implementation results include:

- Initial silica deficiency.
- Provisional hypersthene.
- Provisional albite.
- Final normative mineral molecular amounts.

All eight final published mineral molecular amounts were within an absolute tolerance of 0.001 in the recorded comparison.

**Important qualification:** MnO and P₂O₅ were not reported in the source analysis and were explicitly assumed zero. Optional components were recorded as unmeasured and conditionally assumed absent. Historical published values are rounded to three decimal places.

### Other reference comparisons

The Winter (2014) basalt example uses a simplified or modified CIPW procedure. It is a diagnostic comparison, not proof of exact Kelsey equivalence.

The Idaho Batholith exercise uses Hyndman's procedure. It is useful for selected oxide-conversion and comparative checks, not as a direct Kelsey acceptance benchmark.

### Automated tests

Run the complete test suite:

```powershell
python -m pytest -q
```

Run the Kelsey Bostonite regression tests:

```powershell
python -m pytest -q tests/test_kelsey_bostonite_regression.py
```

Run the Winter basalt diagnostic tests:

```powershell
python -m pytest -q tests/test_winter_basalt_norm_regression.py
```

Run the validation scripts:

```powershell
python -m scripts.run_kelsey_bostonite_validation

python -m scripts.run_tholeiitic_basalt_diagnostic

python -m scripts.audit_apatite_fluorine
```

**Recorded baseline:** 331 passing automated tests during the documented development validation run. Re-run the test suite to establish the current result after subsequent changes.

A passing test suite demonstrates that the coded assertions pass; it does not independently certify every possible composition or calculation branch.

## Known limitations

1. The Streamlit graphical interface is not yet connected to the complete normative calculation workflow.
2. The published Bostonite benchmark contains conditional assumptions for unreported components.
3. The Winter basalt and Idaho Batholith comparisons use procedures different from classical Kelsey (1965).
4. The existing benchmark collection does not independently validate every optional-component branch and every possible mineral assemblage.
5. Internal mass balance is necessary but does not alone establish agreement with an external normative procedure.
6. Further independent published worked examples are needed to strengthen validation coverage.

## Development roadmap

Planned development areas include:

- Complete geochemical input interface.
- Integration of the calculation engine with Streamlit.
- Normative mineral interpretation.
- Normative mineral distribution plots.
- Geochemical visualization.
- Calculation result export.
- Reproducible scientific reports.
- Additional published reference benchmarks.
- Expanded validation of optional-component and silica-deficiency pathways.

## References

1. Kelsey, C. H. (1965). Calculation of the C.I.P.W. norm. *Mineralogical Magazine*, 34(268), 276–282. https://doi.org/10.1180/minmag.1965.034.268.23

2. Washington, H. S. (1917). Source analysis associated with the Bostonite worked example, p. 274, analysis no. 37, as used in Kelsey's Table III.

3. Winter, J. D. (2014). *Principles of Igneous and Metamorphic Petrology*, 2nd edition. Pearson.

4. Mattioli, G. S., & Zachry, D. L. (2008). Idaho Batholith granite, sample 134.15, published educational exercise.

## License

No license has been selected for this repository yet.

Until a license is added, the default copyright restrictions apply. Please do not assume that the source code is available for unrestricted reuse.

## Author

**Deepak Mohanta**

M.Tech Applied Geology
National Institute of Technology, Raipur

GitHub: https://github.com/helldeepak116-design

---

*CIPW Norm Studio — Scientific calculation, transparency, and reproducibility in normative mineralogy.*
