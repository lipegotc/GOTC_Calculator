# streamlit_battle.py
import streamlit as st
import pandas as pd

from models import TroopType, attackBattleStats, defenseBattleStats
from calculator import compute_battle_outcome

st.set_page_config(page_title="Battle Simulator", page_icon="⚔️")
st.title("Battle Simulator ⚔️")

st.markdown(""" 
This simulator allows you to simulate battles between attackers and defenders in two scenarios:
            
- **Solo Attack vs Solo Reinforcement**: Simulate a battle between a single attacking march and a single defending march.
- **Rally vs Multi-Reinforcements**: Simulate a rally attack against multiple reinforcements, with both options for a detailed and simplified report of losses.

- Only troop tiers 11 and 12 options available.
            
Keep in mind the results are **estimations** and not the exact values you would get in game due to extra hidden mechanics.
""")
st.caption("Decimal standard: use a dot (.) for decimal values (example: 1317.48).")


TT_MAP = {
    "Infantry": TroopType.INFANTRY,
    "Ranged": TroopType.RANGED,
    "Cavalry": TroopType.CAVALRY,
}


def _num_or_zero(v):
    return 0.0 if v is None else float(v)

def _build_att(
    tt_str,
    tier,
    msize,
    baseAtk,
    marcherAtk,
    vsCav,
    vsInf,
    vsRng,
    baseDef=0.0,
    marcherDef=0.0,
    defVsCav=0.0,
    defVsInf=0.0,
    defVsRng=0.0,
    baseHp=0.0,
    marcherHp=0.0,
):
    return attackBattleStats(
        TroopType=TT_MAP[tt_str],
        TroopTier=int(tier),
        msizeAtt=int(msize),
        baseAttackBuff=_num_or_zero(baseAtk),
        marcherAttackBuff=_num_or_zero(marcherAtk),
        baseDefenseBuff=_num_or_zero(baseDef),
        marcherDefenseBuff=_num_or_zero(marcherDef),
        baseHealthBuff=_num_or_zero(baseHp),
        marcherHealthBuff=_num_or_zero(marcherHp),
        attvscav=_num_or_zero(vsCav),
        attvsinf=_num_or_zero(vsInf),
        attvsrng=_num_or_zero(vsRng),
        defvscav=_num_or_zero(defVsCav),
        defvsinf=_num_or_zero(defVsInf),
        defvsrng=_num_or_zero(defVsRng),
    )

def _build_def(
    tt_str,
    tier,
    msize,
    baseDef,
    baseHp,
    defAtSop,
    hpAtSop,
    vsCav,
    vsInf,
    vsRng,
    defDefBuff,
    defHpBuff,
    baseAtk=0.0,
    atkAtSop=0.0,
    defAtkBuff=0.0,
    atkVsCav=0.0,
    atkVsInf=0.0,
    atkVsRng=0.0,
):
    return defenseBattleStats(
        TroopType=TT_MAP[tt_str],
        TroopTier=int(tier),
        msizeDef=int(msize),
        baseAttackBuff=_num_or_zero(baseAtk),
        attackatsopBuff=_num_or_zero(atkAtSop),
        defenderattackbuff=_num_or_zero(defAtkBuff),
        baseDefenseBuff=_num_or_zero(baseDef),
        baseHealthBuff=_num_or_zero(baseHp),
        defenseatsopBuff=_num_or_zero(defAtSop),
        healthatsopBuff=_num_or_zero(hpAtSop),
        attvscav=_num_or_zero(atkVsCav),
        attvsinf=_num_or_zero(atkVsInf),
        attvsrng=_num_or_zero(atkVsRng),
        defvscav=_num_or_zero(vsCav),
        defvsinf=_num_or_zero(vsInf),
        defvsrng=_num_or_zero(vsRng),
        defenderdefensebuff=_num_or_zero(defDefBuff),
        defenderhealthbuff=_num_or_zero(defHpBuff),
    )

