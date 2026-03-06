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
    pair_rows = list(res.get("pairwise_exchange_rows", []))
    attacker_names = list(res.get("attacker_names", []))
    defender_names = list(res.get("defender_names", []))
    if not pair_rows:
        return pd.DataFrame(columns=["Section", "From", "To", "TroopsLost"])

    def att_label(slot: int) -> str:
        idx = slot - 1
        if 0 <= idx < len(attacker_names) and str(attacker_names[idx]).strip():
            return str(attacker_names[idx]).strip()
        return f"Attacker{slot}"

    def def_label(slot: int) -> str:
        idx = slot - 1
        if 0 <= idx < len(defender_names) and str(defender_names[idx]).strip():
            return str(defender_names[idx]).strip()
        return f"Defender{slot}"

    detailed_rows = []
    for r in pair_rows:
        a_slot = int(r.get("AttackerSlot", 0))
        d_slot = int(r.get("DefenderSlot", 0))
        detailed_rows.append({
            "Section": "Attacker vs Defender",
            "From": att_label(a_slot),
            "To": def_label(d_slot),
            "TroopsLost": int(r.get("DefenderLossesFromAttacker", 0)),
        })
        detailed_rows.append({
            "Section": "Defender vs Attacker",
            "From": def_label(d_slot),
            "To": att_label(a_slot),
            "TroopsLost": int(r.get("AttackerLossesFromDefender", 0)),
        })

    attacker_losses_slot = list(res.get("attacker_losses_by_slot", []))
    defender_losses_slot = list(res.get("defender_losses_by_slot", []))

    for i, v in enumerate(attacker_losses_slot, start=1):
        detailed_rows.append({
            "Section": "Attacker Total Loss",
            "From": att_label(i),
            "To": "",
            "TroopsLost": int(v),
        })
    for i, v in enumerate(defender_losses_slot, start=1):
        detailed_rows.append({
            "Section": "Defender Total Loss",
            "From": def_label(i),
            "To": "",
            "TroopsLost": int(v),
        })

    detailed_rows.append({
        "Section": "Total Defender Losses",
        "From": "All Defenders",
        "To": "",
        "TroopsLost": int(res.get("defender_losses_total", 0)),
    })
    detailed_rows.append({
        "Section": "Total Attacker Losses",
        "From": "All Attackers",
        "To": "",
        "TroopsLost": int(res.get("attacker_losses_total", 0)),
    })

    return pd.DataFrame(detailed_rows)


