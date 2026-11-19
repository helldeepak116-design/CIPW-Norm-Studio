# CIPW Norm Studio — Reference Benchmark Registry

This registry classifies the validation evidence. Do not combine the categories into one undifferentiated claim of scientific validation.

| ID | Name | Source / provenance | Category | Input / assumptions | Compared output | Current recorded status | Regression / audit location |
|---|---|---|---|---|---|---|---|
| KELSEY-BOSTONITE-1965 | Bostonite, Maros, Celebes | Kelsey (1965), Table III; Washington (1917), p. 274, analysis 37 | Rounded published worked-example comparison | Kelsey Table III uses Fe2O3 1.05 and TiO2 0.21 wt.%; MnO and P2O5 assumed zero; optional components not measured and conditionally assumed zero; H2O+ excluded | Kelsey intermediate silica-deficiency values and final normative mineral molecular amounts | 3 dedicated tests passed; all eight final mineral amounts within 0.001 molecular proportions in recorded run | `tests/test_kelsey_bostonite_regression.py`; `scripts/run_kelsey_bostonite_validation.py` |
| WINTER-MAR-2014 | Mid-Atlantic Ridge tholeiitic basalt | Winter (2014), Appendix B, Table 2 | Modified-CIPW diagnostic comparison | Major oxides, S=0.14 wt.%; H2O=1.65 wt.% excluded from anhydrous norm; other optional components explicitly zero in diagnostic | Major oxide molecular proportions; ten normative mineral molecular amounts; normalized normative wt.% diagnostic | 2 dedicated tests passed; close published comparison; internal balance and final silica checks passed | `tests/test_winter_basalt_norm_regression.py`; `scripts/run_tholeiitic_basalt_diagnostic.py` |
| IDAHO-BATHOLITH-13415 | Idaho Batholith granite, sample 134.15 | Mattioli & Zachry (2008) educational exercise | Different-procedure reference / oxide-conversion comparison | Published exercise uses Hyndman's procedure; major oxide analytical total 99.04 wt.% | Rounded oxide molecular proportions and diagnostic normative comparison | Existing reference tests pass; not a Kelsey acceptance benchmark | `tests/test_reference_benchmarks.py`; `scripts/run_reference_validation.py` |
| APATITE-F-AUDIT | Synthetic low-F and high-F compositions | Independent arithmetic audit based on Kelsey Rule 5 / Rule 6 convention | Synthetic rule / formula-mass audit | Two synthetic compositions; low F and excess F; explicit measured-zero optional-component records | Apatite F allocation, fluorite allocation, independent apatite formula mass, component balance | Both recorded cases passed; formula-mass agreement and zero component residuals | `scripts/audit_apatite_fluorine.py` |
| INTERNAL-MASS-BALANCE | Engine component-conservation checks | Internal implementation audit | Internal consistency check | Major and optional molecular proportions plus provisional and redistributed mineral results | Component residuals, silica error, mass-balance status | Recorded Bostonite and Winter runs balanced | `src/mass_balance.py`; exposed through `NormCalculationResult.mass_balance` |

## Registry rules

- **Exact / rounded published worked example:** source and procedure are the same; report source precision and any assumptions.
- **Different-procedure reference:** source is useful for selected checks but uses another normative procedure.
- **Modified-procedure diagnostic:** close agreement is informative but does not prove exact Kelsey equivalence.
- **Synthetic audit:** tests a specific equation, rule, or integration pathway; it is not an external whole-rock benchmark.
- **Internal consistency check:** verifies conservation or numerical invariants, not agreement with an external method.

## Baseline

Recorded full test suite: **331 passed in 1.15 seconds** after the corrected Kelsey Bostonite regression was added. Re-run the full suite before treating this as the current local baseline after any subsequent code change.