def dfs_from_battle_result(res: dict):
    # Attackers table
    df_attackers = pd.DataFrame(res.get("attackers", []))
    if not df_attackers.empty:
        cols = ["TroopType", "Tier", "MarchSize", "Att_vs_Inf", "Att_vs_Cav", "Att_vs_Ranged"]
        df_attackers = df_attackers[[c for c in cols if c in df_attackers.columns]]

    # Defenders table
    df_defenders = pd.DataFrame(res.get("defenders", []))
    if not df_defenders.empty:
        cols = ["TroopType", "Tier", "MarchSize", "TotalHealth",
                "TotalDef_vs_Inf", "TotalDef_vs_Cav", "TotalDef_vs_Ranged"]
        df_defenders = df_defenders[[c for c in cols if c in df_defenders.columns]]

    # Kills matrix
    killed_matrix = res.get("killed_matrix", {})
    df_matrix = pd.DataFrame.from_dict(killed_matrix, orient="index").fillna(0).astype(int)

    wanted_cols = ["Infantry", "Cavalry", "Ranged"]
    df_matrix = df_matrix[[c for c in wanted_cols if c in df_matrix.columns]]

    df_matrix["Row Total"] = df_matrix.sum(axis=1)
    col_total = df_matrix.sum(axis=0).to_frame().T
    col_total.index = ["Col Total"]
    df_matrix = pd.concat([df_matrix, col_total], axis=0)

    # Totals breakdown
    by_att = res.get("killed_by_attacker_type", {})
    by_def = res.get("kills_by_defender_type", {})
    total_def_losses = res.get("defender_losses_total", res.get("killed_total", 0))
    total_att_losses = res.get("attacker_losses_total", 0)
    scenario = res.get("scenario", "")

    rows = []
    if scenario == "solo_attack_vs_solo_reinforcement":
        att_list = res.get("attackers", [])
        def_list = res.get("defenders", [])
        att_type = att_list[0]["TroopType"] if att_list else None
        def_type = def_list[0]["TroopType"] if def_list else None

        if att_type:
            rows.append({
                "Group": "Defender Losses",
                "Killed": int(by_att.get(att_type, 0)),
            })
        if def_type:
            rows.append({
                "Group": "Attacker Losses",
                "Killed": int(by_def.get(def_type, 0)),
            })
    else:
        for k, v in by_att.items():
            rows.append({"Group": f"Defender Losses ({k})", "Killed": int(v)})
        for k, v in by_def.items():
            rows.append({"Group": f"Attacker Losses ({k})", "Killed": int(v)})

        rows.append({"Group": "Defender Losses Total", "Killed": int(total_def_losses)})
        rows.append({"Group": "Attacker Losses Total", "Killed": int(total_att_losses)})
    df_totals = pd.DataFrame(rows)

    return df_attackers, df_defenders, df_matrix, df_totals


def kills_exchange_df(res: dict) -> pd.DataFrame:
    rows = list(res.get("killed_exchange_rows", []))
    if not rows:
        return pd.DataFrame(columns=["KillerSide", "KillerTroopType", "AgainstTroopType", "TroopsKilled"])
    df = pd.DataFrame(rows)
    total_rows = []
    if "defender_losses_total" in res:
        total_rows.append({
            "KillerSide": "Attacker",
            "KillerTroopType": "TOTAL",
            "AgainstTroopType": "All Defenders",
            "TroopsKilled": int(res.get("defender_losses_total", 0)),
        })
    if "attacker_losses_total" in res:
        total_rows.append({
            "KillerSide": "Defender",
            "KillerTroopType": "TOTAL",
            "AgainstTroopType": "All Attackers",
            "TroopsKilled": int(res.get("attacker_losses_total", 0)),
        })
    if total_rows:
        df = pd.concat([df, pd.DataFrame(total_rows)], ignore_index=True)
    return df


def simplified_rally_losses_df(res: dict) -> pd.DataFrame:
    attacker_losses_slot = list(res.get("attacker_losses_by_slot", []))
    defender_losses_slot = list(res.get("defender_losses_by_slot", []))
    attacker_losses = res.get("attacker_losses_by_type", {})
    defender_losses = res.get("defender_losses_by_type", {})
    attackers = res.get("attackers", [])
    defenders = res.get("defenders", [])

    rows = []
    for i, a in enumerate(attackers, start=1):
        if i - 1 < len(attacker_losses_slot):
            killed = int(attacker_losses_slot[i - 1])
        else:
            tt = a.get("TroopType", "")
            killed = int(attacker_losses.get(tt, 0))
        rows.append({"Group": f"Attacker{i}", "Killed": killed})
    for i, d in enumerate(defenders, start=1):
        if i - 1 < len(defender_losses_slot):
            killed = int(defender_losses_slot[i - 1])
        else:
            tt = d.get("TroopType", "")
            killed = int(defender_losses.get(tt, 0))
        rows.append({"Group": f"Defender{i}", "Killed": killed})

    return pd.DataFrame(rows, columns=["Group", "Killed"])


def _render_result(res: dict):
    if res.get("scenario") == "rally_vs_multi_reinforcement":
        report_mode = res.get("report_mode", "Detailed Report")
        if report_mode == "Simplified Report":
            st.subheader("Simplified Report")
            st.dataframe(simplified_rally_losses_df(res), use_container_width=True)
        else:
            st.subheader("Detailed Report")
            st.dataframe(kills_exchange_df(res), use_container_width=True)
        return

    if res.get("scenario") == "solo_attack_vs_solo_reinforcement":
        _, _, _, df_totals = dfs_from_battle_result(res)
        st.subheader("Totals")
        st.dataframe(df_totals, use_container_width=True)
        return

    df_attackers, df_defenders, df_matrix, df_totals = dfs_from_battle_result(res)
    st.subheader("Attackers (effective attack vs troop types)")
    st.dataframe(df_attackers, use_container_width=True)
    st.subheader("Defenders (total health + total defense vs troop types)")
    st.dataframe(df_defenders, use_container_width=True)
    st.subheader("Kills Matrix (attacker rows x defender columns)")
    st.dataframe(df_matrix, use_container_width=True)
    st.subheader("Totals")
    st.dataframe(df_totals, use_container_width=True)


battle_formats = [
    "Solo Attack vs Solo Reinforcement",
    "Rally vs Multi-Reinforcements"
]
choice = st.selectbox("Select Battle Format", options=battle_formats, key="battle_format_choice")


