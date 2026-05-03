import streamlit as st
from models import DragonInfo
from calculator import dvdcalc_duel
import pandas as pd

st.set_page_config(page_title="Dragon vs Dragon Calculator", page_icon="🐉", layout="wide")
st.header("Dragon Calculator 🐉")
st.sidebar.header("Dragon vs Dragon Calculator")
st.markdown("Enter Attacker and Defender's Dragon stats below **WITHOUT** % symbol for buffs (e.g., enter 1500 for 1500%).")

st.markdown(
    "Calculator will give as result:\n"
    "- An **estimation** of the damage dealt by both sides (doesn't take into account damage done by player's troops, only Dragon vs Dragon); \n"
    "- Gold costs for healing the dragon."
)

st.markdown("On the Dragon **DEFENSE** input, enter the **LOWEST** defense value.")
st.markdown("On the **'Stat Changes (+/-)'** sections, you can input the changes in stats to see how they affect the battle outcome. Remember to enter + or - signs for the respective change.")


def _parse_num(v, label: str) -> float:
    s = str(v).strip().replace("%", "").replace(",", ".")
    if s == "":
        return 0.0
    try:
        return float(s)
    except ValueError as e:
        raise ValueError(f"Invalid number for '{label}': {v}") from e


with st.form("dragon_stats_form"):
    dragonAttacker, dragonDefender = st.columns(2)

    with dragonAttacker:
        st.header("Attacker's Dragon Stats")
        LevelAtt = st.text_input("Dragon Level", "69", key="attackerlvl")
        DvdAttAtt = st.text_input("Dragon vs Dragon Attack", "1790", key="attackerdvdatt")
        DvdDefAtt = st.text_input("Dragon Defense (LOWEST NUMBER)", "600", key="attackerdvddef")
        DvdHealthAtt = st.text_input("Dragon Health Bonus", "190", key="attackerdvdhealth")
        RegenrateAtt = st.text_input("Dragon Regen Rate", "15", key="attackerdvdregenrate")

        st.subheader("Stat Changes (+/-)")
        LevelAttChange = st.text_input("Dragon Level Change", "0", key="attackerlvlchange")
        DvdAttAttChange = st.text_input("Dragon vs Dragon Attack Change", "0", key="attackerdvdattchange")
        DvdDefAttChange = st.text_input("Dragon Defense Change", "0", key="attackerdvddefchange")
        DvdHealthAttChange = st.text_input("Dragon Health Bonus Change", "0", key="attackerdvdhealthchange")
        RegenrateAttChange = st.text_input("Dragon Regen Rate Change", "0", key="attackerdvdregenratechange")

    with dragonDefender:
        st.header("Defender's Dragon Stats")
        LevelDef = st.text_input("Dragon Level", "69", key="defenderlvl")
        DvdAttDef = st.text_input("Dragon vs Dragon Attack", "400", key="defenderdvdatt")
        DvdDefDef = st.text_input("Dragon Defense (LOWEST NUMBER)", "1163", key="defenderdvddef")
        DvdHealthDef = st.text_input("Dragon Health Bonus", "367", key="defenderdvdhealth")
        RegenrateDef = st.text_input("Dragon Regen Rate", "15", key="defenderdvdregenrate")

        st.subheader("Stat Changes (+/-)")
        LevelDefChange = st.text_input("Dragon Level Change", "0", key="defenderlvlchange")
        DvdAttDefChange = st.text_input("Dragon vs Dragon Attack Change", "0", key="defenderdvdattchange")
        DvdDefDefChange = st.text_input("Dragon Defense Change", "0", key="defenderdvddefchange")
        DvdHealthDefChange = st.text_input("Dragon Health Bonus Change", "0", key="defenderdvdhealthchange")
        RegenrateDefChange = st.text_input("Dragon Regen Rate Change", "0", key="defenderdvdregenratechange")

    submitted = st.form_submit_button("Calculate Battle")

