# CIPW Norm Studio — Scientific Validation Report

**Validation baseline:** 332 passing automated tests
**Calculation procedure:** Classical Kelsey (1965)
**Iron handling:** Measured FeO and Fe2O3 separately
**Report status:** Validation summary based on the benchmark and audit results recorded during development

---

## 1. Purpose and scope

This report records the available scientific validation evidence for CIPW Norm Studio. It distinguishes:

- comparison against a published worked example;
- comparison against a published example using a simplified or modified CIPW procedure;
- comparison against an exercise that uses a different normative procedure;
- targeted arithmetic and component-balance audits; and
- automated software regression tests.

These evidence types are not interchangeable. In particular, a close diagnostic comparison is not proof that every implementation rule is equivalent to the classical Kelsey (1965) procedure.

## 2. Validation summary

| Benchmark / audit | Evidence category | Current outcome | Important qualification |
|---|---|---|---|
| Kelsey (1965) Bostonite, Table III | Rounded published worked-example comparison | 3 dedicated regression tests pass | Conditional assumptions for unreported components; comparison uses published molecular amounts rounded to 0.001 |
| Winter (2014) Mid-Atlantic Ridge tholeiitic basalt | Modified-CIPW diagnostic comparison | 2 dedicated regression tests pass; close agreement with published norm | Winter describes a simplified/modified procedure, not an independent exact Kelsey implementation |
| Idaho Batholith granite, sample 134.15 | Published exercise / oxide molecular-proportion comparison | Existing benchmark tests pass | Source exercise uses Hyndman's procedure; not an exact Kelsey acceptance benchmark |
| Apatite-fluorine synthetic audit | Targeted arithmetic and integration audit | Low-F and excess-F cases pass; independent formula mass agrees with engine | Synthetic cases, not a complete published whole-rock reference analysis |
| Internal mass-balance checks | Internal conservation audit | Passed in recorded Bostonite and Winter runs | Internal consistency does not by itself prove agreement with an external normative procedure |

## 3. Kelsey (1965) Bostonite benchmark

### Source and input basis

The worked example is Kelsey's Bostonite from Maros, Celebes, Table III, associated with Washington (1917), page 274, analysis no. 37.

Kelsey's Table III input values used in the regression are:

| Oxide | wt.% |
|---|---:|
| SiO2 | 61.15 |
| TiO2 | 0.21 |
| Al2O3 | 22.07 |
| Fe2O3 | 1.05 |
| FeO | 1.02 |
| MgO | 0.40 |
| CaO | 0.75 |
| Na2O | 5.86 |
| K2O | 7.01 |

The original Washington transcription gives TiO2 = 0.20 wt.% and Fe2O3 = 1.06 wt.%. Kelsey's Table III uses 0.21 and 1.05 wt.% respectively. The Kelsey regression uses the values in Kelsey's worked table rather than mixing the original analysis values with Kelsey's outputs.

H2O+ is excluded from the anhydrous norm. MnO and P2O5 are not reported in the analysis and are explicitly assumed zero for this benchmark. All ten optional components are recorded as `not_measured`; `assume_unmeasured_zero=True` is used only to permit a conditional calculation. The output must remain labelled conditional.

### Published intermediate comparison

| Quantity | Studio | Kelsey published | Difference |
|---|---:|---:|---:|
| Initial silica deficiency D | 0.037735 | 0.038 | -0.000265 |
| Provisional hypersthene hy' | 0.014917 | 0.015 | -0.000083 |
| Provisional albite ab' | 0.094548 | 0.095 | -0.000452 |

The final silica deficiency is zero in the recorded run.

### Published final molecular amounts

| Mineral | Studio | Kelsey published | Difference |
|---|---:|---:|---:|
| Corundum (c) | 0.034113 | 0.034 | +0.000113 |
| Olivine (ol) | 0.007459 | 0.008 | -0.000541 |
| Orthoclase (or) | 0.074419 | 0.074 | +0.000419 |
| Magnetite (mt) | 0.006575 | 0.006 | +0.000575 |
| Albite (ab) | 0.086979 | 0.087 | -0.000021 |
| Ilmenite (il) | 0.002629 | 0.003 | -0.000371 |
| Anorthite (an) | 0.013374 | 0.014 | -0.000626 |
| Nepheline (ne) | 0.007569 | 0.008 | -0.000431 |

The regression uses an absolute tolerance of 0.001 molecular proportions to reflect the three-decimal precision of the historical published values.

**Interpretation:** This is a useful rounded end-to-end worked-example comparison for the selected Kelsey procedure. It is not an exact analytical reproduction because unreported components are conditionally assumed absent and the source values are rounded.

