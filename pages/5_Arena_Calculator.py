import streamlit as st

from calculator import calc_arena_damage, calc_arena_troop_attack
from models import TroopType


st.set_page_config(page_title="Arena Calculator")
st.header("Arena Damage Calculator")
st.info("The Arena Calculator is still under testing and will be updated soon.")
st.write("Estimate damage against each Arena weakness for a T12 Infantry or Cavalry march.")

def attack_buff(label: str, key: str) -> float:
    return st.number_input(label, value=0.0, step=1.0, format="%.3f", key=key)


troop_names = {
    TroopType.INFANTRY: "Infantry",
    TroopType.CAVALRY: "Cavalry",
}

with st.container(border=True):
    troop_type = st.selectbox(
        "Attacking troop", tuple(troop_names), format_func=troop_names.__getitem__
    )
    # Re-enable the troop tier selector after validating T11 against more Arena reports.
    troop_tier = 12
    march_size = st.number_input("March size", min_value=1, step=1, value=100_000)

troop_attack_label = f"{troop_names[troop_type]} Attack"
dragon_troop_attack_label = f"Dragon: {troop_attack_label}"

with st.form("arena_damage_form"):
    st.caption("Enter percentage buffs as shown in-game. For 150%, enter 150.")

    with st.container(border=True):
        st.subheader("Stats from Profile Stats Panel")
        left, right = st.columns(2)
        with left:
            profile_type_attack = attack_buff(troop_attack_label, "profile_type_attack")
            profile_creature_attack = attack_buff("Attack vs Creatures", "profile_creature_attack")
        with right:
            arena_attack = attack_buff("Troop Attack in the Arena", "arena_attack")
            arena_type_attack = attack_buff(f"{troop_attack_label} in the Arena", "arena_type_attack")

    with st.container(border=True):
        st.subheader("Dragon Stats from Dragon Pit Stats Panel")
        left, right = st.columns(2)
        with left:
            dragon_type_attack = attack_buff(dragon_troop_attack_label, "dragon_type_attack")
        with right:
            dragon_attack = st.number_input(
                "Dragon Attack",
                min_value=0.0,
                value=0.0,
                help="Enter the flat Total Dragon Attack from the Arena worksheet. A percentage requires the dragon's base Attack to convert it. Enter 0 for a troop-only march.",
            )

    with st.container(border=True):
        st.subheader("Marcher Hero Stats Panel")
        left, right = st.columns(2)
        with left:
            hero_troop_attack = attack_buff("Troop Attack", "hero_troop_attack")
            hero_type_attack = attack_buff(troop_attack_label, "hero_type_attack")
            hero_creature_attack = attack_buff("Attack vs Creatures", "hero_creature_attack")
        with right:
            hero_dragon_type_attack = attack_buff(dragon_troop_attack_label, "hero_dragon_type_attack")
            hero_dragon_troop_attack = attack_buff("Dragon: Troop Attack", "hero_dragon_troop_attack")

    submitted = st.form_submit_button("Calculate Arena Damage")

if submitted:
    try:
        troop_attack = calc_arena_troop_attack(
            troop_type,
            profile_type_attack + profile_creature_attack + hero_troop_attack
            + hero_type_attack + hero_creature_attack,
            dragon_type_attack + hero_dragon_type_attack + hero_dragon_troop_attack,
            arena_attack,
            arena_type_attack,
            troop_tier=troop_tier,
        )
        damage = calc_arena_damage(
            troop_type, march_size, troop_attack, dragon_attack, troop_tier=troop_tier
        )
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.metric("Total Troop Attack used", f"{troop_attack:,.5f}".rstrip("0").rstrip("."))
        st.table([
            {"Arena weakness": label, "Estimated damage": f"{damage[weakness]:,}"}
            for weakness, label in (
                (TroopType.INFANTRY, "Weak Infantry"),
                (TroopType.RANGED, "Weak Ranged"),
                (TroopType.CAVALRY, "Weak Cavalry"),
            )
        ])
