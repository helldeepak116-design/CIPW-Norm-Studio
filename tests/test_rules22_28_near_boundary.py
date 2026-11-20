import pytest

from src.kelsey_silica_deficiency import redistribute_silica


EPSILON = 1e-8
TOLERANCE = 1e-10


CASES = [
    # Rule 22: Hy -> Ol; 1 Hy releases 0.5 SiO2.
    (
        "rule22_below",
        {"hy": 0.1},
        0.05 - EPSILON,
        [22],
        {"hy": 2 * EPSILON, "ol": 0.05 - EPSILON},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule22_at",
        {"hy": 0.1},
        0.05,
        [22],
        {"hy": 0.0, "ol": 0.05},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule22_above",
        {"hy": 0.1},
        0.05 + EPSILON,
        [22],
        {"hy": 0.0, "ol": 0.05},
        EPSILON,
        0.0,
        "UNRESOLVED_DEFICIENCY",
    ),

    # Rule 23: Tn -> Pf; 1 Tn releases 1 SiO2.
    (
        "rule23_below",
        {"tn": 0.1},
        0.1 - EPSILON,
        [23],
        {"tn": EPSILON, "pf": 0.1 - EPSILON},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule23_at",
        {"tn": 0.1},
        0.1,
        [23],
        {"tn": 0.0, "pf": 0.1},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule23_above",
        {"tn": 0.1},
        0.1 + EPSILON,
        [23],
        {"tn": 0.0, "pf": 0.1},
        EPSILON,
        0.0,
        "UNRESOLVED_DEFICIENCY",
    ),

    # Rule 24: Ab -> Ne; 1 Ab releases 4 SiO2.
    (
        "rule24_below",
        {"ab": 0.1},
        0.4 - EPSILON,
        [24],
        {"ab": EPSILON / 4, "ne": 0.1 - EPSILON / 4},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule24_at",
        {"ab": 0.1},
        0.4,
        [24],
        {"ab": 0.0, "ne": 0.1},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule24_above",
        {"ab": 0.1},
        0.4 + EPSILON,
        [24],
        {"ab": 0.0, "ne": 0.1},
        EPSILON,
        0.0,
        "UNRESOLVED_DEFICIENCY",
    ),

    # Rules 25 + 28: Or -> provisional Lc -> Kp.
    # Together they can release 4 SiO2 per Or.
    (
        "rules25_28_below",
        {"or": 0.1},
        0.4 - EPSILON,
        [25, 28],
        {
            "or": 0.0,
            "lc": EPSILON / 2,
            "kp": 0.1 - EPSILON / 2,
        },
        0.0,
        EPSILON / 2,
        "COMPLETED",
    ),
    (
        "rules25_28_at",
        {"or": 0.1},
        0.4,
        [25, 28],
        {"or": 0.0, "lc": 0.0, "kp": 0.1},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rules25_28_above",
        {"or": 0.1},
        0.4 + EPSILON,
        [25, 28],
        {"or": 0.0, "lc": 0.0, "kp": 0.1},
        EPSILON,
        0.0,
        "UNRESOLVED_DEFICIENCY",
    ),

    # Rule 26: Wo -> Cs; 1 Wo releases 0.5 SiO2.
    (
        "rule26_below",
        {"wo": 0.1},
        0.05 - EPSILON,
        [26],
        {"wo": 2 * EPSILON, "cs": 0.05 - EPSILON},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule26_at",
        {"wo": 0.1},
        0.05,
        [26],
        {"wo": 0.0, "cs": 0.05},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule26_above",
        {"wo": 0.1},
        0.05 + EPSILON,
        [26],
        {"wo": 0.0, "cs": 0.05},
        EPSILON,
        0.0,
        "UNRESOLVED_DEFICIENCY",
    ),

    # Rule 27: Di -> 0.5 Cs + 0.5 Ol; 1 Di releases 1 SiO2.
    (
        "rule27_below",
        {"di": 0.1},
        0.1 - EPSILON,
        [27],
        {
            "di": EPSILON,
            "cs": (0.1 - EPSILON) / 2,
            "ol": (0.1 - EPSILON) / 2,
        },
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule27_at",
        {"di": 0.1},
        0.1,
        [27],
        {"di": 0.0, "cs": 0.05, "ol": 0.05},
        0.0,
        0.0,
        "COMPLETED",
    ),
    (
        "rule27_above",
        {"di": 0.1},
        0.1 + EPSILON,
        [27],
        {"di": 0.0, "cs": 0.05, "ol": 0.05},
        EPSILON,
        0.0,
        "UNRESOLVED_DEFICIENCY",
    ),
]


@pytest.mark.parametrize(
    (
        "case_name",
        "initial_minerals",
        "initial_deficiency",
        "expected_rules",
        "expected_minerals",
        "expected_deficiency",
        "expected_lc_prime_remaining",
        "expected_status",
    ),
    CASES,
    ids=[case[0] for case in CASES],
)
def test_rules22_to_28_near_conversion_boundaries(
    case_name,
    initial_minerals,
    initial_deficiency,
    expected_rules,
    expected_minerals,
    expected_deficiency,
    expected_lc_prime_remaining,
    expected_status,
):
    result = redistribute_silica(
        initial_minerals,
        initial_deficiency,
    )

    assert [step["rule"] for step in result.steps] == expected_rules

    for mineral, expected_amount in expected_minerals.items():
        assert result.minerals[mineral] == pytest.approx(
            expected_amount,
            abs=TOLERANCE,
        )

    assert result.final_deficiency == pytest.approx(
        expected_deficiency,
        abs=TOLERANCE,
    )
    assert result.lc_prime_remaining == pytest.approx(
        expected_lc_prime_remaining,
        abs=TOLERANCE,
    )
    assert result.status == expected_status

    # All generated mineral amounts must remain non-negative.
    assert all(
        amount >= 0.0
        for amount in result.minerals.values()
    )
    assert result.lc_prime_remaining >= 0.0
    assert result.final_deficiency >= 0.0
