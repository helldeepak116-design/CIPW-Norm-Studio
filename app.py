
"""Main Streamlit application for CIPW Norm Studio."""

import streamlit as st

from config.settings import (
    APP_NAME,
    APP_VERSION,
    CALCULATION_METHOD,
    IRON_HANDLING,
    REQUIRED_OXIDES,
)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🪨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🪨 CIPW Norm Studio")

st.caption(
    "Scientific calculation, interpretation and visualization "
    "of normative mineralogy."
)

st.markdown("---")

st.subheader("Welcome")

st.write(
    """
    CIPW Norm Studio is a scientific application for calculating
    and interpreting normative mineral assemblages from whole-rock
    major-element geochemical compositions.
    """
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Application version", APP_VERSION)

with col2:
    st.metric("Supported major oxides", len(REQUIRED_OXIDES))

with col3:
    st.metric("Iron handling", "Measured FeO / Fe₂O₃")

st.markdown("---")

st.subheader("Calculation methodology")

st.info(
    f"""
    **Method:** {CALCULATION_METHOD}

    **Iron convention:** {IRON_HANDLING}

    Measured FeO and Fe₂O₃ are retained independently.
    The application will not silently assume an iron oxidation ratio.
    """
)

st.subheader("Available calculation inputs")

st.dataframe(
    {
        "Oxide": REQUIRED_OXIDES,
        "Input unit": ["wt.%"] * len(REQUIRED_OXIDES),
    },
    width="stretch",
    hide_index=True,
)

st.markdown("---")

st.warning(
    "The calculation engine is currently under development. "
    "No normative mineral values are calculated by this initial interface."
)

st.caption(
    "CIPW Norm Studio | Developed for scientific and educational use."
)

