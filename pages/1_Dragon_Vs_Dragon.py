import streamlit as st
from models import DragonInfo
from calculator import dvdcalc_duel
import pandas as pd

st.set_page_config(page_title="Dragon vs Dragon Calculator", page_icon=":dragon:", layout="wide")
header = st.header("Dragon Calculator")
st.sidebar.header("Dragon vs Dragon Calculator")
st.markdown("Enter Attacker and Defender's Dragon stats below **WITHOUT** % symbol for buffs (e.g., enter 1500 for 1500%).")

st.markdown("Calculator will give as result:\n" \
"- An **estimation** of the damage dealt by both sides (doesn't take into account damage done by player's troops, only Dragon vs Dragon); \n" \
"- Gold costs for healing the dragon." \
"")

st.markdown("On the Dragon **DEFENSE** input, enter the **LOWEST** defense value.")

st.markdown("On the **'Stat Changes (+/-)'** sections, you can input the changes in stats to see how they affect the battle outcome. Remember to enter + or - signs for the respective change.")
with st.form("dragon_stats_form"):

    dragonAttacker, dragonDefender = st.columns(2)
    with dragonAttacker:
        st.header("Attacker's Dragon Stats")
        LevelAtt = st.text_input("Dragon Level", "69", key="attackerlvl" )
        DvdAttAtt = st.text_input("Dragon vs Dragon Attack", "1570", key="attackerdvdatt" )
        DvdDefAtt = st.text_input("Dragon Defense (LOWEST NUMBER)", "300", key="attackerdvddef" )
        DvdHealthAtt = st.text_input("Dragon Health Bonus", "190", key="attackerdvdhealth" )
        RegenrateAtt = st.text_input("Dragon Regen Rate", "15", key="attackerdvdregenrate" )

        st.subheader("Stat Changes (+/-)")
        LevelAttChange = st.text_input("Dragon Level Change", "0", key="attackerlvlchange")
        DvdAttAttChange = st.text_input("Dragon vs Dragon Attack Change", "0", key="attackerdvdattchange")
        DvdDefAttChange = st.text_input("Dragon Defense Change", "0", key="attackerdvddefchange")
        DvdHealthAttChange = st.text_input("Dragon Health Bonus Change", "0", key="attackerdvdhealthchange")
        RegenrateAttChange = st.text_input("Dragon Regen Rate Change", "0", key="attackerdvdregenratechange")

        dragon_attacker = DragonInfo(
            level=int(LevelAtt),
            atkbuff=float(DvdAttAtt.rstrip('%')),
            defbuff=float(DvdDefAtt),
            healthbuff=float(DvdHealthAtt.rstrip('%')),
            regenrate=float(RegenrateAtt)
        )

        dragon_attacker_changed = DragonInfo(
            level=int(LevelAtt) + int(LevelAttChange),
            atkbuff=float(DvdAttAtt.rstrip('%')) + float(DvdAttAttChange.rstrip('%')),
            defbuff=float(DvdDefAtt) + float(DvdDefAttChange),
            healthbuff=float(DvdHealthAtt.rstrip('%')) + float(DvdHealthAttChange.rstrip('%')),
            regenrate=float(RegenrateAtt) + float(RegenrateAttChange)
        )

    with dragonDefender:
        st.header("Defender's Dragon Stats")
        LevelDef = st.text_input("Dragon Level", "69", key="defenderlvl" )
        DvdAttDef = st.text_input("Dragon vs Dragon Attack", "400", key="defenderdvdatt" )
        DvdDefDef = st.text_input("Dragon Defense (LOWEST NUMBER)", "999", key="defenderdvddef" )
        DvdHealthDef = st.text_input("Dragon Health Bonus", "367", key="defenderdvdhealth" )
        RegenrateDef = st.text_input("Dragon Regen Rate", "15", key="defenderdvdregenrate" )

        st.subheader("Stat Changes (+/-)")
        LevelDefChange = st.text_input("Dragon Level Change", "0", key="defenderlvlchange")
        DvdAttDefChange = st.text_input("Dragon vs Dragon Attack Change", "0", key="defenderdvdattchange")
        DvdDefDefChange = st.text_input("Dragon Defense Change", "0", key="defenderdvddefchange")
        DvdHealthDefChange = st.text_input("Dragon Health Bonus Change", "0", key="defenderdvdhealthchange")
        RegenrateDefChange = st.text_input("Dragon Regen Rate Change", "0", key="defenderdvdregenratechange")

        dragon_defender = DragonInfo(
                level=int(LevelDef),
                atkbuff=float(DvdAttDef.rstrip('%')),
                defbuff=float(DvdDefDef),
                healthbuff=float(DvdHealthDef.rstrip('%')),
                regenrate=float(RegenrateDef)
            )

        dragon_defender_changed = DragonInfo(
                level=int(LevelDef) + int(LevelDefChange),
                atkbuff=float(DvdAttDef.rstrip('%')) + float(DvdAttDefChange.rstrip('%')),
                defbuff=float(DvdDefDef) + float(DvdDefDefChange),
                healthbuff=float(DvdHealthDef.rstrip('%')) + float(DvdHealthDefChange.rstrip('%')),
                regenrate=float(RegenrateDef) + float(RegenrateDefChange)
            )

    if st.form_submit_button("Calculate Battle"):
        resultAtt = dvdcalc_duel(dragon_attacker, dragon_defender)
        resultDef = dvdcalc_duel(dragon_defender, dragon_attacker)

        resultAttChanged = dvdcalc_duel(dragon_attacker_changed, dragon_defender_changed)
        resultDefChanged = dvdcalc_duel(dragon_defender_changed, dragon_attacker_changed)

        dvdbattle = pd.DataFrame({
            "Attacker Losses (Original)": {
                "Raw Damage Lost": resultDef["raw_damage"],
                "Percent Damage Lost": resultDef["percent_damage"],
                "Total Gold Cost": resultDef["total_gold"]
            },
            "Attacker Losses (With Changes)": {
                "Raw Damage Lost": resultDefChanged["raw_damage"],
                "Percent Damage Lost": resultDefChanged["percent_damage"],
                "Total Gold Cost": resultDefChanged["total_gold"]
            },
            "Defender Losses (Original)": {
                "Raw Damage Lost": resultAtt["raw_damage"],
                "Percent Damage Lost": resultAtt["percent_damage"],
                "Total Gold Cost": resultAtt["total_gold"]
            },
            "Defender Losses (With Changes)": {
                "Raw Damage Lost": resultAttChanged["raw_damage"],
                "Percent Damage Lost": resultAttChanged["percent_damage"],
                "Total Gold Cost": resultAttChanged["total_gold"]
            }
        })
        st.dataframe(dvdbattle, use_container_width=True)


