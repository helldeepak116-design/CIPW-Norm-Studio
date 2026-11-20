
"""Validation utilities for whole-rock major-element analyses."""

from __future__ import annotations

import numpy as np
import pandas as pd

from config.settings import (
    ANALYTICAL_TOTAL_MAX,
    ANALYTICAL_TOTAL_MIN,
    MAXIMUM_OXIDE_VALUE,
    MINIMUM_OXIDE_VALUE,
    REQUIRED_OXIDES,
)


def validate_oxide_composition(
    composition: dict,
    *,
    require_all_oxides: bool = True,
) -> dict:
    """Validate one oxide composition without modifying its values.

    Missing values are not interpreted as zero. Explicit zero values
    are accepted. Analytical-total limits generate warnings rather
    than automatic rejection.

    Numeric strings are accepted and converted for validation.
    Boolean values are rejected because they are not valid
    geochemical concentrations.

    Returns a report containing errors, warnings and analytical total.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(composition, dict):
        return {
            "valid": False,
            "errors": ["Composition must be a dictionary."],
            "warnings": [],
            "analytical_total": None,
            "total_status": "not_calculated",
        }

    unknown = sorted(set(composition) - set(REQUIRED_OXIDES))
    if unknown:
        errors.append(f"Unsupported oxide columns: {unknown}")

    missing = [oxide for oxide in REQUIRED_OXIDES if oxide not in composition]
    if missing and require_all_oxides:
        errors.append(f"Missing required oxides: {missing}")

    numeric_values: dict[str, float] = {}

    for oxide in REQUIRED_OXIDES:
        if oxide not in composition:
            continue

        value = composition[oxide]

        if value is None or pd.isna(value):
            errors.append(f"{oxide} is missing.")
            continue

        if isinstance(value, (bool, np.bool_)):
            errors.append(f"{oxide} must be numeric, not boolean.")
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            errors.append(f"{oxide} must be numeric.")
            continue

        if not np.isfinite(numeric_value):
            errors.append(f"{oxide} must be finite.")
            continue

        if numeric_value < MINIMUM_OXIDE_VALUE:
            errors.append(f"{oxide} cannot be negative.")
            continue

        if numeric_value > MAXIMUM_OXIDE_VALUE:
            errors.append(
                f"{oxide} exceeds the permitted maximum "
                f"of {MAXIMUM_OXIDE_VALUE} wt.%."
            )
            continue

        numeric_values[oxide] = numeric_value

    analytical_total = None
    total_status = "not_calculated"

    if not errors or (
        not require_all_oxides
        and all(
            oxide in numeric_values
            for oxide in REQUIRED_OXIDES
            if oxide in composition
        )
    ):
        if len(numeric_values) == len(REQUIRED_OXIDES):
            analytical_total = float(sum(numeric_values.values()))

            if analytical_total < ANALYTICAL_TOTAL_MIN:
                total_status = "low"
                warnings.append(
                    f"Analytical total ({analytical_total:.4f} wt.%) "
                    f"is below {ANALYTICAL_TOTAL_MIN:.2f} wt.%."
                )
            elif analytical_total > ANALYTICAL_TOTAL_MAX:
                total_status = "high"
                warnings.append(
                    f"Analytical total ({analytical_total:.4f} wt.%) "
                    f"exceeds {ANALYTICAL_TOTAL_MAX:.2f} wt.%."
                )
            else:
                total_status = "within_range"

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "analytical_total": analytical_total,
        "total_status": total_status,
    }


def validate_geochemical_dataframe(
    dataframe: pd.DataFrame,
    sample_id_column: str | None = "Sample_ID",
) -> dict:
    """Validate a table containing one analysis per row."""
    errors: list[str] = []
    warnings: list[str] = []
    row_reports: list[dict] = []

    if not isinstance(dataframe, pd.DataFrame):
        return {
            "valid": False,
            "errors": ["Input must be a pandas DataFrame."],
            "warnings": [],
            "row_reports": [],
        }

    if dataframe.empty:
        return {
            "valid": False,
            "errors": ["Input dataset contains no rows."],
            "warnings": [],
            "row_reports": [],
        }

    if dataframe.columns.duplicated().any():
        errors.append("Duplicate column names are not permitted.")

    required_columns = set(REQUIRED_OXIDES)
    missing_columns = sorted(required_columns - set(dataframe.columns))

    if missing_columns:
        errors.append(f"Missing required oxide columns: {missing_columns}")

    if sample_id_column and sample_id_column in dataframe.columns:
        sample_ids = dataframe[sample_id_column]

        if sample_ids.isna().any():
            errors.append(f"{sample_id_column} contains missing identifiers.")

        blank_ids = sample_ids.map(
            lambda value: isinstance(value, str) and not value.strip()
        )
        if blank_ids.any():
            errors.append(f"{sample_id_column} contains blank identifiers.")

        if sample_ids.astype(str).duplicated().any():
            errors.append(f"{sample_id_column} contains duplicate identifiers.")

    if missing_columns:
        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
            "row_reports": [],
        }

    for index, row in dataframe.iterrows():
        composition = {oxide: row[oxide] for oxide in REQUIRED_OXIDES}
        report = validate_oxide_composition(composition)

        sample_id = (
            row[sample_id_column]
            if sample_id_column and sample_id_column in dataframe.columns
            else index
        )

        row_report = {
            "row_index": index,
            "sample_id": sample_id,
            **report,
        }
        row_reports.append(row_report)

        for error in report["errors"]:
            errors.append(f"Sample {sample_id}: {error}")

        for warning in report["warnings"]:
            warnings.append(f"Sample {sample_id}: {warning}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_reports": row_reports,
    }
