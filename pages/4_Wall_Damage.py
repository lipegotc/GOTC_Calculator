import streamlit as st
import pandas as pd

from models import siege
from calculator import calc_wall_damage
from data import load_siegestats, load_sophealth


st.set_page_config(page_title="Wall Damage", page_icon="🧱🧱")
header = st.header("Wall Damage Calculator")

st.markdown("This will calculate the % damage you can do vs a certain Seat of Power (2* - 5*) based on your stats.")

st.markdown("It supports T11 and T12 Siege stats.")

@st.cache_data
def load_data():
    return load_siegestats(), load_sophealth()

siege_by_tier, sop_by_star = load_data()

with st.form("wdb_form"):
    st.header("Wall Damage Calculator")

    siegeTier = st.number_input(
        "Siege Tier",
        min_value=11,
        max_value=12,
        step=1,
        value=11,
    )

    msize = st.number_input(
        "March Size",
        min_value=1,
        step=1,
        value=100_000,
    )

    wdbstat = st.number_input(
        "Wall Damage Bonus (percent)",
        help="Enter 150 for 150% wall damage bonus",
        min_value=0.0,
        step=1.0,
        value=0.0,
    )

    starnum = st.selectbox(
        "Seat of Power Stars",
        options=sorted(sop_by_star.keys()),
        index=0,
    )

    submitted = st.form_submit_button("Calculate Wall Damage")

if submitted:
    siege_obj = siege.from_dict({
        "tier": siegeTier,
        "msize": msize,
        "wdb": wdbstat,
    })

    result = calc_wall_damage(
        siege_input=siege_obj,
        sop_stars=starnum,
        siege_by_tier=siege_by_tier,
        sop_by_star=sop_by_star,
    )

    df = pd.DataFrame([{
        "SOP Star": result["inputs"]["sop_stars"],
        "Player Tier": result["inputs"]["tier"],
        "Raw Damage": round(result["results"]["raw_damage"], 0),
        "Damage Percent": f'{result["results"]["percent_damage_pct"]:.2f}%',
    }])

    st.subheader("Wall Damage Result")
    st.dataframe(df, use_container_width=True)