def battle_solo_vs_solo():
    st.write("Solo Attack vs Solo Reinforcement")
    with st.form(key="battle_solo_solo_simulator_form"):
        attacker, defender = st.columns(2)

        with attacker:
            st.write("### Attacker Stats")
            troopTypeAtt = st.selectbox("Troop Type", options=["Infantry", "Ranged", "Cavalry"], key="troopTypeAttSoloSolo")
            tierAtt = st.selectbox("Troop Tier", options=[11, 12], key="tierAttSoloSolo")
            msizeAtt = st.number_input("March Size", min_value=1, value=400000, key="msizeAttSoloSolo")
            baseAttTroopTypeBuffAtt = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.0, key="baseTroopTypeBuffAttSoloSolo")
            baseDefTroopTypeBuffAtt = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.0, key="baseDefTroopTypeBuffAttSoloSolo")
            baseHealthTroopBuffAtt = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.0, key="baseHealthTroopBuffAttSoloSolo")
            atkVsInfAtt = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.0, key="atkVsInfAttSoloSolo")
            atkVsRngAtt = st.number_input("Attack vs Ranged", min_value=0.0, value=346.0, key="atkVsRngAttSoloSolo")
            atkVsCavAtt = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.0, key="atkVsCavAttSoloSolo")
            defVsInfAtt = st.number_input("Defense vs Infantry", min_value=0.0, value=589.0, key="defVsInfAttSoloSolo")
            defVsRngAtt = st.number_input("Defense vs Ranged", min_value=0.0, value=608.0, key="defVsRngAttSoloSolo")
            defVsCavAtt = st.number_input("Defense vs Cavalry", min_value=0.0, value=919.0, key="defVsCavAttSoloSolo")
            marcherTroopBuffAtt = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=6873.0, key="marcherTroopBuffAttSoloSolo")
            marcherDefTroopBuffAtt = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttSoloSolo")
            marcherHealthTroopBuffAtt = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttSoloSolo")

        with defender:
            st.write("### Defender Stats")
            troopTypeDef = st.selectbox("Troop Type", options=["Infantry", "Ranged", "Cavalry"], key="troopTypeDefSoloSolo")
            tierDef = st.selectbox("Troop Tier", options=[11, 12], key="tierDefSoloSolo")
            msizeDef = st.number_input("March Size", min_value=1, value=400000, key="msizeDefSoloSolo")
            baseAtkTroopTypeBuffDef = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.0, key="baseAtkTroopTypeBuffDefSoloSolo")
            baseDefTroopTypeBuffDef = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.0, key="baseDefTroopTypeBuffDefSoloSolo")
            baseHealthTroopBuffDef = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.0, key="baseHealthTroopBuffDefSoloSolo")
            atkVsInfDef = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.0, key="atkVsInfDefSoloSolo")
            atkVsRngDef = st.number_input("Attack vs Ranged", min_value=0.0, value=346.0, key="atkVsRngDefSoloSolo")
            atkVsCavDef = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.0, key="atkVsCavDefSoloSolo")
            defVsInfDef = st.number_input("Defense vs Infantry", min_value=0.0, value=589.0, key="defVsInfDefSoloSolo")
            defVsRngDef = st.number_input("Defense vs Ranged", min_value=0.0, value=608.0, key="defVsRngDefSoloSolo")
            defVsCavDef = st.number_input("Defense vs Cavalry", min_value=0.0, value=919.0, key="defVsCavDefSoloSolo")
            attackatsopBuffDef = st.number_input("Attack at SOP", min_value=0.0, value=2400.0, key="attackatsopBuffDefSoloSolo")
            defenseatsopBuffDef = st.number_input("Defense at SOP", min_value=0.0, value=2600.0, key="defenseatsopBuffDefSoloSolo")
            healthatsopBuffDef = st.number_input("Health at SOP", min_value=0.0, value=2108.0, key="healthatsopBuffDefSoloSolo")
            defenderattackBuffDef = st.number_input("Defender Attack Buff", min_value=0.0, value=67.0, key="defenderattackBuffDefSoloSolo")
            defenderdefenseBuffDef = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefSoloSolo")
            defenderhealthBuffDef = st.number_input("Defender Health Buff", min_value=0.0, value=96.0, key="defenderhealthBuffDefSoloSolo")

        submitted = st.form_submit_button("Simulate Battle")

    if submitted:
        attackers = [
            _build_att(troopTypeAtt, tierAtt, msizeAtt, baseAttTroopTypeBuffAtt, marcherTroopBuffAtt,
                       atkVsCavAtt, atkVsInfAtt, atkVsRngAtt,
                       baseDefTroopTypeBuffAtt, marcherDefTroopBuffAtt,
                       defVsCavAtt, defVsInfAtt, defVsRngAtt,
                       baseHealthTroopBuffAtt, marcherHealthTroopBuffAtt)
        ]
        defenders = [
            _build_def(troopTypeDef, tierDef, msizeDef,
                       baseDefTroopTypeBuffDef, baseHealthTroopBuffDef,
                       defenseatsopBuffDef, healthatsopBuffDef,
                       defVsCavDef, defVsInfDef, defVsRngDef,
                       defenderdefenseBuffDef, defenderhealthBuffDef,
                       baseAtkTroopTypeBuffDef, attackatsopBuffDef, defenderattackBuffDef,
                       atkVsCavDef, atkVsInfDef, atkVsRngDef)
        ]

        res = compute_battle_outcome(
            attackers=attackers,
            defenders=defenders,
            scenario="solo_attack_vs_solo_reinforcement",
        )
        _render_result(res)


