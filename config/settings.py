
"""Central application settings for CIPW Norm Studio."""

from pathlib import Path

APP_NAME = "CIPW Norm Studio"
APP_VERSION = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
REFERENCE_DIR = DATA_DIR / "reference"
SAMPLE_DIR = DATA_DIR / "sample"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
CALCULATION_DIR = OUTPUT_DIR / "calculations"
PLOT_DIR = OUTPUT_DIR / "plots"
REPORT_DIR = OUTPUT_DIR / "reports"

# Scientific calculation configuration
CALCULATION_METHOD = "Classical CIPW Norm - Kelsey (1965)"
IRON_HANDLING = "measured"

# Analytical validation
MINIMUM_OXIDE_VALUE = 0.0
MAXIMUM_OXIDE_VALUE = 100.0

# Analytical total is checked, not silently normalized.
ANALYTICAL_TOTAL_MIN = 95.0
ANALYTICAL_TOTAL_MAX = 105.0

# Numerical tolerance for calculations.
NUMERICAL_TOLERANCE = 1e-10

# Default output precision.
OUTPUT_DECIMAL_PLACES = 4

# Required major-element oxides.
REQUIRED_OXIDES = [
    "SiO2",
    "TiO2",
    "Al2O3",
    "Fe2O3",
    "FeO",
    "MnO",
    "MgO",
    "CaO",
    "Na2O",
    "K2O",
    "P2O5",
]

# Create application directories if they do not exist.
for directory in [
    INPUT_DIR,
    REFERENCE_DIR,
    SAMPLE_DIR,
    CALCULATION_DIR,
    PLOT_DIR,
    REPORT_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
