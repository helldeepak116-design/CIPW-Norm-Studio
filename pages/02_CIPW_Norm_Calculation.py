"""CIPW Norm Studio: complete Kelsey (1965) calculation interface."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import (
    REQUIRED_OXIDES,
    NUMERICAL_TOLERANCE,
    OUTPUT_DECIMAL_PLACES,
)
from src.norm_calculation import (
    calculate_cipw_norm,
    OptionalComponentsIncompleteError,
)
from src.optional_components import OPTIONAL_COMPONENTS
from src.mineral_formula_weights import MINERAL_FORMULAE
from src.report_generator import generate_cipw_pdf_report


st.set_page_config(
    page_title="CIPW Norm Calculation | CIPW Norm Studio",
    page_icon="🧮",
    layout="wide",
)

st.title("🧮 CIPW Norm Calculation")
st.caption("Classical CIPW Norm — Kelsey (1965)")

st.info(
    "Enter measured major-oxide concentrations and explicitly identify "
    "the analytical status of each optional component. FeO and Fe₂O₃ "
    "are treated independently."
)

# ------------------------------------------------------------------
# Input form
# ------------------------------------------------------------------

st.header("1. Major-element composition")

sample_id = st.text_input(
    "Sample ID",
    value="SAMPLE_001",
    key="norm_sample_id",
)

st.caption("All concentrations must be entered in wt.%.")

with st.form("cipw_norm_calculation_form"):

    st.subheader("Major oxides")

    major_values = {}
    columns = st.columns(3)

    for index, oxide in enumerate(REQUIRED_OXIDES):
        with columns[index % 3]:
            raw = st.text_input(
                oxide,
                placeholder="Measured wt.%",
                key=f"norm_major_{oxide}",
            )
            major_values[oxide] = raw

    st.divider()

    st.header("2. Optional-component measurements")

    st.warning(
        "Do not select measured zero unless the component was actually "
        "analysed and reported as zero. Not measured is a separate state."
    )

    optional_values = {}

    for index, component in enumerate(OPTIONAL_COMPONENTS):

        if index % 2 == 0:
            left, right = st.columns(2)

        column = left if index % 2 == 0 else right

        with column:
            st.markdown(f"**{component}**")

            status = st.selectbox(
                f"{component} measurement status",
                options=[
                    "not_measured",
                    "measured",
                    "measured_zero",
                ],
                format_func=lambda value: {
                    "not_measured": "Not measured",
                    "measured": "Measured",
                    "measured_zero": "Measured zero",
                }[value],
                key=f"norm_status_{component}",
            )

            if status == "measured":
                value = st.number_input(
                    f"{component} concentration (wt.%)",
                    min_value=0.000000001,
                    value=0.01,
                    format="%.8f",
                    key=f"norm_value_{component}",
                )
            elif status == "measured_zero":
                value = 0.0
                st.caption("Recorded concentration: 0 wt.%")
            else:
                value = None
                st.caption("Concentration unavailable")

            optional_values[component] = {
                "status": status,
                "value_wt_percent": value,
            }

    st.divider()

    st.header("3. Calculation settings")

    setting_col1, setting_col2 = st.columns(2)

    with setting_col1:
        sulfur_basis = st.selectbox(
            "Sulfur analytical basis",
            options=["none", "S", "SO3"],
            help=(
                "Select the reported sulfur basis. Do not report the "
                "same sulfur measurement under both S and SO3."
            ),
        )

        carbonate_mode = st.selectbox(
            "Carbonate treatment",
            options=["none", "cancrinite", "calcite"],
        )

    with setting_col2:
        volatile_free = st.checkbox(
            "Apply volatile-free normalization",
            value=False,
            help=(
                "Normalizes major oxides to 100 wt.% and applies "
                "the same factor to optional-component proportions."
            ),
        )

        assume_unmeasured_zero = st.checkbox(
            "Allow exploratory calculation assuming unmeasured "
            "optional components are absent",
            value=False,
            help=(
                "Produces a conditional result. This does not mean "
                "the components were measured at zero."
            ),
        )

    st.divider()

    submitted = st.form_submit_button(
        "Calculate CIPW Norm",
        type="primary",
        use_container_width=True,
    )


# ------------------------------------------------------------------
# Calculation
# ------------------------------------------------------------------

if submitted:

    st.session_state.pop("cipw_norm_result", None)
    st.session_state.pop("cipw_norm_error", None)

    errors = []

    if not sample_id.strip():
        errors.append("Sample ID cannot be empty.")

    major_composition = {}

    for oxide, raw_value in major_values.items():

        if not raw_value.strip():
            errors.append(f"{oxide} is missing.")
            continue

        try:
            value = float(raw_value)
        except ValueError:
            errors.append(f"{oxide} must be numeric.")
            continue

        major_composition[oxide] = value

    if errors:
        st.error("Input validation failed.")

        for error in errors:
            st.write(f"- {error}")

    else:
        try:
            result = calculate_cipw_norm(
                major_oxide_wt_percent=major_composition,
                optional_measurements=optional_values,
                sulfur_basis=sulfur_basis,
                carbonate_mode=carbonate_mode,
                volatile_free=volatile_free,
                assume_unmeasured_zero=assume_unmeasured_zero,
                numerical_tolerance=NUMERICAL_TOLERANCE,
            )

            # Save complete calculation context for reproducible reporting.
            st.session_state["cipw_norm_result"] = result
            st.session_state["cipw_norm_sample_id"] = sample_id.strip()
            st.session_state["cipw_norm_input"] = major_composition.copy()

            st.session_state["cipw_norm_optional_input"] = {
                component: record.copy()
                for component, record in optional_values.items()
            }

            st.session_state["cipw_norm_settings"] = {
                "sulfur_basis": sulfur_basis,
                "carbonate_mode": carbonate_mode,
                "volatile_free": volatile_free,
                "assume_unmeasured_zero": assume_unmeasured_zero,
            }

            st.success("CIPW calculation completed.")

        except OptionalComponentsIncompleteError as exc:
            st.error(
                "Calculation blocked: incomplete optional measurements."
            )
            st.write(str(exc))

        except (ValueError, TypeError, ArithmeticError) as exc:
            st.error("The calculation could not be completed.")
            st.exception(exc)

        except Exception as exc:
            st.error("Unexpected calculation error.")
            st.exception(exc)


# ------------------------------------------------------------------
# Results
# ------------------------------------------------------------------

result = st.session_state.get("cipw_norm_result")

if result is not None:

    sample_name = st.session_state["cipw_norm_sample_id"]

    st.divider()
    st.header("4. Calculation results")

    st.subheader(f"Sample: {sample_name}")

    st.write(f"**Method:** {result.method}")

    status_col1, status_col2, status_col3 = st.columns(3)

    status_col1.metric("Calculation status", result.status)

    status_col2.metric(
        "Mass balance",
        result.mass_balance.status,
    )

    status_col3.metric(
        "Total normative mass",
        f"{result.total_normative_mass:.4f}",
    )

    if result.conditional:
        st.warning(
            "CONDITIONAL RESULT: one or more optional components were "
            "unmeasured and assumed absent. Interpret accordingly."
        )

    if not result.mass_balance.balanced:
        st.error(
            "Component mass balance failed. Do not treat this result "
            "as a verified normative calculation."
        )
    elif result.status == "COMPLETED":
        st.success("Component mass balance passed.")

    if result.status == "UNRESOLVED_SILICA_DEFICIENCY":
        st.warning("Silica deficiency remains unresolved.")

    for warning in result.warnings:
        st.warning(warning)

    # --------------------------------------------------------------
    # Normative mineral table
    # --------------------------------------------------------------

    st.subheader("Final normative mineral assemblage")

    mineral_rows = []

    for symbol, amount in result.final_minerals.items():

        formula_entry = MINERAL_FORMULAE[symbol]

        mineral_rows.append({
            "Symbol": symbol,
            "Mineral": formula_entry.name,
            "Ideal formula": formula_entry.formula,
            "Molecular amount": amount,
            "Mineral mass": result.mineral_masses[symbol],
            "Normative wt.%": result.mineral_wt_percent[symbol],
        })

    mineral_df = pd.DataFrame(mineral_rows)

    if not mineral_df.empty:

        mineral_df = mineral_df.sort_values(
            "Normative wt.%",
            ascending=False,
        )

        st.dataframe(
            mineral_df.round(OUTPUT_DECIMAL_PLACES),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Normative mineral proportions")

        chart_df = mineral_df.set_index("Mineral")[
            "Normative wt.%"
        ]

        st.bar_chart(chart_df)

        st.metric(
            "Sum of normalized normative percentages",
            f"{sum(result.mineral_wt_percent.values()):.6f}%",
        )

    else:
        st.warning(
            "No positive normative mineral amounts were produced."
        )

    # --------------------------------------------------------------
    # Provisional versus final allocation
    # --------------------------------------------------------------

    st.divider()
    st.subheader("5. Kelsey allocation audit")

    provisional = result.provisional_result
    redistribution = result.redistribution_result

    provisional_minerals = provisional.minerals
    final_minerals = redistribution.minerals

    audit_symbols = sorted(
        set(provisional_minerals) | set(final_minerals)
    )

    audit_df = pd.DataFrame([
        {
            "Mineral": symbol,
            "Provisional amount": provisional_minerals.get(
                symbol, 0.0
            ),
            "Final amount": final_minerals.get(symbol, 0.0),
            "Change": (
                final_minerals.get(symbol, 0.0)
                - provisional_minerals.get(symbol, 0.0)
            ),
        }
        for symbol in audit_symbols
    ])

    st.dataframe(
        audit_df.round(OUTPUT_DECIMAL_PLACES),
        use_container_width=True,
        hide_index=True,
    )

    deficiency_col1, deficiency_col2 = st.columns(2)

    deficiency_col1.metric(
        "Initial silica deficiency",
        f"{redistribution.initial_deficiency:.8f}",
    )

    deficiency_col2.metric(
        "Final silica deficiency",
        f"{redistribution.final_deficiency:.8f}",
    )

    # --------------------------------------------------------------
    # Mass-balance diagnostics
    # --------------------------------------------------------------

    st.divider()
    st.subheader("6. Component mass-balance verification")

    balance = result.mass_balance

    balance_col1, balance_col2, balance_col3 = st.columns(3)

    balance_col1.metric(
        "Maximum non-silica error",
        f"{balance.max_non_silica_error:.3e}",
    )

    balance_col2.metric(
        "Silica error",
        f"{balance.silica_error:.3e}",
    )

    balance_col3.metric(
        "Expected silica deficit",
        f"{balance.expected_silica_deficit:.8f}",
    )

    difference_df = pd.DataFrame([
        {
            "Component": component,
            "Difference": difference,
        }
        for component, difference
        in balance.component_differences.items()
    ])

    with st.expander("View component conservation details"):
        st.dataframe(
            difference_df,
            use_container_width=True,
            hide_index=True,
        )

    for message in balance.messages:
        st.warning(message)

    # --------------------------------------------------------------
    # Intermediate calculations
    # --------------------------------------------------------------

    st.divider()
    st.subheader("7. Calculation intermediates")

    with st.expander("Major oxide molecular proportions"):
        st.json(result.major_oxide_moles)

    with st.expander("Optional-component molecular proportions"):
        st.json(result.optional_component_moles)

    with st.expander("Rule 19 Mg-Fe proportions"):
        st.write({
            "Mg fraction": provisional.mg_fraction,
            "Fe fraction": provisional.fe_fraction,
        })

    with st.expander("Provisional residual oxides"):
        st.json(provisional.residual_oxides)

    with st.expander("Provisional allocation audit trail"):
        st.json({
            "Provisional minerals": provisional.minerals,
            "Initial silica deficiency": provisional.silica_deficiency,
            "Apatite fluorine amount": (
                provisional.apatite_fluorine_amount
            ),
        })

    with st.expander("Silica redistribution steps"):
        st.json({
            "Initial deficiency": redistribution.initial_deficiency,
            "Final deficiency": redistribution.final_deficiency,
            "Final minerals": redistribution.minerals,
            "Redistribution steps": [
                {
                    "rule": step.get("rule"),
                    "description": step.get("description"),
                    "reactants": step.get("reactants"),
                    "products": step.get("products"),
                    "remaining": step.get("remaining"),
                }
                for step in redistribution.steps
            ],
        })

    # --------------------------------------------------------------
    # Downloads
    # --------------------------------------------------------------

    st.divider()
    st.subheader("8. Export results")

    # Generate PDF from the saved inputs and the current result.
    saved_settings = st.session_state.get(
        "cipw_norm_settings", {}
    )

    try:
        pdf_data = generate_cipw_pdf_report(
            result=result,
            sample_id=sample_name,
            major_oxide_input=st.session_state.get(
                "cipw_norm_input", {}
            ),
            optional_measurements=st.session_state.get(
                "cipw_norm_optional_input", {}
            ),
            sulfur_basis=saved_settings.get(
                "sulfur_basis", "none"
            ),
            carbonate_mode=saved_settings.get(
                "carbonate_mode", "none"
            ),
            volatile_free=saved_settings.get(
                "volatile_free", False
            ),
            assume_unmeasured_zero=saved_settings.get(
                "assume_unmeasured_zero", False
            ),
            metadata={},
        )

        st.download_button(
            "Download scientific calculation report (PDF)",
            data=pdf_data,
            file_name=f"{sample_name}_cipw_norm_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as exc:
        st.error("PDF report generation failed.")
        st.exception(exc)

    # Existing mineral CSV export.
    csv_data = mineral_df.to_csv(index=False)

    st.download_button(
        "Download normative mineral results (CSV)",
        data=csv_data,
        file_name=f"{sample_name}_cipw_norm.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Existing mass-balance CSV export.
    balance_csv = difference_df.to_csv(index=False)

    st.download_button(
        "Download mass-balance diagnostics (CSV)",
        data=balance_csv,
        file_name=f"{sample_name}_mass_balance.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.caption(
        "Mineral masses are calculated on the analytical basis. "
        "Normative wt.% values are normalized to the total normative "
        "mineral mass; they are not the original whole-rock oxide "
        "weight percentages."
    )

st.divider()

st.caption(
    "CIPW Norm Studio | Classical Kelsey (1965) | "
    "Scientific calculation and audit interface"
)