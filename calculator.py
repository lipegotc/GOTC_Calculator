from __future__ import annotations
from typing import Any, Dict, List, Mapping
from models import siege, DragonInfo, TroopType, attackBattleStats, defenseBattleStats
from data import load_troopBaseData, load_dragonBaseData, load_damageModifiers, load_maxedStats, load_siegestats, load_sophealth
from helpers import *
import math
from models import _to_float


_TROOPTYPE_TO_JSON = {
    TroopType.INFANTRY: "Infantry",
    TroopType.RANGED: "Ranged",
    TroopType.CAVALRY: "Cavalry",
}

_TROOPTYPE_TO_TROOPKEY_PREFIX = {
    TroopType.INFANTRY: "Infantry",
    TroopType.RANGED: "Ranged",
    TroopType.CAVALRY: "Cavalry",
}


def _normalize_troop_type(tt: Any) -> TroopType:
    """Accept TroopType or strings like 'inf', 'rng', 'cav'."""
    if isinstance(tt, TroopType):
        return tt
    if isinstance(tt, str):
        return TroopType(tt.lower().strip())
    raise TypeError(f"troop_type must be TroopType or str, got {type(tt)}")

def calc_wall_damage(
    siege_input,  
    sop_stars: Any,
    siege_by_tier: Mapping[int, Any],   
    sop_by_star: Mapping[Any, Any],  
) -> dict:


    tier = siege_input.tier
    march_size = siege_input.msize
    wdb_pp = siege_input.wdb 


    if tier not in siege_by_tier:
        raise KeyError(f"Unknown siege tier: {tier}. Available: {sorted(siege_by_tier.keys())}")

    tier_row = siege_by_tier[tier]
    base_damage = float(tier_row.damage) 

    stars_key = _to_float(sop_stars, default=None)
    if stars_key is None:
        raise ValueError(f"Invalid sop_stars: {sop_stars}")

    sop_row = sop_by_star.get(stars_key)
    if sop_row is None:

        if float(stars_key).is_integer():
            sop_row = sop_by_star.get(int(stars_key))

    if sop_row is None:
        raise KeyError(f"Unknown SoP stars: {sop_stars}. Available: {sorted(sop_by_star.keys())}")

    sop_health = float(sop_row.wall)  
    if sop_health <= 0:
        raise ValueError(f"SoP wall health must be > 0. Got: {sop_health}")


    raw_damage = march_size * base_damage * (1.0 + (wdb_pp / 100.0))
    percent_damage = raw_damage / sop_health

    remaining_wall = max(0.0, sop_health - raw_damage)
    hits_to_break = math.inf if raw_damage <= 0 else math.ceil(sop_health / raw_damage)

    return {
        "inputs": {
            "tier": tier,
            "march_size": march_size,
            "wdb_percent_points": wdb_pp,
            "sop_stars": stars_key,
        },
        "lookups": {
            "base_damage": base_damage,
            "sop_health": sop_health,
        },
        "results": {
            "raw_damage": raw_damage,
            "percent_damage": percent_damage,          
            "percent_damage_pct": percent_damage * 100.0,
            "remaining_wall": remaining_wall,
            "hits_to_break": hits_to_break,
        },
    }