def simplified_rally_losses_df(res: dict) -> pd.DataFrame:
    attacker_losses_slot = list(res.get("attacker_losses_by_slot", []))
    defender_losses_slot = list(res.get("defender_losses_by_slot", []))
    attacker_names = list(res.get("attacker_names", []))
    defender_names = list(res.get("defender_names", []))

    def att_label(slot: int) -> str:
        idx = slot - 1
        if 0 <= idx < len(attacker_names) and str(attacker_names[idx]).strip():
            return str(attacker_names[idx]).strip()
        return f"Attacker{slot}"

    def def_label(slot: int) -> str:
        idx = slot - 1
        if 0 <= idx < len(defender_names) and str(defender_names[idx]).strip():
            return str(defender_names[idx]).strip()
        return f"Defender{slot}"

    rows = []
    for i, v in enumerate(defender_losses_slot, start=1):
        rows.append({"Section": "Defender Total Loss", "Name": def_label(i), "TroopsLost": int(v)})
    for i, v in enumerate(attacker_losses_slot, start=1):
        rows.append({"Section": "Attacker Total Loss", "Name": att_label(i), "TroopsLost": int(v)})
    rows.append({"Section": "Total Defender Losses", "Name": "All Defenders", "TroopsLost": int(res.get("defender_losses_total", 0))})
    rows.append({"Section": "Total Attacker Losses", "Name": "All Attackers", "TroopsLost": int(res.get("attacker_losses_total", 0))})

    return pd.DataFrame(rows, columns=["Section", "Name", "TroopsLost"])


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

    attacker_troop_cycle = ["Cavalry", "Infantry", "Ranged"]
    defender_troop_cycle = ["Infantry", "Ranged", "Cavalry"]

    attacker_defaults = {
        "Cavalry": {
            "base_att": 1317.48,
            "base_def": 1197.68,
            "base_hp": 337.45,
            "atk_vs_inf": 471.49,
            "atk_vs_rng": 1642.80,
            "atk_vs_cav": 1620.69,
            "def_vs_inf": 1094.47,
            "def_vs_rng": 917.15,
            "def_vs_cav": 521.90,
            "marcher_att": 7271.58,
            "marcher_def": 2500.0,
            "marcher_hp": 2400.0,
        },
        "Infantry": {
            "base_att": 1390.35,
            "base_def": 1018.42,
            "base_hp": 365.07,
            "atk_vs_inf": 1097.48,
            "atk_vs_rng": 346.15,
            "atk_vs_cav": 1610.51,
            "def_vs_inf": 589.85,
            "def_vs_rng": 608.53,
            "def_vs_cav": 917.99,
            "marcher_att": 6873.38,
            "marcher_def": 2500.0,
            "marcher_hp": 2400.0,
        },
        "Ranged": {
            "base_att": 1308.81,
            "base_def": 1225.62,
            "base_hp": 438.98,
            "atk_vs_inf": 1717.59,
            "atk_vs_rng": 1483.59,
            "atk_vs_cav": 436.92,
            "def_vs_inf": 989.71,
            "def_vs_rng": 477.20,
            "def_vs_cav": 838.02,
            "marcher_att": 7415.18,
            "marcher_def": 2500.0,
            "marcher_hp": 2400.0,
        },
    }

    defender_defaults = {
        "Cavalry": {
            "base_att": 1317.48,
            "base_def": 1197.68,
            "base_hp": 337.45,
            "atk_vs_inf": 471.49,
            "atk_vs_rng": 1642.80,
            "atk_vs_cav": 1620.69,
            "def_vs_inf": 1094.47,
            "def_vs_rng": 917.15,
            "def_vs_cav": 521.90,
            "atk_sop": 2400.0,
            "def_sop": 2310.14,
            "hp_sop": 2873.64,
            "defender_att": 67.0,
            "defender_def": 86.0,
            "defender_hp": 45.0,
        },
        "Infantry": {
            "base_att": 1390.35,
            "base_def": 1018.42,
            "base_hp": 365.07,
            "atk_vs_inf": 1097.48,
            "atk_vs_rng": 346.15,
            "atk_vs_cav": 1610.51,
            "def_vs_inf": 589.85,
            "def_vs_rng": 608.53,
            "def_vs_cav": 917.99,
            "atk_sop": 2400.0,
            "def_sop": 2600.58,
            "hp_sop": 2108.68,
            "defender_att": 67.0,
            "defender_def": 86.0,
            "defender_hp": 96.41,
        },
        "Ranged": {
            "base_att": 1308.81,
            "base_def": 1225.62,
            "base_hp": 438.98,
            "atk_vs_inf": 1717.59,
            "atk_vs_rng": 1483.59,
            "atk_vs_cav": 436.92,
            "def_vs_inf": 989.71,
            "def_vs_rng": 477.20,
            "def_vs_cav": 838.02,
            "atk_sop": 2400.0,
            "def_sop": 2720.27,
            "hp_sop": 2302.55,
            "defender_att": 67.0,
            "defender_def": 86.0,
            "defender_hp": 87.23,
        },
    }

    if "rally_multi_att_forms" not in st.session_state:
        st.session_state.rally_multi_att_forms = 6
    if "rally_multi_def_forms" not in st.session_state:
        st.session_state.rally_multi_def_forms = 3

    st.write("### Forms")
    att_controls = st.columns(4)
    with att_controls[0]:
        if st.button("+ Attacker Form", key="add_attacker_form"):
            st.session_state.rally_multi_att_forms += 1
    with att_controls[1]:
        if st.button("- Attacker Form", key="remove_attacker_form", disabled=st.session_state.rally_multi_att_forms <= 1):
            st.session_state.rally_multi_att_forms -= 1
    with att_controls[2]:
        st.caption(f"Attacker forms: {st.session_state.rally_multi_att_forms}")
    with att_controls[3]:
        if st.button("Reset 6v3", key="reset_rally_forms"):
            st.session_state.rally_multi_att_forms = 6
            st.session_state.rally_multi_def_forms = 3

    def_controls = st.columns(3)
    with def_controls[0]:
        if st.button("+ Defender Form", key="add_defender_form"):
            st.session_state.rally_multi_def_forms += 1
    with def_controls[1]:
        if st.button("- Defender Form", key="remove_defender_form", disabled=st.session_state.rally_multi_def_forms <= 1):
            st.session_state.rally_multi_def_forms -= 1
    with def_controls[2]:
        st.caption(f"Defender forms: {st.session_state.rally_multi_def_forms}")

    def _apply_attacker_defaults(slot_idx: int):
        key_prefix = f"rally_att_{slot_idx}"
        troop_type = st.session_state.get(f"{key_prefix}_troop_type", attacker_troop_cycle[slot_idx % len(attacker_troop_cycle)])
        d = attacker_defaults[troop_type]
        st.session_state[f"{key_prefix}_msize"] = 400000
        st.session_state[f"{key_prefix}_base_att"] = d["base_att"]
        st.session_state[f"{key_prefix}_base_def"] = d["base_def"]
        st.session_state[f"{key_prefix}_base_hp"] = d["base_hp"]
        st.session_state[f"{key_prefix}_atk_vs_inf"] = d["atk_vs_inf"]
        st.session_state[f"{key_prefix}_atk_vs_rng"] = d["atk_vs_rng"]
        st.session_state[f"{key_prefix}_atk_vs_cav"] = d["atk_vs_cav"]
        st.session_state[f"{key_prefix}_def_vs_inf"] = d["def_vs_inf"]
        st.session_state[f"{key_prefix}_def_vs_rng"] = d["def_vs_rng"]
        st.session_state[f"{key_prefix}_def_vs_cav"] = d["def_vs_cav"]
        st.session_state[f"{key_prefix}_marcher_att"] = d["marcher_att"]
        st.session_state[f"{key_prefix}_marcher_def"] = d["marcher_def"]
        st.session_state[f"{key_prefix}_marcher_hp"] = d["marcher_hp"]

    def _apply_defender_defaults(slot_idx: int):
        key_prefix = f"rally_def_{slot_idx}"
        troop_type = st.session_state.get(f"{key_prefix}_troop_type", defender_troop_cycle[slot_idx % len(defender_troop_cycle)])
        d = defender_defaults[troop_type]
        st.session_state[f"{key_prefix}_msize"] = 400000
        st.session_state[f"{key_prefix}_base_att"] = d["base_att"]
        st.session_state[f"{key_prefix}_base_def"] = d["base_def"]
        st.session_state[f"{key_prefix}_base_hp"] = d["base_hp"]
        st.session_state[f"{key_prefix}_atk_vs_inf"] = d["atk_vs_inf"]
        st.session_state[f"{key_prefix}_atk_vs_rng"] = d["atk_vs_rng"]
        st.session_state[f"{key_prefix}_atk_vs_cav"] = d["atk_vs_cav"]
        st.session_state[f"{key_prefix}_def_vs_inf"] = d["def_vs_inf"]
        st.session_state[f"{key_prefix}_def_vs_rng"] = d["def_vs_rng"]
        st.session_state[f"{key_prefix}_def_vs_cav"] = d["def_vs_cav"]
        st.session_state[f"{key_prefix}_atk_sop"] = d["atk_sop"]
        st.session_state[f"{key_prefix}_def_sop"] = d["def_sop"]
        st.session_state[f"{key_prefix}_hp_sop"] = d["hp_sop"]
        st.session_state[f"{key_prefix}_defender_att"] = d["defender_att"]
        st.session_state[f"{key_prefix}_defender_def"] = d["defender_def"]
        st.session_state[f"{key_prefix}_defender_hp"] = d["defender_hp"]

    def _ensure_state(key: str, default):
        if key not in st.session_state:
            st.session_state[key] = default

    attacker_field_suffixes = [
        "name",
        "troop_type",
        "tier",
        "msize",
        "base_att",
        "base_def",
        "base_hp",
        "atk_vs_inf",
        "atk_vs_rng",
        "atk_vs_cav",
        "def_vs_inf",
        "def_vs_rng",
        "def_vs_cav",
        "marcher_att",
        "marcher_def",
        "marcher_hp",
    ]
    defender_field_suffixes = [
        "name",
        "troop_type",
        "tier",
        "msize",
        "base_att",
        "base_def",
        "base_hp",
        "atk_vs_inf",
        "atk_vs_rng",
        "atk_vs_cav",
        "def_vs_inf",
        "def_vs_rng",
        "def_vs_cav",
        "atk_sop",
        "def_sop",
        "hp_sop",
        "defender_att",
        "defender_def",
        "defender_hp",
    ]

    def _remove_attacker_form(slot_idx: int):
        total = st.session_state.rally_multi_att_forms
        if total <= 1:
            return
        for i in range(slot_idx, total - 1):
            for suffix in attacker_field_suffixes:
                src = f"rally_att_{i + 1}_{suffix}"
                dst = f"rally_att_{i}_{suffix}"
                if src in st.session_state:
                    st.session_state[dst] = st.session_state[src]
        for suffix in attacker_field_suffixes:
            st.session_state.pop(f"rally_att_{total - 1}_{suffix}", None)
        st.session_state.rally_multi_att_forms -= 1

    def _remove_defender_form(slot_idx: int):
        total = st.session_state.rally_multi_def_forms
        if total <= 1:
            return
        for i in range(slot_idx, total - 1):
            for suffix in defender_field_suffixes:
                src = f"rally_def_{i + 1}_{suffix}"
                dst = f"rally_def_{i}_{suffix}"
                if src in st.session_state:
                    st.session_state[dst] = st.session_state[src]
        for suffix in defender_field_suffixes:
            st.session_state.pop(f"rally_def_{total - 1}_{suffix}", None)
        st.session_state.rally_multi_def_forms -= 1

    def render_attacker_form(slot_idx: int, default_troop: str):
        key_prefix = f"rally_att_{slot_idx}"
        _ensure_state(f"{key_prefix}_name", f"Attacker {slot_idx + 1}")
        st.text_input("Name", key=f"{key_prefix}_name")
        troop_key = f"{key_prefix}_troop_type"
        _ensure_state(troop_key, default_troop)
        troop_type = st.selectbox("Troop Type", options=["Infantry", "Ranged", "Cavalry"], key=troop_key)
        form_action_cols = st.columns(2)
        with form_action_cols[0]:
            st.form_submit_button(
                "Load Defaults",
                key=f"{key_prefix}_load_defaults",
                on_click=_apply_attacker_defaults,
                kwargs={"slot_idx": slot_idx},
            )
        with form_action_cols[1]:
            st.form_submit_button(
                "Remove",
                key=f"{key_prefix}_remove_form",
                on_click=_remove_attacker_form,
                kwargs={"slot_idx": slot_idx},
                disabled=st.session_state.rally_multi_att_forms <= 1,
            )
        d = attacker_defaults[troop_type]
        _ensure_state(f"{key_prefix}_tier", 11)
        _ensure_state(f"{key_prefix}_msize", 400000)
        _ensure_state(f"{key_prefix}_base_att", d["base_att"])
        _ensure_state(f"{key_prefix}_base_def", d["base_def"])
        _ensure_state(f"{key_prefix}_base_hp", d["base_hp"])
        _ensure_state(f"{key_prefix}_atk_vs_inf", d["atk_vs_inf"])
        _ensure_state(f"{key_prefix}_atk_vs_rng", d["atk_vs_rng"])
        _ensure_state(f"{key_prefix}_atk_vs_cav", d["atk_vs_cav"])
        _ensure_state(f"{key_prefix}_def_vs_inf", d["def_vs_inf"])
        _ensure_state(f"{key_prefix}_def_vs_rng", d["def_vs_rng"])
        _ensure_state(f"{key_prefix}_def_vs_cav", d["def_vs_cav"])
        _ensure_state(f"{key_prefix}_marcher_att", d["marcher_att"])
        _ensure_state(f"{key_prefix}_marcher_def", d["marcher_def"])
        _ensure_state(f"{key_prefix}_marcher_hp", d["marcher_hp"])

        return {
            "name": st.session_state.get(f"{key_prefix}_name", "").strip(),
            "troop_type": troop_type,
            "tier": st.selectbox("Troop Tier", options=[11, 12], key=f"{key_prefix}_tier"),
            "msize": st.number_input("March Size", min_value=1, key=f"{key_prefix}_msize"),
            "base_att": st.number_input("Base Troop Type Attack Buff", min_value=0.0, key=f"{key_prefix}_base_att"),
            "base_def": st.number_input("Base Troop Type Defense Buff", min_value=0.0, key=f"{key_prefix}_base_def"),
            "base_hp": st.number_input("Base Troop Health Buff", min_value=0.0, key=f"{key_prefix}_base_hp"),
            "atk_vs_inf": st.number_input("Attack vs Infantry", min_value=0.0, key=f"{key_prefix}_atk_vs_inf"),
            "atk_vs_rng": st.number_input("Attack vs Ranged", min_value=0.0, key=f"{key_prefix}_atk_vs_rng"),
            "atk_vs_cav": st.number_input("Attack vs Cavalry", min_value=0.0, key=f"{key_prefix}_atk_vs_cav"),
            "def_vs_inf": st.number_input("Defense vs Infantry", min_value=0.0, key=f"{key_prefix}_def_vs_inf"),
            "def_vs_rng": st.number_input("Defense vs Ranged", min_value=0.0, key=f"{key_prefix}_def_vs_rng"),
            "def_vs_cav": st.number_input("Defense vs Cavalry", min_value=0.0, key=f"{key_prefix}_def_vs_cav"),
            "marcher_att": st.number_input("Marcher Troop Type Attack", min_value=0.0, key=f"{key_prefix}_marcher_att"),
            "marcher_def": st.number_input("Marcher Troop Type Defense", min_value=0.0, key=f"{key_prefix}_marcher_def"),
            "marcher_hp": st.number_input("Marcher Troop Type Health", min_value=0.0, key=f"{key_prefix}_marcher_hp"),
        }

    def render_defender_form(slot_idx: int, default_troop: str):
        key_prefix = f"rally_def_{slot_idx}"
        _ensure_state(f"{key_prefix}_name", f"Defender {slot_idx + 1}")
        st.text_input("Name", key=f"{key_prefix}_name")
        troop_key = f"{key_prefix}_troop_type"
        _ensure_state(troop_key, default_troop)
        troop_type = st.selectbox("Troop Type", options=["Infantry", "Ranged", "Cavalry"], key=troop_key)
        form_action_cols = st.columns(2)
        with form_action_cols[0]:
            st.form_submit_button(
                "Load Defaults",
                key=f"{key_prefix}_load_defaults",
                on_click=_apply_defender_defaults,
                kwargs={"slot_idx": slot_idx},
            )
        with form_action_cols[1]:
            st.form_submit_button(
                "Remove",
                key=f"{key_prefix}_remove_form",
                on_click=_remove_defender_form,
                kwargs={"slot_idx": slot_idx},
                disabled=st.session_state.rally_multi_def_forms <= 1,
            )
        d = defender_defaults[troop_type]
        _ensure_state(f"{key_prefix}_tier", 11)
        _ensure_state(f"{key_prefix}_msize", 400000)
        _ensure_state(f"{key_prefix}_base_att", d["base_att"])
        _ensure_state(f"{key_prefix}_base_def", d["base_def"])
        _ensure_state(f"{key_prefix}_base_hp", d["base_hp"])
        _ensure_state(f"{key_prefix}_atk_vs_inf", d["atk_vs_inf"])
        _ensure_state(f"{key_prefix}_atk_vs_rng", d["atk_vs_rng"])
        _ensure_state(f"{key_prefix}_atk_vs_cav", d["atk_vs_cav"])
        _ensure_state(f"{key_prefix}_def_vs_inf", d["def_vs_inf"])
        _ensure_state(f"{key_prefix}_def_vs_rng", d["def_vs_rng"])
        _ensure_state(f"{key_prefix}_def_vs_cav", d["def_vs_cav"])
        _ensure_state(f"{key_prefix}_atk_sop", d["atk_sop"])
        _ensure_state(f"{key_prefix}_def_sop", d["def_sop"])
        _ensure_state(f"{key_prefix}_hp_sop", d["hp_sop"])
        _ensure_state(f"{key_prefix}_defender_att", d["defender_att"])
        _ensure_state(f"{key_prefix}_defender_def", d["defender_def"])
        _ensure_state(f"{key_prefix}_defender_hp", d["defender_hp"])

        return {
            "name": st.session_state.get(f"{key_prefix}_name", "").strip(),
            "troop_type": troop_type,
            "tier": st.selectbox("Troop Tier", options=[11, 12], key=f"{key_prefix}_tier"),
            "msize": st.number_input("March Size", min_value=1, key=f"{key_prefix}_msize"),
            "base_att": st.number_input("Base Troop Type Attack Buff", min_value=0.0, key=f"{key_prefix}_base_att"),
            "base_def": st.number_input("Base Troop Type Defense Buff", min_value=0.0, key=f"{key_prefix}_base_def"),
            "base_hp": st.number_input("Base Troop Health Buff", min_value=0.0, key=f"{key_prefix}_base_hp"),
            "atk_vs_inf": st.number_input("Attack vs Infantry", min_value=0.0, key=f"{key_prefix}_atk_vs_inf"),
            "atk_vs_rng": st.number_input("Attack vs Ranged", min_value=0.0, key=f"{key_prefix}_atk_vs_rng"),
            "atk_vs_cav": st.number_input("Attack vs Cavalry", min_value=0.0, key=f"{key_prefix}_atk_vs_cav"),
            "def_vs_inf": st.number_input("Defense vs Infantry", min_value=0.0, key=f"{key_prefix}_def_vs_inf"),
            "def_vs_rng": st.number_input("Defense vs Ranged", min_value=0.0, key=f"{key_prefix}_def_vs_rng"),
            "def_vs_cav": st.number_input("Defense vs Cavalry", min_value=0.0, key=f"{key_prefix}_def_vs_cav"),
            "atk_sop": st.number_input("Attack at SOP", min_value=0.0, key=f"{key_prefix}_atk_sop"),
            "def_sop": st.number_input("Defense at SOP", min_value=0.0, key=f"{key_prefix}_def_sop"),
            "hp_sop": st.number_input("Health at SOP", min_value=0.0, key=f"{key_prefix}_hp_sop"),
            "defender_att": st.number_input("Defender Attack Buff", min_value=0.0, key=f"{key_prefix}_defender_att"),
            "defender_def": st.number_input("Defender Defense Buff", min_value=0.0, key=f"{key_prefix}_defender_def"),
            "defender_hp": st.number_input("Defender Health Buff", min_value=0.0, key=f"{key_prefix}_defender_hp"),
        }

    with st.form(key="battle_rally_multi_simulator_form"):
        st.write("### Attackers Stats")
        attacker_forms_input = []
        attacker_cols = st.columns(3)
        for i in range(st.session_state.rally_multi_att_forms):
            with attacker_cols[i % 3]:
                st.write(f"### Attacker {i + 1}")
                attacker_forms_input.append(render_attacker_form(i, attacker_troop_cycle[i % len(attacker_troop_cycle)]))

        st.write("### Defenders Stats")
        defender_forms_input = []
        defender_cols = st.columns(3)
        for i in range(st.session_state.rally_multi_def_forms):
            with defender_cols[i % 3]:
                st.write(f"### Defender {i + 1}")
                defender_forms_input.append(render_defender_form(i, defender_troop_cycle[i % len(defender_troop_cycle)]))

        submitted = st.form_submit_button("Simulate Battle")

    if submitted:
        attacker_names = [row.get("name", "").strip() or f"Attacker{i + 1}" for i, row in enumerate(attacker_forms_input)]
        defender_names = [row.get("name", "").strip() or f"Defender{i + 1}" for i, row in enumerate(defender_forms_input)]
        attackers = [
            _build_att(
                row["troop_type"],
                row["tier"],
                row["msize"],
                row["base_att"],
                row["marcher_att"],
                row["atk_vs_cav"],
                row["atk_vs_inf"],
                row["atk_vs_rng"],
                row["base_def"],
                row["marcher_def"],
                row["def_vs_cav"],
                row["def_vs_inf"],
                row["def_vs_rng"],
                row["base_hp"],
                row["marcher_hp"],
            )
            for row in attacker_forms_input
        ]

        defenders = [
            _build_def(
                row["troop_type"],
                row["tier"],
                row["msize"],
                row["base_def"],
                row["base_hp"],
                row["def_sop"],
                row["hp_sop"],
                row["def_vs_cav"],
                row["def_vs_inf"],
                row["def_vs_rng"],
                row["defender_def"],
                row["defender_hp"],
                row["base_att"],
                row["atk_sop"],
                row["defender_att"],
                row["atk_vs_cav"],
                row["atk_vs_inf"],
                row["atk_vs_rng"],
            )
            for row in defender_forms_input
        ]

        res = compute_battle_outcome(
            attackers=attackers,
            defenders=defenders,
            scenario="rally_vs_multi_reinforcement",
        )
        res["report_mode"] = report_mode
        res["attacker_names"] = attacker_names
        res["defender_names"] = defender_names
        _render_result(res)

if choice == battle_formats[0]:
    battle_solo_vs_solo()
elif choice == battle_formats[1]:
    battle_rally_vs_multi()