## 4. Winter tholeiitic basalt diagnostic

The diagnostic uses the Mid-Atlantic Ridge tholeiitic basalt example in Winter (2014), Appendix B, Table 2.

The source reports a major-oxide analysis, sulfur, water, molecular proportions, intermediate allocations, and a final norm. Winter describes a simplified or modified CIPW procedure. Therefore, this is classified as a **modified-CIPW diagnostic comparison**, not an exact independent Kelsey validation.

Recorded results:

- Major-oxide molecular proportions agree closely with the published values.
- Ten normative mineral molecular amounts were compared with the published table.
- The diagnostic regression uses an absolute tolerance of 1.0e-4 for those published molecular amounts.
- The normalized normative weight percentages agreed closely after normalizing the source's published norm total of 98.43 to 100.
- The engine reported balanced component mass balance and zero final silica deficiency.

The dedicated regression test checks the source major-oxide molecular proportions and the full calculation's mass-balance / silica-deficiency status. It should not be described as proof of exact Kelsey rule equivalence.

## 5. Idaho Batholith granite comparison

The Idaho Batholith granite, sample 134.15, is drawn from a published educational exercise by Mattioli and Zachry (2008).

The exercise uses Hyndman's procedure. It is useful for checking oxide conversion and for contextual comparison of a normative calculation, but it is **not** a direct published Kelsey (1965) benchmark.

The existing validation script compares the engine's result with the published norm as a diagnostic. The reference tests also check the reported analytical total and rounded oxide molecular proportions.

## 6. Apatite-fluorine audit

Two synthetic compositions were used to test the Kelsey Rule 5 / Rule 6 fluorine allocation:

- Low fluorine: all available F is allocated to apatite; no fluorite is produced.
- Higher fluorine: apatite receives F up to the Kelsey allocation limit, and excess F is allocated to fluorite.

The audit independently calculated apatite formula mass and compared it with the engine. The recorded low-F and high-F cases agreed, and component mass-balance residuals were zero.

This is a targeted rule and formula-mass audit. It is not a substitute for a complete published whole-rock benchmark.

## 7. Automated regression baseline

Recorded full-suite result after adding the corrected Kelsey Bostonite benchmark:

```text
332 passed in 1.25s
```

Dedicated regression tests recorded:

- Kelsey Bostonite: 3 passed.
- Winter tholeiitic basalt: 2 passed.

The test suite is a software regression baseline. A passing test suite establishes that the coded assertions pass; it does not independently certify the scientific validity of every possible composition or branch.

## 8. Known limitations and controls

1. **Conditional optional components:** Unmeasured optional components are not equivalent to measured zeros. Any calculation using `assume_unmeasured_zero=True` must remain visibly conditional.
2. **Unreported major oxides:** MnO and P2O5 are absent from the Bostonite analysis. The regression explicitly uses zero assumptions for these required API fields.
3. **Historical rounding:** Kelsey's molecular amounts and intermediate values are printed to limited precision. Tests must compare at source-appropriate precision and must not imply greater accuracy than the source provides.
4. **Different procedures:** Winter's modified CIPW and the Idaho Hyndman exercise must not be represented as exact Kelsey validations.
5. **Mass balance versus reference agreement:** Internal mass balance is necessary but not sufficient. A calculation can conserve components and still differ from a published normative allocation.
6. **Formula-weight conventions:** Published normative weight percentages may reflect historical rounding and conventions. Compare like-for-like quantities and retain molecular amounts as the primary comparison where the source publishes them.
7. **Coverage:** The current benchmark set does not establish independent end-to-end validation of every optional-component branch, every silica-deficiency pathway, or every possible mineral assemblage.

## 9. Recommended future validation work

- Obtain complete primary-source worked examples for additional Kelsey rule branches.
- Add separate benchmarks for silica excess and each relevant silica-deficiency redistribution pathway.
- Add independent tests for sulfur, halogens, carbonate, zirconium, chromium, and other optional-component branches.
- Record source page/table, original input values, assumptions, source precision, comparison quantity, and tolerance for every benchmark.
- Keep exact Kelsey references separate from modified-procedure diagnostics and synthetic audits.

---

## 10. Reproducibility commands

Run from the project root with the project virtual environment active:

```powershell
python -m pytest -q
python -m pytest -q tests/test_kelsey_bostonite_regression.py
python -m pytest -q tests/test_winter_basalt_norm_regression.py
python -m scripts.run_kelsey_bostonite_validation
python -m scripts.run_tholeiitic_basalt_diagnostic
python -m scripts.audit_apatite_fluorine
```
