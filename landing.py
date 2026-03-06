import streamlit as st

st.set_page_config(
    page_title="GOTC Calculators",)

st.write("# Welcome to the GOTC Calculators page!")

st.sidebar.success("Select a calculator above.")

st.markdown("""
This page hosts various calculators to help you optimize your gameplay in GOTC. Select a calculator available from the sidebar.

Calculators currently available:

- **Dragon vs Dragon Calculator**: Estimate damage and healing costs in dragon battle.

- **Stats Calculator**: similar to the old GOTC Tips PVP Calculator, the Stats Calculator calculates your "true stats" on PVP occasions and also compares to theoretical maxed stats for your troop type.

- **Battle Simulator**: Simulate battles between attackers and defenders for 2 scenarios - Solo Attacker vs Solo Defender & Rally vs Multi Defender.

- **Wall Damage Calculator**: Estimate total damage you can do vs a SOP's wall.

Most inputs have default values so you don't have to type out every single value, adjust as needed.

This is an unofficial fan-made tool and is not affiliated with WB Games. All rights reserved to their respective owners.
            
Questions or suggestions? Message me on Discord (Lipeeeee).

""")