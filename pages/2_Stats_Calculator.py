import streamlit as st
from calculator import statsCalculator, statsComparator
import pandas as pd

header = st.header("Stats Calculator 📊")
st.set_page_config(page_title="Stats Calculator", page_icon="📊")
st.sidebar.header("Stats Calculator 📊")

st.markdown("Enter your troop stats below WITHOUT % symbol (e.g., enter 1500 for 1500%) for Attacker scenario and Defender scenario. The calculator will provide your effective stats on PVP occasions\n")

def stats_submitted():
    st.header("PVP Stats and Comparison vs Maxed Stats")

    if submitted:
        st.subheader("Comparison Results")
        comparison_results = statsComparator(
            troop_type_json=troopTypeAtt,
            attacker={
                "baseatkbuff": float(baseTroopTypeBuffAtt),
                "marcheratkbuff": float(baseMarcherAttackBuffAtt),
                "atkvscav": float(atkvscavAtt),
                "atkvsinf": float(atkvsinfAtt),
                "atkvsrng": float(atkvsrngAtt),
            },
            defender={
                "basedefbuff": float(baseTroopTypeDefenseBuffDef),
                "basehealthbuff": float(baseTroopTypeHealthBuffDef),
                "defatsopbuff": float(defatsopDef),
                "healthatsopbuff": float(healthatsopDef),
                "defvscav": float(defvscavDef),
                "defvsinf": float(defvsinfDef),
                "defvsrng": float(defvsrngDef),
                "defdefensebuff": float(defDefenseBuffDef),
                "defhealthbuff": float(defHealthBuffDef),
            }
        )
        atk_comp = comparison_results["comparison"]["attacker_vs_maxed"]
        k_cav = "Total Attack vs Cavalry"
        k_rng = "Total Attack vs Ranged"
        k_inf = "Total Attack vs Infantry"

        def_comp = comparison_results["comparison"]["defender_vs_maxed"]  
        k_hp  = "Total Health"
        k_defcav = "Total Defense vs Cavalry"
        k_definf = "Total Defense vs Infantry"
        k_defrng = "Total Defense vs Ranged"

        dfAtk = pd.DataFrame([
            {
                "Player": "Player",
                "Troop Type": troopTypeAtt,
                "Attack vs Cavalry": atk_comp[k_cav]["player"],
                "Attack vs Ranged": atk_comp[k_rng]["player"],
                "Attack vs Infantry": atk_comp[k_inf]["player"],
            },
            {
                "Player": "Maxed",
                "Troop Type": troopTypeAtt,
                "Attack vs Cavalry": atk_comp[k_cav]["maxed"],
                "Attack vs Ranged": atk_comp[k_rng]["maxed"],
                "Attack vs Infantry": atk_comp[k_inf]["maxed"],
            },
            {
                "Player": "Difference",
                "Troop Type": troopTypeAtt,
                "Attack vs Cavalry": atk_comp[k_cav]["diff_pct"],
                "Attack vs Ranged": atk_comp[k_rng]["diff_pct"],
                "Attack vs Infantry": atk_comp[k_inf]["diff_pct"],
            },
        ])

        dfDef = pd.DataFrame([
            {
                "Player": "Player",
                "Troop Type": troopTypeAtt,
                "Health": def_comp[k_hp]["player"],
                "Defense vs Cavalry": def_comp[k_defcav]["player"],
                "Defense vs Infantry": def_comp[k_definf]["player"],
                "Defense vs Ranged": def_comp[k_defrng]["player"],
            },
            {
                "Player": "Maxed",
                "Troop Type": troopTypeAtt,
                "Health": def_comp[k_hp]["maxed"],
                "Defense vs Cavalry": def_comp[k_defcav]["maxed"],
                "Defense vs Infantry": def_comp[k_definf]["maxed"],
                "Defense vs Ranged": def_comp[k_defrng]["maxed"],
            },
            {
                "Player": "Difference",
                "Troop Type": troopTypeAtt,
                "Health": def_comp[k_hp]["diff_pct"],
                "Defense vs Cavalry": def_comp[k_defcav]["diff_pct"],
                "Defense vs Infantry": def_comp[k_definf]["diff_pct"],
                "Defense vs Ranged": def_comp[k_defrng]["diff_pct"],
            },
        ])
        st.subheader("Attacker Results")
        st.dataframe(dfAtk, use_container_width=True)
        st.subheader("Defender Results")
        st.dataframe(dfDef, use_container_width=True)

TierAtt = st.number_input("Troop Tier (1-12)", min_value=1, max_value=12, value=1, step=1, key="trooptier")
troopTypeAtt = st.selectbox("Troop Type", ["Infantry", "Ranged", "Cavalry"], key="trooptype")

with st.form("stats_form"):
    attackerStats, defenderStats = st.columns(2)
    with attackerStats:
        
        st.subheader("Attacker Stats")
        
        baseTroopTypeBuffAtt = st.text_input("Base Troop Type Attack Buff", "0", key="attackerbasetrooptypebuff")
        baseMarcherAttackBuffAtt = st.text_input("Marcher Attack Buff", "0", key="attackermarcheratkbuff")
        atkvscavAtt = st.text_input("Attack vs Cavalry Buff", "0", key="attackeratkvscav")
        atkvsrngAtt = st.text_input("Attack vs Ranged Buff", "0", key="attackeratkvsrng")
        atkvsinfAtt = st.text_input("Attack vs Infantry Buff", "0", key="attackeratkvsinf")
    with defenderStats:
        st.subheader("Defender Stats")
        baseTroopTypeDefenseBuffDef = st.text_input("Base Troop Type Defense Buff", "0", key="defenderbasetroopdefbuff")
        baseTroopTypeHealthBuffDef = st.text_input("Base Troop Type Health Buff", "0", key="defenderbasetroophealthbuff")

        defvscavDef = st.text_input("Defense vs Cavalry Buff", "0", key="defenderdefvscav")
        defvsrngDef = st.text_input("Defense vs Ranged Buff", "0", key="defenderdefvsrng")
        defvsinfDef = st.text_input("Defense vs Infantry Buff", "0", key="defenderdefvsinf")

        defatsopDef = st.text_input("Defense at SOP Buff", "0", key="defenderdefatsopbuff")
        healthatsopDef = st.text_input("Health at SOP Buff", "0", key="defenderhealthatsopbuff")

        defDefenseBuffDef = st.text_input("Defender Defense Buff", "0", key="defenderdefenderdefbuff")
        defHealthBuffDef = st.text_input("Defender Health Buff", "0", key="defenderdefenderhealthbuff")
        submitted = st.form_submit_button("Submit")
    if submitted:
        st.write("Form submitted successfully!")
        stats_submitted()

