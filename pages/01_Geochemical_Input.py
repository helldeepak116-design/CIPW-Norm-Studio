
"""Geochemical input, validation and molecular conversion interface."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import REQUIRED_OXIDES
from src.data_validation import (
    validate_oxide_composition,
    validate_geochemical_dataframe,
)
from src.oxide_conversion import convert_oxides_to_molecular_proportions


st.set_page_config(
    page_title="Geochemical Input | CIPW Norm Studio",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 Geochemical Input")
st.caption("Enter or upload whole-rock major-element oxide analyses.")

st.info(
    "Input values must be reported in wt.%. Measured FeO and Fe₂O₃ "
    "are retained independently. Missing values are not treated as zero."
)


def process_composition(
    sample_id: str,
    composition: dict,
    volatile_free: bool,
):
    """Validate and convert one sample."""
    validation = validate_oxide_composition(composition)

    if not validation["valid"]:
        return validation, None

    conversion = convert_oxides_to_molecular_proportions(
        composition,
        volatile_free=volatile_free,
    )

    return validation, conversion


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read CSV or Excel input."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    raise ValueError("Unsupported file format.")


def build_conversion_outputs(
    dataframe: pd.DataFrame,
    volatile_free: bool,
):
    """Validate and convert a batch of analyses."""
    validation = validate_geochemical_dataframe(dataframe)

    if not validation["valid"]:
        return validation, [], [], []

    summary_rows = []
    detailed_rows = []
    failed_rows = []

    for index, row in dataframe.iterrows():
        sample_id = (
            str(row["Sample_ID"])
            if "Sample_ID" in dataframe.columns
            else f"Sample_{index + 1:03d}"
        )

        composition = {
            oxide: row[oxide]
            for oxide in REQUIRED_OXIDES
        }

        row_validation, conversion = process_composition(
            sample_id,
            composition,
            volatile_free,
        )

        if not row_validation["valid"]:
            failed_rows.append(
                {
                    "Sample_ID": sample_id,
                    "Errors": "; ".join(row_validation["errors"]),
                }
            )
            continue

        summary_rows.append(
            {
                "Sample_ID": sample_id,
                "Analytical_Total_wt_pct": (
                    row_validation["analytical_total"]
                ),
                "Total_Status": row_validation["total_status"],
                "Conversion_Total_wt_pct": (
                    conversion["conversion_total"]
                ),
                "Volatile_Free": volatile_free,
            }
        )

        oxide_table = conversion["oxide_table"]

        for oxide, values in oxide_table.iterrows():
            detailed_rows.append(
                {
                    "Sample_ID": sample_id,
                    "Oxide": oxide,
                    "Input_wt_pct": values["wt_percent"],
                    "Molecular_Weight": values["molecular_weight"],
                    "Molecular_Proportion": values[
                        "molecular_proportion"
                    ],
                    "Cation_Proportion": values["cation_proportion"],
                    "Oxygen_Proportion": values["oxygen_proportion"],
                    "Volatile_Free": volatile_free,
                }
            )

    return (
        validation,
        summary_rows,
        detailed_rows,
        failed_rows,
    )


tab_manual, tab_batch = st.tabs(
    ["Manual sample entry", "CSV / Excel batch upload"]
)

with tab_manual:
    st.subheader("Single-sample analysis")

    with st.form("manual_geochemical_input"):
        sample_id = st.text_input(
            "Sample ID",
            value="SAMPLE_001",
        )

        st.markdown("**Major-element oxide composition (wt.%)**")

        columns = st.columns(3)
        manual_values = {}

        for index, oxide in enumerate(REQUIRED_OXIDES):
            with columns[index % 3]:
                manual_values[oxide] = st.text_input(
                    oxide,
                    value="",
                    placeholder="Enter measured wt.%",
                    key=f"manual_{oxide}",
                )

        volatile_free_manual = st.checkbox(
            "Perform explicit volatile-free recalculation",
            value=False,
            key="manual_volatile_free",
        )

        manual_submit = st.form_submit_button(
            "Validate and convert sample",
            type="primary",
        )

    if manual_submit:
        if not sample_id.strip():
            st.error("Sample ID cannot be empty.")
        else:
            composition = {}
            input_errors = []

            for oxide, raw_value in manual_values.items():
                if raw_value.strip() == "":
                    input_errors.append(f"{oxide} is missing.")
                    continue

                try:
                    composition[oxide] = float(raw_value)
                except ValueError:
                    input_errors.append(f"{oxide} must be numeric.")

            if input_errors:
                st.error("Input errors: " + " ".join(input_errors))
            else:
                validation, conversion = process_composition(
                    sample_id.strip(),
                    composition,
                    volatile_free_manual,
                )

                if not validation["valid"]:
                    st.error("The sample failed validation.")
                    for error in validation["errors"]:
                        st.write(f"- {error}")
                else:
                    st.session_state["cipw_input_sample_id"] = sample_id.strip()
                    st.session_state["cipw_input_composition"] = composition
                    st.session_state["cipw_input_conversion"] = conversion
                    st.session_state["cipw_input_validation"] = validation

                    st.success("Input validation and molecular conversion completed.")

    if "cipw_input_conversion" in st.session_state:
        validation = st.session_state["cipw_input_validation"]
        conversion = st.session_state["cipw_input_conversion"]

        st.markdown("---")
        st.subheader("Analytical validation")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Analytical total",
            f"{validation['analytical_total']:.4f} wt.%",
        )
        col2.metric(
            "Total status",
            validation["total_status"].replace("_", " ").title(),
        )
        col3.metric(
            "Conversion total",
            f"{conversion['conversion_total']:.4f} wt.%",
        )

        for warning in validation["warnings"]:
            st.warning(warning)

        st.subheader("Molecular conversion table")
        st.dataframe(
            conversion["oxide_table"].round(8),
            width="stretch",
        )

        csv_data = conversion["oxide_table"].reset_index().to_csv(
            index=False
        )

        st.download_button(
            "Download molecular conversion CSV",
            data=csv_data,
            file_name="cipw_molecular_conversion.csv",
            mime="text/csv",
        )


with tab_batch:
    st.subheader("Multiple-sample analysis")

    uploaded_file = st.file_uploader(
        "Upload geochemical data",
        type=["csv", "xlsx", "xls"],
        help=(
            "Required columns: " + ", ".join(REQUIRED_OXIDES)
            + ". Optional identifier column: Sample_ID."
        ),
        key="geochemical_batch_upload",
    )

    volatile_free_batch = st.checkbox(
        "Perform explicit volatile-free recalculation for all samples",
        value=False,
        key="batch_volatile_free",
    )

    if uploaded_file is not None:
        try:
            input_dataframe = read_uploaded_file(uploaded_file)

            st.markdown("**Uploaded data preview**")
            st.dataframe(
                input_dataframe.head(10),
                width="stretch",
            )

            if st.button(
                "Validate and convert batch",
                type="primary",
                key="process_geochemical_batch",
            ):
                validation, summary, detailed, failed = (
                    build_conversion_outputs(
                        input_dataframe,
                        volatile_free_batch,
                    )
                )

                st.session_state["cipw_batch_validation"] = validation
                st.session_state["cipw_batch_summary"] = summary
                st.session_state["cipw_batch_detailed"] = detailed
                st.session_state["cipw_batch_failed"] = failed

        except Exception as exc:
            st.error(f"Could not read uploaded file: {exc}")

    if "cipw_batch_validation" in st.session_state:
        validation = st.session_state["cipw_batch_validation"]
        summary = st.session_state["cipw_batch_summary"]
        detailed = st.session_state["cipw_batch_detailed"]
        failed = st.session_state["cipw_batch_failed"]

        st.markdown("---")
        st.subheader("Batch validation report")

        if validation["valid"]:
            st.success("Dataset structure and sample identifiers are valid.")
        else:
            st.error("Dataset-level validation failed.")
            for error in validation["errors"]:
                st.write(f"- {error}")

        for warning in validation["warnings"]:
            st.warning(warning)

        if summary:
            summary_dataframe = pd.DataFrame(summary)

            st.subheader("Conversion summary")
            st.dataframe(
                summary_dataframe,
                width="stretch",
                hide_index=True,
            )

            summary_csv = summary_dataframe.to_csv(index=False)

            st.download_button(
                "Download sample summary CSV",
                data=summary_csv,
                file_name="cipw_sample_conversion_summary.csv",
                mime="text/csv",
            )

        if detailed:
            detailed_dataframe = pd.DataFrame(detailed)

            st.subheader("Detailed molecular proportions")
            st.dataframe(
                detailed_dataframe,
                width="stretch",
                hide_index=True,
            )

            detailed_csv = detailed_dataframe.to_csv(index=False)

            st.download_button(
                "Download detailed molecular conversion CSV",
                data=detailed_csv,
                file_name="cipw_detailed_molecular_conversion.csv",
                mime="text/csv",
            )

        if failed:
            st.subheader("Samples not converted")
            st.dataframe(
                pd.DataFrame(failed),
                width="stretch",
                hide_index=True,
            )

st.markdown("---")
st.caption(
    "CIPW Norm Studio | This page performs geochemical validation "
    "and molecular conversion only. It does not calculate normative minerals."
)