def battle_rally_vs_multi():
    st.write("Rally vs Multi-Reinforcements")
    report_mode = st.selectbox(
        "Report Type",
        options=["Detailed Report", "Simplified Report"],
        key="rally_multi_report_type",
    )
    with st.form(key="battle_rally_multi_simulator_form"):
        st.write("### Attackers Stats")
        atkCav, atkInf, atkRng, atkCav2, atkInf2, atkRng2 = st.columns(6)
        st.write("### Defenders Stats")
        infdef, rngdef, cavdef = st.columns(3)

        with atkCav:
            st.write("### Cavalry Attacker Stats")
            troopTypeAttCav = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeAttCav_multi")
            tierAttCav = st.selectbox("Troop Tier", options=[11, 12], key="tierAttCav_multi")
            msizeAttCav = st.number_input("March Size", min_value=1, value=400000, key="msizeAttCav_multi")

            baseAttTroopTypeBuffAttCav = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1317.48, key="baseAttTroopTypeBuffAttCav_multi")
            baseDefTroopTypeBuffAttCav = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1197.68, key="baseDefTroopTypeBuffAttCav_multi")
            baseHealthTroopBuffAttCav = st.number_input("Base Troop Health Buff", min_value=0.0, value=337.45, key="baseHealthTroopBuffAttCav_multi")
            atkVsInfAttCav = st.number_input("Attack vs Infantry", min_value=0.0, value=471.49, key="atkVsInfAttCav_multi")
            atkVsRngAttCav = st.number_input("Attack vs Ranged", min_value=0.0, value=1642.80, key="atkVsRngAttCav_multi")
            atkVsCavAttCav = st.number_input("Attack vs Cavalry", min_value=0.0, value=1620.69, key="atkVsCavAttCav_multi")
            defVsInfAttCav = st.number_input("Defense vs Infantry", min_value=0.0, value=1094.47, key="defVsInfAttCav_multi")
            defVsRngAttCav = st.number_input("Defense vs Ranged", min_value=0.0, value=917.15, key="defVsRngAttCav_multi")
            defVsCavAttCav = st.number_input("Defense vs Cavalry", min_value=0.0, value=521.90, key="defVsCavAttCav_multi")
            marcherTroopBuffAttCav = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=7271.58, key="marcherTroopBuffAttCav_multi")
            marcherDefTroopBuffAttCav = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttCav_multi")
            marcherHealthTroopBuffAttCav = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttCav_multi")

        with atkInf:
            st.write("### Infantry Attacker Stats")
            troopTypeAttInf = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeAttInf_multi")
            tierAttInf = st.selectbox("Troop Tier", options=[11, 12], key="tierAttInf_multi")
            msizeAttInf = st.number_input("March Size", min_value=1, value=400000, key="msizeAttInf_multi")

            baseAttTroopTypeBuffAttInf = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.35, key="baseAttTroopTypeBuffAttInf_multi")
            baseDefTroopTypeBuffAttInf = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.42, key="baseDefTroopTypeBuffAttInf_multi")
            baseHealthTroopBuffAttInf = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.07, key="baseHealthTroopBuffAttInf_multi")
            atkVsInfAttInf = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.48, key="atkVsInfAttInf_multi")
            atkVsRngAttInf = st.number_input("Attack vs Ranged", min_value=0.0, value=346.15, key="atkVsRngAttInf_multi")
            atkVsCavAttInf = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.51, key="atkVsCavAttInf_multi")
            defVsInfAttInf = st.number_input("Defense vs Infantry", min_value=0.0, value=589.85, key="defVsInfAttInf_multi")
            defVsRngAttInf = st.number_input("Defense vs Ranged", min_value=0.0, value=608.53, key="defVsRngAttInf_multi")
            defVsCavAttInf = st.number_input("Defense vs Cavalry", min_value=0.0, value=917.99, key="defVsCavAttInf_multi")
            marcherTroopBuffAttInf = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=6873.38, key="marcherTroopBuffAttInf_multi")
            marcherDefTroopBuffAttInf = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttInf_multi")
            marcherHealthTroopBuffAttInf = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttInf_multi")

        with atkRng:
            st.write("### Ranged Attacker Stats")
            troopTypeAttRng = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeAttRng_multi")
            tierAttRng = st.selectbox("Troop Tier", options=[11, 12], key="tierAttRng_multi")
            msizeAttRng = st.number_input("March Size", min_value=1, value=400000, key="msizeAttRng_multi")

            baseAttTroopTypeBuffAttRng = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1308.81, key="baseAttTroopTypeBuffAttRng_multi")
            baseDefTroopTypeBuffAttRng = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1225.62, key="baseDefTroopTypeBuffAttRng_multi")
            baseHealthTroopBuffAttRng = st.number_input("Base Troop Health Buff", min_value=0.0, value=438.98, key="baseHealthTroopBuffAttRng_multi")
            atkVsInfAttRng = st.number_input("Attack vs Infantry", min_value=0.0, value=1717.59, key="atkVsInfAttRng_multi")
            atkVsRngAttRng = st.number_input("Attack vs Ranged", min_value=0.0, value=1483.59, key="atkVsRngAttRng_multi")
            atkVsCavAttRng = st.number_input("Attack vs Cavalry", min_value=0.0, value=436.92, key="atkVsCavAttRng_multi")
            defVsInfAttRng = st.number_input("Defense vs Infantry", min_value=0.0, value=989.71, key="defVsInfAttRng_multi")
            defVsRngAttRng = st.number_input("Defense vs Ranged", min_value=0.0, value=477.20, key="defVsRngAttRng_multi")
            defVsCavAttRng = st.number_input("Defense vs Cavalry", min_value=0.0, value=838.02, key="defVsCavAttRng_multi")
            marcherTroopBuffAttRng = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=7415.18, key="marcherTroopBuffAttRng_multi")
            marcherDefTroopBuffAttRng = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttRng_multi")
            marcherHealthTroopBuffAttRng = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttRng_multi")

        with atkCav2:
            st.write("### Cavalry Attacker Stats (2)")
            troopTypeAttCav2 = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeAttCav2_multi")
            tierAttCav2 = st.selectbox("Troop Tier", options=[11, 12], key="tierAttCav2_multi")
            msizeAttCav2 = st.number_input("March Size", min_value=1, value=400000, key="msizeAttCav2_multi")

            baseAttTroopTypeBuffAttCav2 = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1317.48, key="baseAttTroopTypeBuffAttCav2_multi")
            baseDefTroopTypeBuffAttCav2 = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1197.68, key="baseDefTroopTypeBuffAttCav2_multi")
            baseHealthTroopBuffAttCav2 = st.number_input("Base Troop Health Buff", min_value=0.0, value=337.45, key="baseHealthTroopBuffAttCav2_multi")
            atkVsInfAttCav2 = st.number_input("Attack vs Infantry", min_value=0.0, value=471.49, key="atkVsInfAttCav2_multi")
            atkVsRngAttCav2 = st.number_input("Attack vs Ranged", min_value=0.0, value=1642.80, key="atkVsRngAttCav2_multi")
            atkVsCavAttCav2 = st.number_input("Attack vs Cavalry", min_value=0.0, value=1620.69, key="atkVsCavAttCav2_multi")
            defVsInfAttCav2 = st.number_input("Defense vs Infantry", min_value=0.0, value=1094.47, key="defVsInfAttCav2_multi")
            defVsRngAttCav2 = st.number_input("Defense vs Ranged", min_value=0.0, value=917.15, key="defVsRngAttCav2_multi")
            defVsCavAttCav2 = st.number_input("Defense vs Cavalry", min_value=0.0, value=521.90, key="defVsCavAttCav2_multi")
            marcherTroopBuffAttCav2 = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=7271.58, key="marcherTroopBuffAttCav2_multi")
            marcherDefTroopBuffAttCav2 = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttCav2_multi")
            marcherHealthTroopBuffAttCav2 = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttCav2_multi")

        with atkInf2:
            st.write("### Infantry Attacker Stats (2)")
            troopTypeAttInf2 = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeAttInf2_multi")
            tierAttInf2 = st.selectbox("Troop Tier", options=[11, 12], key="tierAttInf2_multi")
            msizeAttInf2 = st.number_input("March Size", min_value=1, value=400000, key="msizeAttInf2_multi")

            baseAttTroopTypeBuffAttInf2 = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.35, key="baseAttTroopTypeBuffAttInf2_multi")
            baseDefTroopTypeBuffAttInf2 = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.42, key="baseDefTroopTypeBuffAttInf2_multi")
            baseHealthTroopBuffAttInf2 = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.07, key="baseHealthTroopBuffAttInf2_multi")
            atkVsInfAttInf2 = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.48, key="atkVsInfAttInf2_multi")
            atkVsRngAttInf2 = st.number_input("Attack vs Ranged", min_value=0.0, value=346.15, key="atkVsRngAttInf2_multi")
            atkVsCavAttInf2 = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.51, key="atkVsCavAttInf2_multi")
            defVsInfAttInf2 = st.number_input("Defense vs Infantry", min_value=0.0, value=589.85, key="defVsInfAttInf2_multi")
            defVsRngAttInf2 = st.number_input("Defense vs Ranged", min_value=0.0, value=608.53, key="defVsRngAttInf2_multi")
            defVsCavAttInf2 = st.number_input("Defense vs Cavalry", min_value=0.0, value=917.99, key="defVsCavAttInf2_multi")
            marcherTroopBuffAttInf2 = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=6873.38, key="marcherTroopBuffAttInf2_multi")
            marcherDefTroopBuffAttInf2 = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttInf2_multi")
            marcherHealthTroopBuffAttInf2 = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttInf2_multi")

        with atkRng2:
            st.write("### Ranged Attacker Stats (2)")
            troopTypeAttRng2 = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeAttRng2_multi")
            tierAttRng2 = st.selectbox("Troop Tier", options=[11, 12], key="tierAttRng2_multi")
            msizeAttRng2 = st.number_input("March Size", min_value=1, value=400000, key="msizeAttRng2_multi")

            baseAttTroopTypeBuffAttRng2 = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1308.81, key="baseAttTroopTypeBuffAttRng2_multi")
            baseDefTroopTypeBuffAttRng2 = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1225.62, key="baseDefTroopTypeBuffAttRng2_multi")
            baseHealthTroopBuffAttRng2 = st.number_input("Base Troop Health Buff", min_value=0.0, value=438.98, key="baseHealthTroopBuffAttRng2_multi")
            atkVsInfAttRng2 = st.number_input("Attack vs Infantry", min_value=0.0, value=1717.59, key="atkVsInfAttRng2_multi")
            atkVsRngAttRng2 = st.number_input("Attack vs Ranged", min_value=0.0, value=1483.59, key="atkVsRngAttRng2_multi")
            atkVsCavAttRng2 = st.number_input("Attack vs Cavalry", min_value=0.0, value=436.92, key="atkVsCavAttRng2_multi")
            defVsInfAttRng2 = st.number_input("Defense vs Infantry", min_value=0.0, value=989.71, key="defVsInfAttRng2_multi")
            defVsRngAttRng2 = st.number_input("Defense vs Ranged", min_value=0.0, value=477.20, key="defVsRngAttRng2_multi")
            defVsCavAttRng2 = st.number_input("Defense vs Cavalry", min_value=0.0, value=838.02, key="defVsCavAttRng2_multi")
            marcherTroopBuffAttRng2 = st.number_input("Marcher Troop Type Attack", min_value=0.0, value=7415.18, key="marcherTroopBuffAttRng2_multi")
            marcherDefTroopBuffAttRng2 = st.number_input("Marcher Troop Type Defense", min_value=0.0, value=2500.0, key="marcherDefTroopBuffAttRng2_multi")
            marcherHealthTroopBuffAttRng2 = st.number_input("Marcher Troop Type Health", min_value=0.0, value=2400.0, key="marcherHealthTroopBuffAttRng2_multi")

        with infdef:
            st.write("### Infantry Defender Stats")
            troopTypeDefInf = st.selectbox("Troop Type", options=["Infantry"], key="troopTypeDefInf_multi")
            tierDefInf = st.selectbox("Troop Tier", options=[11, 12], key="tierDefInf_multi")
            msizeDefInf = st.number_input("March Size", min_value=1, value=400000, key="sizeDefInf_multi")

            baseAtkTroopTypeBuffDefInf = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1390.35, key="baseAtkTroopTypeBuffDefInf_multi")
            baseDefTroopTypeBuffDefInf = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1018.42, key="baseDefTroopTypeBuffDefInf_multi")
            baseHealthTroopBuffDefInf = st.number_input("Base Troop Health Buff", min_value=0.0, value=365.07, key="baseHealthTroopBuffDefInf_multi")
            atkVsInfDefInf = st.number_input("Attack vs Infantry", min_value=0.0, value=1097.48, key="atkVsInfDefInf_multi")
            atkVsRngDefInf = st.number_input("Attack vs Ranged", min_value=0.0, value=346.15, key="atkVsRngDefInf_multi")
            atkVsCavDefInf = st.number_input("Attack vs Cavalry", min_value=0.0, value=1610.51, key="atkVsCavDefInf_multi")
            defVsInfDefInf = st.number_input("Defense vs Infantry", min_value=0.0, value=589.85, key="defVsInfDefInf_multi")
            defVsRngDefInf = st.number_input("Defense vs Ranged", min_value=0.0, value=608.53, key="defVsRngDefInf_multi")
            defVsCavDefInf = st.number_input("Defense vs Cavalry", min_value=0.0, value=917.99, key="defVsCavDefInf_multi")
            attackatsopBuffDefInf = st.number_input("Attack at SOP", min_value=0.0, value=2400.0, key="attackatsopBuffDefInf_multi")
            defenseatsopBuffDefInf = st.number_input("Defense at SOP", min_value=0.0, value=2600.58, key="defenseatsopBuffDefInf_multi")
            healthatsopBuffDefInf = st.number_input("Health at SOP", min_value=0.0, value=2108.68, key="healthatsopBuffDefInf_multi")
            defenderattackBuffDefInf = st.number_input("Defender Attack Buff", min_value=0.0, value=67.0, key="defenderattackBuffDefInf_multi")
            defenderdefenseBuffDefInf = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefInf_multi")
            defenderhealthBuffDefInf = st.number_input("Defender Health Buff", min_value=0.0, value=96.41, key="defenderhealthBuffDefInf_multi")

        with rngdef:
            st.write("### Ranged Defender Stats")
            troopTypeDefRng = st.selectbox("Troop Type", options=["Ranged"], key="troopTypeDefRng_multi")
            tierDefRng = st.selectbox("Troop Tier", options=[11, 12], key="tierDefRng_multi")
            msizeDefRng = st.number_input("March Size", min_value=1, value=400000, key="sizeDefRng_multi")

            baseAtkTroopTypeBuffDefRng = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1308.81, key="baseAtkTroopTypeBuffDefRng_multi")
            baseDefTroopTypeBuffDefRng = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1225.62, key="baseDefTroopTypeBuffDefRng_multi")
            baseHealthTroopBuffDefRng = st.number_input("Base Troop Health Buff", min_value=0.0, value=438.98, key="baseHealthTroopBuffDefRng_multi")
            atkVsInfDefRng = st.number_input("Attack vs Infantry", min_value=0.0, value=1717.59, key="atkVsInfDefRng_multi")
            atkVsRngDefRng = st.number_input("Attack vs Ranged", min_value=0.0, value=1483.59, key="atkVsRngDefRng_multi")
            atkVsCavDefRng = st.number_input("Attack vs Cavalry", min_value=0.0, value=436.92, key="atkVsCavDefRng_multi")
            defVsInfDefRng = st.number_input("Defense vs Infantry", min_value=0.0, value=989.71, key="defVsInfDefRng_multi")
            defVsRngDefRng = st.number_input("Defense vs Ranged", min_value=0.0, value=477.20, key="defVsRngDefRng_multi")
            defVsCavDefRng = st.number_input("Defense vs Cavalry", min_value=0.0, value=838.02, key="defVsCavDefRng_multi")
            attackatsopBuffDefRng = st.number_input("Attack at SOP", min_value=0.0, value=2400.0, key="attackatsopBuffDefRng_multi")
            defenseatsopBuffDefRng = st.number_input("Defense at SOP", min_value=0.0, value=2720.27, key="defenseatsopBuffDefRng_multi")
            healthatsopBuffDefRng = st.number_input("Health at SOP", min_value=0.0, value=2302.55, key="healthatsopBuffDefRng_multi")
            defenderattackBuffDefRng = st.number_input("Defender Attack Buff", min_value=0.0, value=67.0, key="defenderattackBuffDefRng_multi")
            defenderdefenseBuffDefRng = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefRng_multi")
            defenderhealthBuffDefRng = st.number_input("Defender Health Buff", min_value=0.0, value=87.23, key="defenderhealthBuffDefRng_multi")

        with cavdef:
            st.write("### Cavalry Defender Stats")
            troopTypeDefCav = st.selectbox("Troop Type", options=["Cavalry"], key="troopTypeDefCav_multi")
            tierDefCav = st.selectbox("Troop Tier", options=[11, 12], key="tierDefCav_multi")
            msizeDefCav = st.number_input("March Size", min_value=1, value=400000, key="sizeDefCav_multi")

            baseAtkTroopTypeBuffDefCav = st.number_input("Base Troop Type Attack Buff", min_value=0.0, value=1317.48, key="baseAtkTroopTypeBuffDefCav_multi")
            baseDefTroopTypeBuffDefCav = st.number_input("Base Troop Type Defense Buff", min_value=0.0, value=1197.68, key="baseDefTroopTypeBuffDefCav_multi")
            baseHealthTroopBuffDefCav = st.number_input("Base Troop Health Buff", min_value=0.0, value=337.45, key="baseHealthTroopBuffDefCav_multi")
            atkVsInfDefCav = st.number_input("Attack vs Infantry", min_value=0.0, value=471.49, key="atkVsInfDefCav_multi")
            atkVsRngDefCav = st.number_input("Attack vs Ranged", min_value=0.0, value=1642.80, key="atkVsRngDefCav_multi")
            atkVsCavDefCav = st.number_input("Attack vs Cavalry", min_value=0.0, value=1620.69, key="atkVsCavDefCav_multi")
            defVsInfDefCav = st.number_input("Defense vs Infantry", min_value=0.0, value=1094.47, key="defVsInfDefCav_multi")
            defVsRngDefCav = st.number_input("Defense vs Ranged", min_value=0.0, value=917.15, key="defVsRngDefCav_multi")
            defVsCavDefCav = st.number_input("Defense vs Cavalry", min_value=0.0, value=521.90, key="defVsCavDefCav_multi")
            attackatsopBuffDefCav = st.number_input("Attack at SOP", min_value=0.0, value=2400.0, key="attackatsopBuffDefCav_multi")
            defenseatsopBuffDefCav = st.number_input("Defense at SOP", min_value=0.0, value=2310.14, key="defenseatsopBuffDefCav_multi")
            healthatsopBuffDefCav = st.number_input("Health at SOP", min_value=0.0, value=2873.64, key="healthatsopBuffDefCav_multi")
            defenderattackBuffDefCav = st.number_input("Defender Attack Buff", min_value=0.0, value=67.0, key="defenderattackBuffDefCav_multi")
            defenderdefenseBuffDefCav = st.number_input("Defender Defense Buff", min_value=0.0, value=86.0, key="defenderdefenseBuffDefCav_multi")
            defenderhealthBuffDefCav = st.number_input("Defender Health Buff", min_value=0.0, value=45.0, key="defenderhealthBuffDefCav_multi")

        submitted = st.form_submit_button("Simulate Battle")

    if submitted:
        attackers = [
            _build_att("Cavalry", tierAttCav, msizeAttCav, baseAttTroopTypeBuffAttCav, marcherTroopBuffAttCav,
                       atkVsCavAttCav, atkVsInfAttCav, atkVsRngAttCav,
                       baseDefTroopTypeBuffAttCav, marcherDefTroopBuffAttCav,
                       defVsCavAttCav, defVsInfAttCav, defVsRngAttCav,
                       baseHealthTroopBuffAttCav, marcherHealthTroopBuffAttCav),
            _build_att("Infantry", tierAttInf, msizeAttInf, baseAttTroopTypeBuffAttInf, marcherTroopBuffAttInf,
                       atkVsCavAttInf, atkVsInfAttInf, atkVsRngAttInf,
                       baseDefTroopTypeBuffAttInf, marcherDefTroopBuffAttInf,
                       defVsCavAttInf, defVsInfAttInf, defVsRngAttInf,
                       baseHealthTroopBuffAttInf, marcherHealthTroopBuffAttInf),
            _build_att("Ranged", tierAttRng, msizeAttRng, baseAttTroopTypeBuffAttRng, marcherTroopBuffAttRng,
                       atkVsCavAttRng, atkVsInfAttRng, atkVsRngAttRng,
                       baseDefTroopTypeBuffAttRng, marcherDefTroopBuffAttRng,
                       defVsCavAttRng, defVsInfAttRng, defVsRngAttRng,
                       baseHealthTroopBuffAttRng, marcherHealthTroopBuffAttRng),
            _build_att("Cavalry", tierAttCav2, msizeAttCav2, baseAttTroopTypeBuffAttCav2, marcherTroopBuffAttCav2,
                       atkVsCavAttCav2, atkVsInfAttCav2, atkVsRngAttCav2,
                       baseDefTroopTypeBuffAttCav2, marcherDefTroopBuffAttCav2,
                       defVsCavAttCav2, defVsInfAttCav2, defVsRngAttCav2,
                       baseHealthTroopBuffAttCav2, marcherHealthTroopBuffAttCav2),
            _build_att("Infantry", tierAttInf2, msizeAttInf2, baseAttTroopTypeBuffAttInf2, marcherTroopBuffAttInf2,
                       atkVsCavAttInf2, atkVsInfAttInf2, atkVsRngAttInf2,
                       baseDefTroopTypeBuffAttInf2, marcherDefTroopBuffAttInf2,
                       defVsCavAttInf2, defVsInfAttInf2, defVsRngAttInf2,
                       baseHealthTroopBuffAttInf2, marcherHealthTroopBuffAttInf2),
            _build_att("Ranged", tierAttRng2, msizeAttRng2, baseAttTroopTypeBuffAttRng2, marcherTroopBuffAttRng2,
                       atkVsCavAttRng2, atkVsInfAttRng2, atkVsRngAttRng2,
                       baseDefTroopTypeBuffAttRng2, marcherDefTroopBuffAttRng2,
                       defVsCavAttRng2, defVsInfAttRng2, defVsRngAttRng2,
                       baseHealthTroopBuffAttRng2, marcherHealthTroopBuffAttRng2),
        ]

        defenders = [
            _build_def("Infantry", tierDefInf, msizeDefInf,
                       baseDefTroopTypeBuffDefInf, baseHealthTroopBuffDefInf,
                       defenseatsopBuffDefInf, healthatsopBuffDefInf,
                       defVsCavDefInf, defVsInfDefInf, defVsRngDefInf,
                       defenderdefenseBuffDefInf, defenderhealthBuffDefInf,
                       baseAtkTroopTypeBuffDefInf, attackatsopBuffDefInf, defenderattackBuffDefInf,
                       atkVsCavDefInf, atkVsInfDefInf, atkVsRngDefInf),

            _build_def("Ranged", tierDefRng, msizeDefRng,
                       baseDefTroopTypeBuffDefRng, baseHealthTroopBuffDefRng,
                       defenseatsopBuffDefRng, healthatsopBuffDefRng,
                       defVsCavDefRng, defVsInfDefRng, defVsRngDefRng,
                       defenderdefenseBuffDefRng, defenderhealthBuffDefRng,
                       baseAtkTroopTypeBuffDefRng, attackatsopBuffDefRng, defenderattackBuffDefRng,
                       atkVsCavDefRng, atkVsInfDefRng, atkVsRngDefRng),

            _build_def("Cavalry", tierDefCav, msizeDefCav,
                       baseDefTroopTypeBuffDefCav, baseHealthTroopBuffDefCav,
                       defenseatsopBuffDefCav, healthatsopBuffDefCav,
                       defVsCavDefCav, defVsInfDefCav, defVsRngDefCav,
                       defenderdefenseBuffDefCav, defenderhealthBuffDefCav,
                       baseAtkTroopTypeBuffDefCav, attackatsopBuffDefCav, defenderattackBuffDefCav,
                       atkVsCavDefCav, atkVsInfDefCav, atkVsRngDefCav),
        ]

        res = compute_battle_outcome(
            attackers=attackers,
            defenders=defenders,
            scenario="rally_vs_multi_reinforcement",
        )
        res["report_mode"] = report_mode
        _render_result(res)


if choice == battle_formats[0]:
    battle_solo_vs_solo()
elif choice == battle_formats[1]:
    battle_rally_vs_multi()