def compute_battle_outcome(
    attackers: List[attackBattleStats],
    defenders: List[defenseBattleStats],
    *,
    scenario: str,
) -> Dict:

    scenario = str(scenario).lower().strip()
    allowed = {"solo_attack_vs_solo_reinforcement", "rally_vs_multi_reinforcement"}
    if scenario not in allowed:
        raise ValueError(f"scenario must be one of: {', '.join(sorted(allowed))}")

    if not attackers or not defenders:
        raise ValueError("attackers and defenders must be non-empty lists")

    if scenario == "solo_attack_vs_solo_reinforcement":
        if len(attackers) != 1 or len(defenders) != 1:
            raise ValueError("solo_attack_vs_solo_reinforcement expects exactly 1 attacker and 1 defender")

    troops = load_troopBaseData()
    mods = load_damageModifiers()
    if not troops:
        raise RuntimeError("TroopBaseStats.json did not load (empty dict).")
    if not mods:
        raise RuntimeError("DamageModifiers.json did not load (empty dict).")

    def troop_key(tt: TroopType, tier: int) -> str:
        return f"{_TROOPTYPE_TO_TROOPKEY_PREFIX[tt]}_{tier}"

    def dmg_mod(tier: int, src_tt: TroopType, tgt_tt: TroopType) -> float:
        tier_key = f"T{tier}"
        src_json = _TROOPTYPE_TO_JSON[src_tt]
        tgt_json = _TROOPTYPE_TO_JSON[tgt_tt]
        return float(mods[tier_key][src_json][tgt_json])

    def atk_vs(att: attackBattleStats, tgt_tt: TroopType) -> float:

        if tgt_tt == TroopType.INFANTRY:
            return att.attvsinf / 100.0
        if tgt_tt == TroopType.RANGED:
            return att.attvsrng / 100.0
        return att.attvscav / 100.0

    def att_def_vs(att: attackBattleStats, tgt_tt: TroopType) -> float:

        if tgt_tt == TroopType.INFANTRY:
            v = att.defvsinf if att.defvsinf != 0 else att.attvsinf
            return v / 100.0
        if tgt_tt == TroopType.RANGED:
            v = att.defvsrng if att.defvsrng != 0 else att.attvsrng
            return v / 100.0
        v = att.defvscav if att.defvscav != 0 else att.attvscav
        return v / 100.0

    def def_att_vs(defn: defenseBattleStats, tgt_tt: TroopType) -> float:

        if tgt_tt == TroopType.INFANTRY:
            v = defn.attvsinf if defn.attvsinf != 0 else defn.defvsinf
            return v / 100.0
        if tgt_tt == TroopType.RANGED:
            v = defn.attvsrng if defn.attvsrng != 0 else defn.defvsrng
            return v / 100.0
        v = defn.attvscav if defn.attvscav != 0 else defn.defvscav
        return v / 100.0

    def def_vs(defn: defenseBattleStats, tgt_tt: TroopType) -> float:

        if tgt_tt == TroopType.INFANTRY:
            return defn.defvsinf / 100.0
        if tgt_tt == TroopType.RANGED:
            return defn.defvsrng / 100.0
        return defn.defvscav / 100.0

    attacker_rows = []
    for a in attackers:
        ttA = a.TroopType
        tierA = int(a.TroopTier)
        if tierA <= 0:
            raise ValueError("attacker TroopTier must be > 0")
        keyA = troop_key(ttA, tierA)
        if keyA not in troops:
            raise KeyError(f"Missing attacker troop '{keyA}' in TroopBaseStats.json")

        tA = troops[keyA]
        base_atk = float(getattr(tA, "attack"))
        base_def = float(getattr(tA, "defense"))
        base_hp = float(getattr(tA, "health"))
        rngA = int(getattr(tA, "range"))

        # Attacker offense
        atk_mul = 1.0 + (a.baseAttackBuff / 100.0) + (a.marcherAttackBuff / 100.0)
        att_vs_inf = base_atk * atk_mul * (1.0 + atk_vs(a, TroopType.INFANTRY))
        att_vs_cav = base_atk * atk_mul * (1.0 + atk_vs(a, TroopType.CAVALRY))
        att_vs_rng = base_atk * atk_mul * (1.0 + atk_vs(a, TroopType.RANGED))

        att_hp_mul = 1.0 + (a.baseHealthBuff / 100.0) + (a.marcherHealthBuff / 100.0)
        att_total_hp = base_hp * att_hp_mul
        att_def_mul = 1.0 + (a.baseDefenseBuff / 100.0) + (a.marcherDefenseBuff / 100.0)
        att_def_vs_inf = base_def * att_def_mul * (1.0 + att_def_vs(a, TroopType.INFANTRY))
        att_def_vs_cav = base_def * att_def_mul * (1.0 + att_def_vs(a, TroopType.CAVALRY))
        att_def_vs_rng = base_def * att_def_mul * (1.0 + att_def_vs(a, TroopType.RANGED))
        att_totaldef_vs_inf = att_total_hp * att_def_vs_inf
        att_totaldef_vs_cav = att_total_hp * att_def_vs_cav
        att_totaldef_vs_rng = att_total_hp * att_def_vs_rng

        attacker_rows.append({
            "type": ttA,
            "type_json": _TROOPTYPE_TO_JSON[ttA],
            "tier": tierA,
            "msize": int(a.msizeAtt),
            "base_attack_buff_pp": float(a.baseAttackBuff),
            "marcher_attack_buff_pp": float(a.marcherAttackBuff),
            "base_defense_buff_pp": float(a.baseDefenseBuff),
            "marcher_defense_buff_pp": float(a.marcherDefenseBuff),
            "base_health_buff_pp": float(a.baseHealthBuff),
            "marcher_health_buff_pp": float(a.marcherHealthBuff),
            "base_atk": base_atk,
            "base_def": base_def,
            "base_hp": base_hp,
            "range": rngA,
            "atk_mul": atk_mul,
            "att_base_after_buffs": base_atk * atk_mul,
            "att_vs_pct": {
                "Infantry": atk_vs(a, TroopType.INFANTRY),
                "Cavalry": atk_vs(a, TroopType.CAVALRY),
                "Ranged": atk_vs(a, TroopType.RANGED),
            },
            "att_def_mul": att_def_mul,
            "def_base_after_buffs": base_def * att_def_mul,
            "def_vs_pct": {
                "Infantry": att_def_vs(a, TroopType.INFANTRY),
                "Cavalry": att_def_vs(a, TroopType.CAVALRY),
                "Ranged": att_def_vs(a, TroopType.RANGED),
            },
            "hp_mul": att_hp_mul,
            "att_vs": {
                "Infantry": att_vs_inf,
                "Cavalry": att_vs_cav,
                "Ranged": att_vs_rng,
            },
            "total_hp": att_total_hp,
            "def_vs": {
                "Infantry": att_def_vs_inf,
                "Cavalry": att_def_vs_cav,
                "Ranged": att_def_vs_rng,
            },
            "totaldef_vs": {
                "Infantry": att_totaldef_vs_inf,
                "Cavalry": att_totaldef_vs_cav,
                "Ranged": att_totaldef_vs_rng,
            },
        })

    defender_rows = []
    for d in defenders:
        ttD = d.TroopType
        tierD = int(d.TroopTier)
        if tierD <= 0:
            raise ValueError("defender TroopTier must be > 0")
        keyD = troop_key(ttD, tierD)
        if keyD not in troops:
            raise KeyError(f"Missing defender troop '{keyD}' in TroopBaseStats.json")

        tD = troops[keyD]
        base_atk = float(getattr(tD, "attack"))
        base_def = float(getattr(tD, "defense"))
        base_hp = float(getattr(tD, "health"))
        rngD = int(getattr(tD, "range"))

        # Defender offense
        def_atk_mul = 1.0 + (d.baseAttackBuff / 100.0) + (d.attackatsopBuff / 100.0) + (d.defenderattackbuff / 100.0)
        def_att_vs_inf = base_atk * def_atk_mul * (1.0 + def_att_vs(d, TroopType.INFANTRY))
        def_att_vs_cav = base_atk * def_atk_mul * (1.0 + def_att_vs(d, TroopType.CAVALRY))
        def_att_vs_rng = base_atk * def_atk_mul * (1.0 + def_att_vs(d, TroopType.RANGED))

        hp_mul = 1.0 + (d.baseHealthBuff / 100.0) + (d.healthatsopBuff / 100.0) + (d.defenderhealthbuff / 100.0)
        total_hp = base_hp * hp_mul


        def_mul = 1.0 + (d.baseDefenseBuff / 100.0) + (d.defenseatsopBuff / 100.0) + (d.defenderdefensebuff / 100.0)

        def_vs_inf = base_def * def_mul * (1.0 + def_vs(d, TroopType.INFANTRY))
        def_vs_cav = base_def * def_mul * (1.0 + def_vs(d, TroopType.CAVALRY))
        def_vs_rng = base_def * def_mul * (1.0 + def_vs(d, TroopType.RANGED))
        totaldef_vs_inf = total_hp * def_vs_inf
        totaldef_vs_cav = total_hp * def_vs_cav
        totaldef_vs_rng = total_hp * def_vs_rng

        defender_rows.append({
            "type": ttD,
            "type_json": _TROOPTYPE_TO_JSON[ttD],
            "tier": tierD,
            "msize": int(d.msizeDef),
            "base_attack_buff_pp": float(d.baseAttackBuff),
            "attack_at_sop_buff_pp": float(d.attackatsopBuff),
            "defender_attack_buff_pp": float(d.defenderattackbuff),
            "base_defense_buff_pp": float(d.baseDefenseBuff),
            "defense_at_sop_buff_pp": float(d.defenseatsopBuff),
            "defender_defense_buff_pp": float(d.defenderdefensebuff),
            "base_health_buff_pp": float(d.baseHealthBuff),
            "health_at_sop_buff_pp": float(d.healthatsopBuff),
            "defender_health_buff_pp": float(d.defenderhealthbuff),
            "base_atk": base_atk,
            "base_def": base_def,
            "base_hp": base_hp,
            "range": rngD,
            "def_atk_mul": def_atk_mul,
            "def_att_base_after_buffs": base_atk * def_atk_mul,
            "att_vs_pct": {
                "Infantry": def_att_vs(d, TroopType.INFANTRY),
                "Cavalry": def_att_vs(d, TroopType.CAVALRY),
                "Ranged": def_att_vs(d, TroopType.RANGED),
            },
            "def_mul": def_mul,
            "def_base_after_buffs": base_def * def_mul,
            "def_vs_pct": {
                "Infantry": def_vs(d, TroopType.INFANTRY),
                "Cavalry": def_vs(d, TroopType.CAVALRY),
                "Ranged": def_vs(d, TroopType.RANGED),
            },
            "hp_mul": hp_mul,
            "total_hp": total_hp,
            "att_vs": {
                "Infantry": def_att_vs_inf,
                "Cavalry": def_att_vs_cav,
                "Ranged": def_att_vs_rng,
            },
            "def_vs": {
                "Infantry": def_vs_inf,
                "Cavalry": def_vs_cav,
                "Ranged": def_vs_rng,
            },
            "totaldef_vs": {
                "Infantry": totaldef_vs_inf,
                "Cavalry": totaldef_vs_cav,
                "Ranged": totaldef_vs_rng,
            }
        })

    attack_capacity = sum(r["msize"] for r in attacker_rows)
    defense_capacity = sum(r["msize"] for r in defender_rows)

    killed_matrix_att_to_def = {
        "Infantry": {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
        "Cavalry":  {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
        "Ranged":   {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
    }
    killed_matrix_def_to_att = {
        "Infantry": {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
        "Cavalry":  {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
        "Ranged":   {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0},
    }
    defender_losses_by_type = {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0}
    attacker_losses_by_type = {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0}
    kills_by_attacker_type = {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0}
    kills_by_defender_type = {"Infantry": 0.0, "Cavalry": 0.0, "Ranged": 0.0}
    attacker_losses_by_slot = [0.0 for _ in attacker_rows]
    defender_losses_by_slot = [0.0 for _ in defender_rows]
    pairwise_exchange_rows = []

    for ai, A in enumerate(attacker_rows):
        att_tt = A["type"]
        att_name = A["type_json"]

        for di, D in enumerate(defender_rows):
            def_tt = D["type"]
            def_name = D["type_json"]


            atk_base_vs = A["att_vs"][def_name]
            def_base_vs = D["def_vs"][att_name]
            def_hp = D["total_hp"]

            dmgA = dmg_mod(A["tier"], att_tt, def_tt)
            dmgD = dmg_mod(D["tier"], def_tt, att_tt)
            tmodA = tiermodifier(A["tier"], D["tier"])
            tmodD = tiermodifier(D["tier"], A["tier"])
            rmod = rangemodifier(A["range"], D["range"])

            boosted_att_atk = atk_base_vs * dmgA * tmodA * rmod
            boosted_def_def = def_base_vs * dmgD * tmodD
            a_step1 = 1.0 + (A["base_attack_buff_pp"] / 100.0) + (A["marcher_attack_buff_pp"] / 100.0)
            a_step2 = 1.0 + A["att_vs_pct"][def_name]
            a_step3 = A["base_atk"]
            a_step4 = dmgA
            a_step5 = rmod
            a_step6 = tmodA
            boosted_att_atk_calc = boosted_att_atk
            boosted_def_def_calc = boosted_def_def
            def_hp_calc = def_hp

            killed_att_to_def = 0.0
            factor = 0.0
            ratio = 0.0
            if boosted_def_def > 0 and def_hp > 0:
                if scenario == "solo_attack_vs_solo_reinforcement":
                    factor = (A["msize"] ** 2) / D["msize"] if D["msize"] > 0 else 0.0
                else:
                    factor = 0.0 if attack_capacity <= 0 or defense_capacity <= 0 else (
                        (D["msize"] / (defense_capacity ** 2)) * (A["msize"] * attack_capacity)
                    )
                # killed = 4 * (BoostedAttack / (BoostedDefense * Health)) * factor
                boosted_att_atk_calc = boosted_att_atk
                boosted_def_def_calc = boosted_def_def
                def_hp_calc = def_hp
                ratio = boosted_att_atk_calc / (boosted_def_def_calc * def_hp_calc) if factor > 0 else 0.0
                killed_att_to_def = 4.0 * ratio * factor if factor > 0 else 0.0

            def_atk_base_vs = D["att_vs"][att_name]
            att_def_base_vs = A["def_vs"][def_name]
            att_hp = A["total_hp"]
            dmgA_rev = dmg_mod(D["tier"], def_tt, att_tt)
            dmgD_rev = dmg_mod(A["tier"], att_tt, def_tt)
            tmodA_rev = tiermodifier(D["tier"], A["tier"])
            tmodD_rev = tiermodifier(A["tier"], D["tier"])
            rmod_rev = rangemodifier(D["range"], A["range"])

            boosted_def_atk = def_atk_base_vs * dmgA_rev * tmodA_rev * rmod_rev
            boosted_att_def = att_def_base_vs * dmgD_rev * tmodD_rev
            d_step1 = 1.0 + (D["base_attack_buff_pp"] / 100.0) + (D["attack_at_sop_buff_pp"] / 100.0) + (D["defender_attack_buff_pp"] / 100.0)
            d_step2 = 1.0 + D["att_vs_pct"][att_name]
            d_step3 = D["base_atk"]
            d_step4 = dmgA_rev
            d_step5 = rmod_rev
            d_step6 = tmodA_rev
            boosted_def_atk_calc = boosted_def_atk
            boosted_att_def_calc = boosted_att_def
            att_hp_calc = att_hp

            killed_def_to_att = 0.0
            factor_rev = 0.0
            ratio_rev = 0.0
            if boosted_att_def > 0 and att_hp > 0:
                if scenario == "solo_attack_vs_solo_reinforcement":
                    factor_rev = (D["msize"] ** 2) / A["msize"] if A["msize"] > 0 else 0.0
                else:
                    factor_rev = 0.0 if attack_capacity <= 0 or defense_capacity <= 0 else (
                        (A["msize"] / (attack_capacity ** 2)) * (D["msize"] * defense_capacity)
                    )
                boosted_def_atk_calc = boosted_def_atk
                boosted_att_def_calc = boosted_att_def
                att_hp_calc = att_hp
                ratio_rev = boosted_def_atk_calc / (boosted_att_def_calc * att_hp_calc) if factor_rev > 0 else 0.0
                killed_def_to_att = 4.0 * ratio_rev * factor_rev if factor_rev > 0 else 0.0

            killed_matrix_att_to_def[att_name][def_name] += killed_att_to_def
            killed_matrix_def_to_att[def_name][att_name] += killed_def_to_att
            defender_losses_by_type[def_name] += killed_att_to_def
            attacker_losses_by_type[att_name] += killed_def_to_att
            kills_by_attacker_type[att_name] += killed_att_to_def
            kills_by_defender_type[def_name] += killed_def_to_att
            attacker_losses_by_slot[ai] += killed_def_to_att
            defender_losses_by_slot[di] += killed_att_to_def
            pairwise_exchange_rows.append({
                "AttackerSlot": ai + 1,
                "AttackerTroopType": att_name,
                "DefenderSlot": di + 1,
                "DefenderTroopType": def_name,
                "DefenderLossesFromAttacker": int(killed_att_to_def),
                "AttackerLossesFromDefender": int(killed_def_to_att),
                "AttackerTier": int(A["tier"]),
                "DefenderTier": int(D["tier"]),
                "AtkBaseVsType_AtoD": float(atk_base_vs),
                "DefBaseVsType_AtoD": float(def_base_vs),
                "AtkFormula_AttBuffTerm_AtoD": float(1.0 + (A["base_attack_buff_pp"] / 100.0) + (A["marcher_attack_buff_pp"] / 100.0)),
                "AtkFormula_VsTypeTerm_AtoD": float(1.0 + (A["att_vs_pct"][def_name])),
                "AtkFormula_BaseAtk_AtoD": float(A["base_atk"]),
                "AtkFormula_Step1_AtoD": float(a_step1),
                "AtkFormula_Step2_AtoD": float(a_step2),
                "AtkFormula_Step3_AtoD": float(a_step3),
                "AtkFormula_Step4_Dmg_AtoD": float(a_step4),
                "AtkFormula_Step5_Rng_AtoD": float(a_step5),
                "AtkFormula_Step6_Tier_AtoD": float(a_step6),
                "BoostedAttack_AtoD": float(boosted_att_atk),
                "BoostedDefense_AtoD": float(boosted_def_def),
                "Health_AtoD": float(def_hp),
                "Denominator_AtoD": float(boosted_def_def * def_hp),
                "BoostedAttack_AtoD_UsedInFormula": float(boosted_att_atk_calc),
                "BoostedDefense_AtoD_UsedInFormula": float(boosted_def_def_calc),
                "Health_AtoD_UsedInFormula": float(def_hp_calc),
                "DamageModAtkToDef": float(dmgA),
                "DamageModDefToAtk": float(dmgD),
                "TierModAtkToDef": float(tmodA),
                "TierModDefToAtk": float(tmodD),
                "RangeModAtkToDef": float(rmod),
                "CapacityFactorAtkToDef": float(factor),
                "RatioAtkToDef": float(ratio),
                "KillsFormula_AtoD": float(4.0 * ratio * factor),
                "AtkBaseVsType_DtoA": float(def_atk_base_vs),
                "DefBaseVsType_DtoA": float(att_def_base_vs),
                "AtkFormula_AttBuffTerm_DtoA": float(1.0 + (D["base_attack_buff_pp"] / 100.0) + (D["attack_at_sop_buff_pp"] / 100.0) + (D["defender_attack_buff_pp"] / 100.0)),
                "AtkFormula_VsTypeTerm_DtoA": float(1.0 + (D["att_vs_pct"][att_name])),
                "AtkFormula_BaseAtk_DtoA": float(D["base_atk"]),
                "AtkFormula_Step1_DtoA": float(d_step1),
                "AtkFormula_Step2_DtoA": float(d_step2),
                "AtkFormula_Step3_DtoA": float(d_step3),
                "AtkFormula_Step4_Dmg_DtoA": float(d_step4),
                "AtkFormula_Step5_Rng_DtoA": float(d_step5),
                "AtkFormula_Step6_Tier_DtoA": float(d_step6),
                "BoostedAttack_DtoA": float(boosted_def_atk),
                "BoostedDefense_DtoA": float(boosted_att_def),
                "Health_DtoA": float(att_hp),
                "Denominator_DtoA": float(boosted_att_def * att_hp),
                "BoostedAttack_DtoA_UsedInFormula": float(boosted_def_atk_calc),
                "BoostedDefense_DtoA_UsedInFormula": float(boosted_att_def_calc),
                "Health_DtoA_UsedInFormula": float(att_hp_calc),
                "DamageModDefToAtk_Rev": float(dmgA_rev),
                "DamageModAtkToDef_Rev": float(dmgD_rev),
                "TierModDefToAtk_Rev": float(tmodA_rev),
                "TierModAtkToDef_Rev": float(tmodD_rev),
                "RangeModDefToAtk_Rev": float(rmod_rev),
                "CapacityFactorDefToAtk": float(factor_rev),
                "RatioDefToAtk": float(ratio_rev),
                "KillsFormula_DtoA": float(4.0 * ratio_rev * factor_rev),
            })

    total_defender_losses = sum(defender_losses_by_type.values())
    total_attacker_losses = sum(attacker_losses_by_type.values())
    killed_exchange_rows = []
    for att_type, row in killed_matrix_att_to_def.items():
        for def_type, val in row.items():
            killed_exchange_rows.append({
                "KillerSide": "Attacker",
                "KillerTroopType": att_type,
                "AgainstTroopType": def_type,
                "TroopsKilled": int(val),
            })
    for def_type, row in killed_matrix_def_to_att.items():
        for att_type, val in row.items():
            killed_exchange_rows.append({
                "KillerSide": "Defender",
                "KillerTroopType": def_type,
                "AgainstTroopType": att_type,
                "TroopsKilled": int(val),
            })

    attacker_debug_rows = []
    for i, r in enumerate(attacker_rows, start=1):
        attacker_debug_rows.append({
            "AttackerSlot": i,
            "TroopType": r["type_json"],
            "Tier": int(r["tier"]),
            "MarchSize": int(r["msize"]),
            "BaseAttack": float(r["base_atk"]),
            "AttackMultiplier_(1+BaseAtk+MarcherAtk)": float(r["atk_mul"]),
            "AttackAfterBuffs": float(r["att_base_after_buffs"]),
            "AttackVsInfFactor_(1+vsInf)": float(1.0 + r["att_vs_pct"]["Infantry"]),
            "AttackVsCavFactor_(1+vsCav)": float(1.0 + r["att_vs_pct"]["Cavalry"]),
            "AttackVsRngFactor_(1+vsRng)": float(1.0 + r["att_vs_pct"]["Ranged"]),
            "AttackVsInfRaw": float(r["att_vs"]["Infantry"]),
            "AttackVsCavRaw": float(r["att_vs"]["Cavalry"]),
            "AttackVsRngRaw": float(r["att_vs"]["Ranged"]),
            "BaseDefense": float(r["base_def"]),
            "DefenseMultiplier_(1+BaseDef+MarcherDef)": float(r["att_def_mul"]),
            "DefenseAfterBuffs": float(r["def_base_after_buffs"]),
            "DefenseVsInfFactor_(1+vsInf)": float(1.0 + r["def_vs_pct"]["Infantry"]),
            "DefenseVsCavFactor_(1+vsCav)": float(1.0 + r["def_vs_pct"]["Cavalry"]),
            "DefenseVsRngFactor_(1+vsRng)": float(1.0 + r["def_vs_pct"]["Ranged"]),
            "DefenseVsInfRaw": float(r["def_vs"]["Infantry"]),
            "DefenseVsCavRaw": float(r["def_vs"]["Cavalry"]),
            "DefenseVsRngRaw": float(r["def_vs"]["Ranged"]),
            "BaseHealth": float(r["base_hp"]),
            "HealthMultiplier_(1+BaseHp+MarcherHp)": float(r["hp_mul"]),
            "HealthRaw": float(r["total_hp"]),
        })

    defender_debug_rows = []
    for i, r in enumerate(defender_rows, start=1):
        defender_debug_rows.append({
            "DefenderSlot": i,
            "TroopType": r["type_json"],
            "Tier": int(r["tier"]),
            "MarchSize": int(r["msize"]),
            "BaseAttack": float(r["base_atk"]),
            "AttackMultiplier_(1+BaseAtk+AtkAtSop+DefenderAtk)": float(r["def_atk_mul"]),
            "AttackAfterBuffs": float(r["def_att_base_after_buffs"]),
            "AttackVsInfFactor_(1+vsInf)": float(1.0 + r["att_vs_pct"]["Infantry"]),
            "AttackVsCavFactor_(1+vsCav)": float(1.0 + r["att_vs_pct"]["Cavalry"]),
            "AttackVsRngFactor_(1+vsRng)": float(1.0 + r["att_vs_pct"]["Ranged"]),
            "AttackVsInfRaw": float(r["att_vs"]["Infantry"]),
            "AttackVsCavRaw": float(r["att_vs"]["Cavalry"]),
            "AttackVsRngRaw": float(r["att_vs"]["Ranged"]),
            "BaseDefense": float(r["base_def"]),
            "DefenseMultiplier_(1+BaseDef+DefAtSop+DefenderDef)": float(r["def_mul"]),
            "DefenseAfterBuffs": float(r["def_base_after_buffs"]),
            "DefenseVsInfFactor_(1+vsInf)": float(1.0 + r["def_vs_pct"]["Infantry"]),
            "DefenseVsCavFactor_(1+vsCav)": float(1.0 + r["def_vs_pct"]["Cavalry"]),
            "DefenseVsRngFactor_(1+vsRng)": float(1.0 + r["def_vs_pct"]["Ranged"]),
            "DefenseVsInfRaw": float(r["def_vs"]["Infantry"]),
            "DefenseVsCavRaw": float(r["def_vs"]["Cavalry"]),
            "DefenseVsRngRaw": float(r["def_vs"]["Ranged"]),
            "BaseHealth": float(r["base_hp"]),
            "HealthMultiplier_(1+BaseHp+HpAtSop+DefenderHp)": float(r["hp_mul"]),
            "HealthRaw": float(r["total_hp"]),
        })

    return {
        "scenario": scenario,

        "attackers": [
            {
                "TroopType": r["type_json"],
                "Tier": r["tier"],
                "MarchSize": r["msize"],
                "Att_vs_Inf": r["att_vs"]["Infantry"],
                "Att_vs_Cav": r["att_vs"]["Cavalry"],
                "Att_vs_Ranged": r["att_vs"]["Ranged"],
            }
            for r in attacker_rows
        ],
        "defenders": [
            {
                "TroopType": r["type_json"],
                "Tier": r["tier"],
                "MarchSize": r["msize"],
                "TotalHealth": r["total_hp"],
                "TotalDef_vs_Inf": r["totaldef_vs"]["Infantry"],
                "TotalDef_vs_Cav": r["totaldef_vs"]["Cavalry"],
                "TotalDef_vs_Ranged": r["totaldef_vs"]["Ranged"],
            }
            for r in defender_rows
        ],

        "killed_matrix": {a: {d: int(v) for d, v in row.items()} for a, row in killed_matrix_att_to_def.items()},
        "killed_matrix_attacker_to_defender": {
            a: {d: int(v) for d, v in row.items()} for a, row in killed_matrix_att_to_def.items()
        },
        "killed_matrix_defender_to_attacker": {
            d: {a: int(v) for a, v in row.items()} for d, row in killed_matrix_def_to_att.items()
        },
        "killed_by_defender_type": {k: int(v) for k, v in defender_losses_by_type.items()},
        "killed_by_attacker_type": {k: int(v) for k, v in kills_by_attacker_type.items()},
        "attacker_losses_by_type": {k: int(v) for k, v in attacker_losses_by_type.items()},
        "defender_losses_by_type": {k: int(v) for k, v in defender_losses_by_type.items()},
        "kills_by_defender_type": {k: int(v) for k, v in kills_by_defender_type.items()},
        "attacker_losses_total": int(total_attacker_losses),
        "defender_losses_total": int(total_defender_losses),
        "attacker_losses_by_slot": [int(v) for v in attacker_losses_by_slot],
        "defender_losses_by_slot": [int(v) for v in defender_losses_by_slot],
        "pairwise_exchange_rows": pairwise_exchange_rows,
        "attacker_debug_rows": attacker_debug_rows,
        "defender_debug_rows": defender_debug_rows,
        "killed_total": int(total_defender_losses),
        "killed_exchange_rows": killed_exchange_rows,
    }


compute_battle_like_sheet = compute_battle_outcome


def statsCalculator(atkbuff, marcheratkbuff, atkvscav, atkvsinf, atkvsrng, defbuff, healthbuff, defatsopbuff, healthatsopbuff, defvscav, defvsinf, defvsrng, defenderdefensebuff, defenderhealthbuff):
    totalatkvscav = ((1 + atkbuff/100 + marcheratkbuff/100) * (1 + atkvscav/100)) - 1
    totalatkvsinf = ((1 + atkbuff/100 + marcheratkbuff/100) * (1 + atkvsinf/100)) - 1
    totalatkvsrng = ((1 + atkbuff/100 + marcheratkbuff/100) * (1 + atkvsrng/100)) - 1

    totalhealth = (1 + healthbuff/100 + defenderhealthbuff/100 + healthatsopbuff/100) - 1
    totaldefvscav = ((1 + defbuff/100 + defenderdefensebuff/100 + defatsopbuff/100) * (1 + defvscav/100)) - 1
    totaldefvsinf = ((1 + defbuff/100 + defenderdefensebuff/100 + defatsopbuff/100) * (1 + defvsinf/100)) - 1
    totaldefvsrng = ((1 + defbuff/100 + defenderdefensebuff/100 + defatsopbuff/100) * (1 + defvsrng/100)) - 1

    r = lambda x: round(x, 2)

    return {
        "Total Attack vs Cavalry": r(totalatkvscav),
        "Total Attack vs Infantry": r(totalatkvsinf),
        "Total Attack vs Ranged": r(totalatkvsrng),
        "Total Health": r(totalhealth),
        "Total Defense vs Cavalry": r(totaldefvscav),
        "Total Defense vs Infantry": r(totaldefvsinf),
        "Total Defense vs Ranged": r(totaldefvsrng),
    }

def statsComparator(troop_type_json: str, attacker: dict, defender: dict) -> dict:


    def g(d: dict, key: str) -> float:
        return float(d.get(key, 0.0))

    def pctdiff(x: float, ref: float) -> str:
        if ref == 0:
            return "0.00%"
        return f"{((x - ref) / ref) * 100:.2f}%"

    maxed_all = load_maxedStats()
    if not maxed_all:
        raise RuntimeError("MaxedStats.json did not load (empty dict).")
    if troop_type_json not in maxed_all:
        raise KeyError(f"MaxedStats missing troop type '{troop_type_json}'.")

    maxed_entry = maxed_all[troop_type_json]
    max_atk = getattr(maxed_entry, "attack", None)
    max_def = getattr(maxed_entry, "defense", None)

    if not isinstance(max_atk, dict) or not isinstance(max_def, dict):
        raise TypeError("MaxedStats structure unexpected: expected Attack/Defense dict blocks.")

    attacker_totals = statsCalculator(
        g(attacker, "baseatkbuff"),
        g(attacker, "marcheratkbuff"),
        g(attacker, "atkvscav"),
        g(attacker, "atkvsinf"),
        g(attacker, "atkvsrng"),
        0.0,   # defbuff
        0.0,   # healthbuff
        0.0,   # defatsopbuff
        0.0,   # healthatsopbuff
        0.0,   # defvscav
        0.0,   # defvsinf
        0.0,   # defvsrng
        0.0,   # defenderdefensebuff
        0.0,   # defenderhealthbuff
    )

    # ---- Player defender totals (attacker-only fields = 0) ----
    defender_totals = statsCalculator(
        0.0,   # atkbuff
        0.0,   # marcheratkbuff
        0.0,   # atkvscav
        0.0,   # atkvsinf
        0.0,   # atkvsrng
        g(defender, "basedefbuff"),
        g(defender, "basehealthbuff"),
        g(defender, "defatsopbuff"),
        g(defender, "healthatsopbuff"),
        g(defender, "defvscav"),
        g(defender, "defvsinf"),
        g(defender, "defvsrng"),
        g(defender, "defdefensebuff"),
        g(defender, "defhealthbuff"),
    )

    # ---- Maxed attacker totals (defender-only fields = 0) ----
    maxed_attacker_totals = statsCalculator(
        float(max_atk.get("Attack", 0.0)),
        float(max_atk.get("MarcherAttack", 0.0)),
        float(max_atk.get("vsCav", 0.0)),
        float(max_atk.get("vsInf", 0.0)),
        float(max_atk.get("vsRanged", 0.0)),
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    )

    # ---- Maxed defender totals (attacker-only fields = 0) ----
    maxed_defender_totals = statsCalculator(
        0.0, 0.0, 0.0, 0.0, 0.0,
        float(max_def.get("Defense", 0.0)),
        float(max_def.get("Health", 0.0)),
        float(max_def.get("DefenseAtSop", 0.0)),
        float(max_def.get("HealthAtSop", 0.0)),
        float(max_def.get("vsCav", 0.0)),
        float(max_def.get("vsInf", 0.0)),
        float(max_def.get("vsRanged", 0.0)),
        float(max_def.get("DefenderDefense", 0.0)),
        float(max_def.get("DefenderHealth", 0.0)),
    )

    # Attacker preset compares attack totals only
    attacker_keys = [
        "Total Attack vs Cavalry",
        "Total Attack vs Infantry",
        "Total Attack vs Ranged",
    ]

    # Defender preset compares health + defense totals
    defender_keys = [
        "Total Health",
        "Total Defense vs Cavalry",
        "Total Defense vs Infantry",
        "Total Defense vs Ranged",
    ]

    attacker_comp = {}
    for k in attacker_keys:
        attacker_comp[k] = {
            "player": attacker_totals[k],
            "maxed": maxed_attacker_totals[k],
            "diff_pct": pctdiff(float(attacker_totals[k]), float(maxed_attacker_totals[k])),
        }

    defender_comp = {}
    for k in defender_keys:
        defender_comp[k] = {
            "player": defender_totals[k],
            "maxed": maxed_defender_totals[k],
            "diff_pct": pctdiff(float(defender_totals[k]), float(maxed_defender_totals[k])),
        }

    return {
        "troop_type": troop_type_json,

        "attacker_true_power": attacker_totals,
        "defender_true_power": defender_totals,

        "maxed_attacker_true_power": maxed_attacker_totals,
        "maxed_defender_true_power": maxed_defender_totals,

        "comparison": {
            "attacker_vs_maxed": attacker_comp,
            "defender_vs_maxed": defender_comp,
        },
    }


def dvdcalc_duel(attacker: DragonInfo, defender: DragonInfo):

    dragons = load_dragonBaseData()

    if attacker.level not in dragons:
        raise KeyError(f"Attacker dragon level {attacker.level} not found.")
    if defender.level not in dragons:
        raise KeyError(f"Defender dragon level {defender.level} not found.")

    A = dragons[attacker.level]
    B = dragons[defender.level]

    A_atk_total = A.base_dvd_attack * (1.0 + attacker.atkbuff / 100.0)
    B_def_total = B.base_dvd_defense * (1.0 + defender.defbuff / 100.0)
    B_hp_total  = B.base_health      * (1.0 + defender.healthbuff / 100.0)

    raw_dmg = A_atk_total / B_def_total
    percent_dmg = raw_dmg / B_hp_total

    heal_mult = B.healing_multiplier
    heal_exp  = B.healing_exponent

    if defender.regenrate <= 0:
        raise ValueError("defender.regenrate must be > 0")

    total_gold_full = heal_mult * (B_hp_total / defender.regenrate) ** heal_exp

    return {
        "raw_damage": int(raw_dmg),                          
        "percent_damage": f"{percent_dmg * 100:.2f}%",      
        "total_gold": int(total_gold_full),                  
    }
