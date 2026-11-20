
"""Scientific PDF report generator for CIPW Norm Studio.

Formats the output of the Classical Kelsey (1965) CIPW calculation.
This module does not perform or modify any scientific calculations.

Redistribution steps use the actual dictionary structure returned by
src.kelsey_silica_deficiency.redistribute_silica().
"""

from __future__ import annotations

from io import BytesIO
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from typing import Any, Mapping

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def _safe(value: Any) -> str:
    """Convert arbitrary values to XML-safe text."""
    return escape(str(value))


def _number(value: Any, digits: int = 8) -> str:
    """Format a numeric value without silently inventing a value."""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError, OverflowError):
        return _safe(value)


def _format_products(products: Any) -> str:
    """Format products_formed dictionaries as readable mineral amounts."""

    if not isinstance(products, Mapping):
        return _safe(products)

    if not products:
        return "None"

    parts = []

    for mineral, amount in products.items():
        parts.append(
            f"{_safe(mineral)} = {_number(amount, 10)}"
        )

    return "; ".join(parts)


def _section(title: str, styles: Mapping[str, Any]) -> Paragraph:
    """Create a section heading."""
    return Paragraph(_safe(title), styles["Section"])


def _make_table(
    data: list[list[Any]],
    *,
    widths: list[float] | None = None,
    header: bool = True,
    compact: bool = False,
) -> Table:
    """Create a wrapping, repeat-header, page-splittable table."""

    if not data:
        data = [["No data"]]

    base_styles = getSampleStyleSheet()

    cell_style = ParagraphStyle(
        "ScientificTableCell",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2 if compact else 8,
        leading=9 if compact else 10,
        spaceAfter=0,
        spaceBefore=0,
        wordWrap="CJK",
    )

    header_style = ParagraphStyle(
        "ScientificTableHeader",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    wrapped_data = []

    for row_index, row in enumerate(data):
        wrapped_row = []

        for value in row:
            style = (
                header_style
                if header and row_index == 0
                else cell_style
            )

            wrapped_row.append(
                Paragraph(str(value), style)
            )

        wrapped_data.append(wrapped_row)

    table = Table(
        wrapped_data,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
        splitByRow=1,
        splitInRow=0,
    )

    commands = [
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            colors.HexColor("#B8C2CC"),
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3 if compact else 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 if compact else 4),
    ]

    if header:
        commands.extend([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#263B53"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
        ])

        if len(data) > 1:
            commands.append(
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F1F4F7"),
                    ],
                )
            )

    table.setStyle(TableStyle(commands))

    return table


# ------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------