if submitted:
    try:
        lvl_att = int(_parse_num(LevelAtt, "Attacker Dragon Level"))
        lvl_att_delta = int(_parse_num(LevelAttChange, "Attacker Dragon Level Change"))
        att_att = _parse_num(DvdAttAtt, "Attacker Dragon vs Dragon Attack")
        att_att_delta = _parse_num(DvdAttAttChange, "Attacker Dragon vs Dragon Attack Change")
        att_def = _parse_num(DvdDefAtt, "Attacker Dragon Defense")
        att_def_delta = _parse_num(DvdDefAttChange, "Attacker Dragon Defense Change")
        att_hp = _parse_num(DvdHealthAtt, "Attacker Dragon Health Bonus")
        att_hp_delta = _parse_num(DvdHealthAttChange, "Attacker Dragon Health Bonus Change")
        att_regen = _parse_num(RegenrateAtt, "Attacker Dragon Regen Rate")
        att_regen_delta = _parse_num(RegenrateAttChange, "Attacker Dragon Regen Rate Change")

        lvl_def = int(_parse_num(LevelDef, "Defender Dragon Level"))
        lvl_def_delta = int(_parse_num(LevelDefChange, "Defender Dragon Level Change"))
        def_att = _parse_num(DvdAttDef, "Defender Dragon vs Dragon Attack")
        def_att_delta = _parse_num(DvdAttDefChange, "Defender Dragon vs Dragon Attack Change")
        def_def = _parse_num(DvdDefDef, "Defender Dragon Defense")
        def_def_delta = _parse_num(DvdDefDefChange, "Defender Dragon Defense Change")
        def_hp = _parse_num(DvdHealthDef, "Defender Dragon Health Bonus")
        def_hp_delta = _parse_num(DvdHealthDefChange, "Defender Dragon Health Bonus Change")
        def_regen = _parse_num(RegenrateDef, "Defender Dragon Regen Rate")
        def_regen_delta = _parse_num(RegenrateDefChange, "Defender Dragon Regen Rate Change")

        dragon_attacker = DragonInfo(
            level=lvl_att,
            atkbuff=att_att,
            defbuff=att_def,
            healthbuff=att_hp,
            regenrate=att_regen,
        )
        dragon_attacker_changed = DragonInfo(
            level=lvl_att + lvl_att_delta,
            atkbuff=att_att + att_att_delta,
            defbuff=att_def + att_def_delta,
            healthbuff=att_hp + att_hp_delta,
            regenrate=att_regen + att_regen_delta,
        )

        dragon_defender = DragonInfo(
            level=lvl_def,
            atkbuff=def_att,
            defbuff=def_def,
            healthbuff=def_hp,
            regenrate=def_regen,
        )
        dragon_defender_changed = DragonInfo(
            level=lvl_def + lvl_def_delta,
            atkbuff=def_att + def_att_delta,
            defbuff=def_def + def_def_delta,
            healthbuff=def_hp + def_hp_delta,
            regenrate=def_regen + def_regen_delta,
        )

        resultAtt = dvdcalc_duel(dragon_attacker, dragon_defender)
        resultDef = dvdcalc_duel(dragon_defender, dragon_attacker)
        resultAttChanged = dvdcalc_duel(dragon_attacker_changed, dragon_defender_changed)
        resultDefChanged = dvdcalc_duel(dragon_defender_changed, dragon_attacker_changed)

    except Exception as e:
        st.error(f"Could not calculate dragon battle: {e}")
    else:
        dvdbattle = pd.DataFrame({
            "Attacker Losses (Original)": {
                "Raw Damage Lost": resultDef["raw_damage"],
                "Percent Damage Lost": resultDef["percent_damage"],
                "Total Gold Cost": resultDef["total_gold"],
            },
            "Attacker Losses (With Changes)": {
                "Raw Damage Lost": resultDefChanged["raw_damage"],
                "Percent Damage Lost": resultDefChanged["percent_damage"],
                "Total Gold Cost": resultDefChanged["total_gold"],
            },
            "Defender Losses (Original)": {
                "Raw Damage Lost": resultAtt["raw_damage"],
                "Percent Damage Lost": resultAtt["percent_damage"],
                "Total Gold Cost": resultAtt["total_gold"],
            },
            "Defender Losses (With Changes)": {
                "Raw Damage Lost": resultAttChanged["raw_damage"],
                "Percent Damage Lost": resultAttChanged["percent_damage"],
                "Total Gold Cost": resultAttChanged["total_gold"],
            },
        })
        st.dataframe(dvdbattle, use_container_width=True)
