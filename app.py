import streamlit as st
from models import DragonInfo
from calculator import dvdcalc_duel

header = st.header("Dragon Calculator")
st.markdown("Enter Attacker and Defender's Dragon stats below **WITHOUT** % symbol for buffs (e.g., enter 1500 for 1500%). The only value the must be a flat number is the Regen Rate stat, everything else is the usual percentage without symbol")

st.markdown("Calculator will give as result:\n" \
"- An **estimation** of the damage dealt by both sides (doesn't take into account damage done by player's troops, only Dragon vs Dragon); \n" \
"- Gold costs for healing the dragon." \
"")

st.markdown("On the Dragon DEFENSE input, enter the **LOWEST** defense value. There are two, the highest one IS NOT used in calculations and it's only purpose is to display the base (Dragon's Level) included. Multiple tests have shown it's the lowest number used.")


dragonAttacker, dragonDefender = st.columns(2)
with dragonAttacker:
    st.header("Attacker's Dragon Stats")
    LevelAtt = st.text_input("Dragon Level", "69", key="attackerlvl" )
    DvdAttAtt = st.text_input("Dragon vs Dragon Attack", "1000%", key="attackerdvdatt" )
    DvdDefAtt = st.text_input("Dragon Defense (LOWEST NUMBER)", "700", key="attackerdvddef" )
    DvdHealthAtt = st.text_input("Dragon Health Bonus", "350%", key="attackerdvdhealth" )
    RegenrateAtt = st.text_input("Dragon Regen Rate", "15", key="attackerdvdregenrate" )

    # Create DragonInfo objects
    dragon_attacker = DragonInfo(
        level=int(LevelAtt),
        atkbuff=float(DvdAttAtt.rstrip('%')),
        defbuff=float(DvdDefAtt),
        healthbuff=float(DvdHealthAtt.rstrip('%')),
        regenrate=float(RegenrateAtt)
    )

with dragonDefender:
    st.header("Defender's Dragon Stats")
    LevelDef = st.text_input("Dragon Level", "69", key="defenderlvl" )
    DvdAttDef = st.text_input("Dragon vs Dragon Attack", "1000", key="defenderdvdatt" )
    DvdDefDef = st.text_input("Dragon Defense (LOWEST NUMBER)", "700", key="defenderdvddef" )
    DvdHealthDef = st.text_input("Dragon Health Bonus", "350", key="defenderdvdhealth" )
    RegenrateDef = st.text_input("Dragon Regen Rate", "15", key="defenderdvdregenrate" )

    dragon_defender = DragonInfo(
            level=int(LevelDef),
            atkbuff=float(DvdAttDef.rstrip('%')),
            defbuff=float(DvdDefDef),
            healthbuff=float(DvdHealthDef.rstrip('%')),
            regenrate=float(RegenrateDef)
        )

if st.button("Submit Dragon Stats"):
    with dragonAttacker:
        st.subheader("Attacker's Dragon Stats")
        st.write("Dragon Level: ", LevelAtt)
        st.write("Dragon vs Dragon Attack: ", DvdAttAtt)
        st.write("Dragon vs Dragon Defense: ", DvdDefAtt)
        st.write("Dragon vs Dragon Health: ", DvdHealthAtt)
        st.write("Dragon Regen Rate: ", RegenrateAtt)    

        # Calculate duel results
        resultAtt = dvdcalc_duel(dragon_attacker, dragon_defender)

        st.subheader("Duel Results - Attacker vs Defender")
        st.write("Raw Damage: ", resultAtt["raw_damage"])
        st.write("Percent Damage: ", resultAtt["percent_damage"])
        st.write("Gold Per Hit: ", resultAtt["gold_per_hit"])
        st.write("Total Gold: ", resultAtt["total_gold"])

    with dragonDefender:
        st.subheader("Defender's Dragon Stats")
        st.write("Dragon Level: ", LevelDef)
        st.write("Dragon vs Dragon Attack: ", DvdAttDef)
        st.write("Dragon vs Dragon Defense: ", DvdDefDef)
        st.write("Dragon vs Dragon Health: ", DvdHealthDef)
        st.write("Dragon Regen Rate: ", RegenrateDef)


        resultDef = dvdcalc_duel(dragon_defender, dragon_attacker)

        st.subheader("Duel Results - Defender vs Attacker")
        st.write("Raw Damage: ", resultDef["raw_damage"])
        st.write("Percent Damage: ", resultDef["percent_damage"])
        st.write("Gold Per Hit: ", resultDef["gold_per_hit"])
        st.write("Total Gold: ", resultDef["total_gold"])