def _page_footer(canvas, document) -> None:
    """Draw page number and report identity."""

    canvas.saveState()

    width, _ = A4

    canvas.setStrokeColor(colors.HexColor("#B8C2CC"))
    canvas.setLineWidth(0.4)

    canvas.line(
        18 * mm,
        15 * mm,
        width - 18 * mm,
        15 * mm,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#536273"))

    canvas.drawString(
        18 * mm,
        10 * mm,
        "CIPW Norm Studio | Classical Kelsey (1965)",
    )

    canvas.drawRightString(
        width - 18 * mm,
        10 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ------------------------------------------------------------------
# Main PDF generator
# ------------------------------------------------------------------

def generate_cipw_pdf_report(
    *,
    result: Any,
    sample_id: str,
    major_oxide_input: Mapping[str, float],
    optional_measurements: Mapping[str, Any],
    sulfur_basis: str,
    carbonate_mode: str,
    volatile_free: bool,
    assume_unmeasured_zero: bool,
    metadata: Mapping[str, str] | None = None,
) -> bytes:
    """Generate a scientific CIPW Norm PDF report."""

    metadata = dict(metadata or {})
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=21 * mm,
        title=f"CIPW Norm Report - {sample_id}",
        author="CIPW Norm Studio",
        subject="Classical Kelsey (1965) normative mineral calculation",
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "Title": ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#19324D"),
            spaceAfter=3 * mm,
        ),
        "Subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base_styles["Normal"],
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#536273"),
            spaceAfter=5 * mm,
        ),
        "Section": ParagraphStyle(
            "ReportSection",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#19324D"),
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "ReportBody",
            parent=base_styles["BodyText"],
            fontSize=8,
            leading=10,
            spaceAfter=1.5 * mm,
        ),
        "Subheading": ParagraphStyle(
            "ReportSubheading",
            parent=base_styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            spaceBefore=1.5 * mm,
            spaceAfter=1 * mm,
            keepWithNext=True,
        ),
        "Small": ParagraphStyle(
            "ReportSmall",
            parent=base_styles["BodyText"],
            fontSize=7.2,
            leading=9,
            spaceAfter=1 * mm,
        ),
        "Warning": ParagraphStyle(
            "ReportWarning",
            parent=base_styles["BodyText"],
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor("#8A3B12"),
            backColor=colors.HexColor("#FFF3E5"),
            borderColor=colors.HexColor("#E5B77A"),
            borderWidth=0.5,
            borderPadding=4,
            spaceAfter=1.5 * mm,
        ),
    }

    story: list[Any] = []

    # --------------------------------------------------------------
    # Report identification
    # --------------------------------------------------------------

    story.append(
        Paragraph("CIPW NORM STUDIO", styles["Title"])
    )

    story.append(
        Paragraph(
            "Scientific Normative Mineral Calculation Report",
            styles["Subtitle"],
        )
    )

    story.append(
        Paragraph(
            "<b>Calculation method:</b> "
            "Classical CIPW Norm - Kelsey (1965)",
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Sample ID:</b> {_safe(sample_id)}",
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "<b>Report generated (UTC):</b> "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Body"],
        )
    )

    metadata_rows = [["Metadata field", "Value"]]

    for key, value in metadata.items():
        metadata_rows.append([
            _safe(key),
            _safe(value or "Not supplied"),
        ])

    if len(metadata_rows) > 1:
        story.append(Spacer(1, 1 * mm))
        story.append(
            _make_table(
                metadata_rows,
                widths=[48 * mm, 115 * mm],
                compact=True,
            )
        )

    # --------------------------------------------------------------
    # 1. Calculation status
    # --------------------------------------------------------------

    story.append(
        _section("1. Calculation status", styles)
    )

    status_rows = [
        ["Parameter", "Result"],
        ["Calculation status", _safe(result.status)],
        ["Method", _safe(result.method)],
        ["Mass-balance status", _safe(result.mass_balance.status)],
        ["Conditional calculation", str(bool(result.conditional))],
        [
            "Total normative mass (g)",
            _number(result.total_normative_mass, 8),
        ],
        [
            "Silica deficiency remaining",
            _number(
                result.redistribution_result.final_deficiency,
                10,
            ),
        ],
    ]

    story.append(
        _make_table(
            status_rows,
            widths=[70 * mm, 93 * mm],
            compact=True,
        )
    )

    # --------------------------------------------------------------
    # 2. Major oxide composition
    # --------------------------------------------------------------

    story.append(
        _section("2. Major oxide composition", styles)
    )

    oxide_rows = [
        ["Oxide", "Analytical concentration (wt.%)"]
    ]

    for oxide, value in major_oxide_input.items():
        oxide_rows.append([
            _safe(oxide),
            _number(value, 8),
        ])

    oxide_total = sum(
        float(value) for value in major_oxide_input.values()
    )

    oxide_rows.append([
        "Total",
        _number(oxide_total, 8),
    ])

    story.append(
        _make_table(
            oxide_rows,
            widths=[65 * mm, 98 * mm],
            compact=True,
        )
    )

    # --------------------------------------------------------------
    # 3. Optional-component measurements
    # --------------------------------------------------------------

    story.append(
        _section("3. Optional-component measurements", styles)
    )

    optional_rows = [[
        "Component",
        "Measurement status",
        "Value (wt.%)",
    ]]

    for component, record in optional_measurements.items():

        if isinstance(record, Mapping):
            status = record.get("status", "unknown")
            value = record.get("value_wt_percent")
        else:
            status = "unknown"
            value = None

        optional_rows.append([
            _safe(component),
            _safe(status),
            (
                "Not available"
                if value is None
                else _number(value, 8)
            ),
        ])

    story.append(
        _make_table(
            optional_rows,
            widths=[43 * mm, 63 * mm, 57 * mm],
            compact=True,
        )
    )

    # --------------------------------------------------------------
    # 4. Calculation settings
    # --------------------------------------------------------------

    story.append(
        _section("4. Calculation settings", styles)
    )

    setting_rows = [
        ["Setting", "Selected value"],
        ["Sulfur basis", _safe(sulfur_basis)],
        ["Carbonate treatment", _safe(carbonate_mode)],
        ["Volatile-free normalization", str(bool(volatile_free))],
        [
            "Allow unmeasured components as zero",
            str(bool(assume_unmeasured_zero)),
        ],
    ]

    story.append(
        _make_table(
            setting_rows,
            widths=[85 * mm, 78 * mm],
            compact=True,
        )
    )


    # --------------------------------------------------------------
    # 5A. Published reference benchmark comparison
    # --------------------------------------------------------------

    from src.reference_benchmarks import (
        BOSTONITE_KELSEY_1965,
        compare_bostonite_reference,
    )

    benchmark_rows = compare_bostonite_reference(
        result.final_minerals,
        major_oxide_input,
    )

    if benchmark_rows is not None:

        story.append(
            _section(
                "5A. Published reference benchmark comparison",
                styles,
            )
        )

        story.append(
            Paragraph(
                _safe(BOSTONITE_KELSEY_1965["reference"]),
                styles["Small"],
            )
        )

        story.append(
            Paragraph(
                "Comparison basis: absolute difference in molecular "
                "proportions. Acceptance tolerance: "
                f"{_number(BOSTONITE_KELSEY_1965['tolerance'], 6)}.",
                styles["Small"],
            )
        )

        benchmark_table = [[
            "Mineral",
            "Published",
            "Studio",
            "Absolute difference",
            "Tolerance",
            "Result",
        ]]

        for row in benchmark_rows:
            benchmark_table.append([
                _safe(row.mineral),
                _number(row.published, 6),
                _number(row.calculated, 8),
                _number(row.absolute_difference, 8),
                _number(row.tolerance, 6),
                "PASS" if row.passed else "FAIL",
            ])

        story.append(
            _make_table(
                benchmark_table,
                widths=[
                    18 * mm,
                    24 * mm,
                    25 * mm,
                    34 * mm,
                    25 * mm,
                    20 * mm,
                ],
                compact=True,
            )
        )

        passed_count = sum(
            row.passed for row in benchmark_rows
        )

        total_count = len(benchmark_rows)

        story.append(
            Paragraph(
                f"<b>Benchmark result:</b> {passed_count} of "
                f"{total_count} published mineral amounts "
                "within tolerance.",
                styles["Body"],
            )
        )

        story.append(
            Paragraph(
                "<b>Reference assumptions:</b> "
                + _safe(BOSTONITE_KELSEY_1965["assumptions"]),
                styles["Small"],
            )
        )

        story.append(
            Paragraph(
                "<b>Interpretation:</b> This is a comparison against "
                "published values rounded to three decimal places. "
                "It is not an exact independent recalculation of "
                "the original analysis.",
                styles["Small"],
            )
        )


    # --------------------------------------------------------------
    # 6. Kelsey allocation audit
    # --------------------------------------------------------------

    story.append(
        _section("6. Kelsey allocation audit", styles)
    )

    provisional = result.provisional_result
    redistribution = result.redistribution_result

    audit_symbols = sorted(
        set(provisional.minerals)
        | set(redistribution.minerals)
    )

    audit_rows = [[
        "Mineral",
        "Provisional amount",
        "Final amount",
        "Change",
    ]]

    for symbol in audit_symbols:

        initial = float(
            provisional.minerals.get(symbol, 0.0)
        )

        final = float(
            redistribution.minerals.get(symbol, 0.0)
        )

        audit_rows.append([
            _safe(symbol),
            _number(initial, 10),
            _number(final, 10),
            _number(final - initial, 10),
        ])

    story.append(
        _make_table(
            audit_rows,
            widths=[
                35 * mm,
                43 * mm,
                43 * mm,
                42 * mm,
            ],
            compact=True,
        )
    )

    story.append(
        Paragraph(
            "<b>Initial silica deficiency:</b> "
            f"{_number(redistribution.initial_deficiency, 12)}",
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "<b>Final silica deficiency:</b> "
            f"{_number(redistribution.final_deficiency, 12)}",
            styles["Body"],
        )
    )

    # --------------------------------------------------------------
    # 7. Silica-deficiency redistribution steps
    # --------------------------------------------------------------

    story.append(
        _section(
            "7. Silica-deficiency redistribution steps",
            styles,
        )
    )

    if redistribution.steps:

        step_rows = [[
            "Rule",
            "Reaction",
            "Deficiency before",
            "Amount converted",
            "Products formed",
            "Deficiency after",
        ]]

        for step in redistribution.steps:

            if not isinstance(step, Mapping):
                raise TypeError(
                    "Redistribution step must be a dictionary; "
                    f"received {type(step).__name__}."
                )

            step_rows.append([
                _safe(step.get("rule", "Unknown")),
                _safe(step.get("reaction", "Not recorded")),
                _number(step.get("deficiency_before"), 10),
                _number(
                    step.get("provisional_amount_converted"),
                    10,
                ),
                _safe(
                    _format_products(
                        step.get("products_formed", {})
                    )
                ),
                _number(step.get("deficiency_after"), 10),
            ])

        story.append(
            _make_table(
                step_rows,
                widths=[
                    12 * mm,
                    43 * mm,
                    25 * mm,
                    27 * mm,
                    31 * mm,
                    25 * mm,
                ],
                compact=True,
            )
        )

    else:
        story.append(
            Paragraph(
                "No silica-deficiency redistribution steps were required.",
                styles["Body"],
            )
        )

    # --------------------------------------------------------------
    # 8. Component mass-balance verification
    # --------------------------------------------------------------

    story.append(
        _section(
            "8. Component mass-balance verification",
            styles,
        )
    )

    balance = result.mass_balance

    balance_rows = [
        ["Diagnostic", "Value"],
        ["Balanced", str(bool(balance.balanced))],
        ["Mass-balance status", _safe(balance.status)],
        [
            "Maximum non-silica error",
            _number(balance.max_non_silica_error, 12),
        ],
        [
            "Silica error",
            _number(balance.silica_error, 12),
        ],
        [
            "Expected silica deficit",
            _number(balance.expected_silica_deficit, 12),
        ],
        [
            "Tolerance",
            _number(balance.tolerance, 12),
        ],
    ]

    story.append(
        _make_table(
            balance_rows,
            widths=[85 * mm, 78 * mm],
            compact=True,
        )
    )

    component_rows = [["Component", "Difference"]]

    for component, difference in balance.component_differences.items():
        component_rows.append([
            _safe(component),
            _number(difference, 12),
        ])

    if len(component_rows) > 1:
        story.append(Spacer(1, 1 * mm))
        story.append(
            _make_table(
                component_rows,
                widths=[70 * mm, 93 * mm],
                compact=True,
            )
        )


    # --------------------------------------------------------------
    # 9. Calculation intermediates
    # --------------------------------------------------------------

    intermediate_groups = [
        (
            "Major oxide molecular proportions",
            result.major_oxide_moles,
        ),
        (
            "Optional-component molecular proportions",
            result.optional_component_moles,
        ),
        (
            "Provisional residual oxides",
            provisional.residual_oxides,
        ),
        (
            "Provisional mineral allocation",
            provisional.minerals,
        ),
    ]

    # Build the first subsection separately so the main section
    # heading stays with its first intermediate table.
    first_heading, first_values = intermediate_groups[0]

    first_rows = [["Component", "Value"]]

    for key, value in first_values.items():
        first_rows.append([
            _safe(key),
            _number(value, 12),
        ])

    first_table = _make_table(
        first_rows,
        widths=[70 * mm, 93 * mm],
        compact=True,
    )

    story.append(
        KeepTogether([
            _section("9. Calculation intermediates", styles),
            Paragraph(
                _safe(first_heading),
                styles["Subheading"],
            ),
            first_table,
        ])
    )

    story.append(Spacer(1, 1 * mm))

    # Remaining intermediate subsections.
    for heading, values in intermediate_groups[1:]:

        intermediate_rows = [["Component", "Value"]]

        for key, value in values.items():
            intermediate_rows.append([
                _safe(key),
                _number(value, 12),
            ])

        intermediate_table = _make_table(
            intermediate_rows,
            widths=[70 * mm, 93 * mm],
            compact=True,
        )

        story.append(
            KeepTogether([
                Paragraph(
                    _safe(heading),
                    styles["Subheading"],
                ),
                intermediate_table,
            ])
        )

        story.append(Spacer(1, 1 * mm))

    # Rule 19 and apatite calculation intermediates.
    story.append(
        Paragraph(
            "<b>Rule 19 Mg fraction:</b> "
            f"{_number(provisional.mg_fraction, 10)}",
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "<b>Rule 19 Fe fraction:</b> "
            f"{_number(provisional.fe_fraction, 10)}",
            styles["Body"],
        )
    )

    story.append(
        Paragraph(
            "<b>Apatite fluorine allocation:</b> "
            f"{_number(provisional.apatite_fluorine_amount, 12)}",
            styles["Body"],
        )
    )



    # --------------------------------------------------------------
    # 10. Scientific warnings, assumptions and references
    # --------------------------------------------------------------

    warnings = list(dict.fromkeys(
        str(warning) for warning in result.warnings
    ))

    has_conditional_warning = any(
        "conditional" in warning.lower()
        for warning in warnings
    )

    if result.conditional and not has_conditional_warning:
        warnings.append(
            "CONDITIONAL RESULT: one or more optional components "
            "were unmeasured and assumed absent. This is not "
            "equivalent to measured zero."
        )

    # Build the complete final section as one pagination group.
    final_section = [
        _section(
            "10. Scientific warnings and assumptions",
            styles,
        )
    ]

    if not warnings:
        final_section.append(
            Paragraph(
                "No calculation warnings were reported.",
                styles["Body"],
            )
        )
    else:
        for warning in warnings:
            final_section.append(
                Paragraph(
                    _safe(warning),
                    styles["Warning"],
                )
            )

    final_section.extend([
        Spacer(1, 2 * mm),

        Paragraph(
            "<b>Methodological statement:</b> This report records a "
            "Classical CIPW Norm calculation using the Kelsey (1965) "
            "procedure implemented in CIPW Norm Studio. The normative "
            "assemblage is a calculated idealized mineral allocation; "
            "it is not a direct measurement of modal mineral abundance.",
            styles["Small"],
        ),

        Spacer(1, 1 * mm),

        Paragraph(
            "Reference: Kelsey, C.H. (1965). Calculation of the "
            "C.I.P.W. norm. Mineralogical Magazine, 34(268), "
            "276–282. "
            "https://doi.org/10.1180/minmag.1965.034.268.23",
            styles["Small"],
        ),
    ])

    story.append(KeepTogether(final_section))

    # --------------------------------------------------------------
    # Build document
    # --------------------------------------------------------------

    document.build(
        story,
        onFirstPage=_page_footer,
        onLaterPages=_page_footer,
    )

    return buffer.getvalue()


    # --------------------------------------------------------------
    # Build document
    # --------------------------------------------------------------

    document.build(
        story,
        onFirstPage=_page_footer,
        onLaterPages=_page_footer,
    )

    return buffer.getvalue()
