from __future__ import annotations
from typing import Any
from models import PlayerInfo, DragonInfo, TroopType
from data import load_troopBaseData, load_dragonBaseData, load_damageModifiers


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

def compute_player_outputs(player: PlayerInfo):
    """
    Produces per-player derived stats table (not a battle).

    - Applies correct buff set based on player.role: 'attacker' or 'defender'
    - Applies DamageModifiers multiplicatively to each vs-target result
    - Returns presentation-ready ints (truncated), plus the used modifiers
    """
    role = str(player.role).lower().strip()
    if role not in ("attacker", "defender"):
        raise ValueError("player.role must be 'attacker' or 'defender'")

    tt = _normalize_troop_type(player.troop_type)

    troops = load_troopBaseData()
    mods = load_damageModifiers()

    if not troops:
        raise RuntimeError("TroopBaseStats.json did not load (empty dict).")
    if not mods:
        raise RuntimeError("DamageModifiers.json did not load (empty dict).")

    tier_key = f"T{player.tier}"
    if tier_key not in mods:
        raise KeyError(f"Tier '{tier_key}' not found in DamageModifiers.json (Modifiers).")

    player_type_json = _TROOPTYPE_TO_JSON[tt]
    if player_type_json not in mods[tier_key]:
        raise KeyError(f"Troop type '{player_type_json}' not found under Modifiers['{tier_key}'].")

    troop_key = f"{_TROOPTYPE_TO_TROOPKEY_PREFIX[tt]}_{player.tier}"
    if troop_key not in troops:
        raise KeyError(f"Troop '{troop_key}' not found in TroopBaseStats.json.")

    troop = troops[troop_key]

    # Base troop stats
    base_atk = float(getattr(troop, "attack"))
    base_def = float(getattr(troop, "defense"))
    base_hp = float(getattr(troop, "health"))

    # Damage modifiers (tier + own type -> enemy type)
    tier_mods = mods[tier_key][player_type_json]
    try:
        m_vs_inf = float(tier_mods["Infantry"])
        m_vs_rng = float(tier_mods["Ranged"])
        m_vs_cav = float(tier_mods["Cavalry"])
    except KeyError as e:
        raise KeyError(f"Missing modifier key in DamageModifiers.json: {e}. Expected Infantry/Ranged/Cavalry.")

    # Shared vs-type buffs (percent points -> fraction)
    atkvsinf = player.atkvsinf / 100.0
    atkvsrng = player.atkvsrng / 100.0
    atkvscav = player.atkvscav / 100.0

    defvsinf = player.defvsinf / 100.0
    defvsrng = player.defvsrng / 100.0
    defvscav = player.defvscav / 100.0

    # Role-specific base multipliers (percent points -> fraction)
    if role == "attacker":
        atk_base_mul = 1.0 + (player.baseatkbuff / 100.0) + (player.marcheratkbuff / 100.0)
        def_base_mul = 1.0 + (player.basedefbuff / 100.0) + (player.marcherdefbuff / 100.0)
        hp_mul = 1.0 + (player.basehealthbuff / 100.0) + (player.marcherhealthbuff / 100.0)
    else:
        atk_base_mul = 1.0 + (player.baseatkbuff / 100.0) + (player.atkatsopbuff / 100.0) + (player.defenderatkbuff / 100.0)
        def_base_mul = 1.0 + (player.basedefbuff / 100.0) + (player.defatsopbuff / 100.0) + (player.defenderdefbuff / 100.0)
        hp_mul = 1.0 + (player.basehealthbuff / 100.0) + (player.defenderhealthbuff / 100.0) + (player.healthatsopbuff / 100.0)

    total_hp = base_hp * hp_mul

    # Attack totals (apply vs buffs and damage mods multiplicatively)
    atk_vs_inf = base_atk * atk_base_mul * (1.0 + atkvsinf) * m_vs_inf
    atk_vs_rng = base_atk * atk_base_mul * (1.0 + atkvsrng) * m_vs_rng
    atk_vs_cav = base_atk * atk_base_mul * (1.0 + atkvscav) * m_vs_cav

    # Defense totals (your current proxy metric; keep as-is)
    def_vs_inf = (total_hp * (base_def * def_base_mul * (1.0 + defvsinf))) * m_vs_inf
    def_vs_rng = (total_hp * (base_def * def_base_mul * (1.0 + defvsrng))) * m_vs_rng
    def_vs_cav = (total_hp * (base_def * def_base_mul * (1.0 + defvscav))) * m_vs_cav

    return {
        "role": role,
        "troop_key": troop_key,
        "tier": player.tier,
        "troop_type": player_type_json,

        "base_atk": int(base_atk),
        "base_def": int(base_def),
        "base_hp": int(base_hp),

        "total_hp": int(total_hp),

        "atk_vs_inf": int(atk_vs_inf),
        "atk_vs_rng": int(atk_vs_rng),
        "atk_vs_cav": int(atk_vs_cav),

        "def_vs_inf": int(def_vs_inf),
        "def_vs_rng": int(def_vs_rng),
        "def_vs_cav": int(def_vs_cav),

        "damage_modifiers": {
            "vs_inf": m_vs_inf,
            "vs_rng": m_vs_rng,
            "vs_cav": m_vs_cav,
        },
    }

def dvdcalc_duel(attacker: DragonInfo, defender: DragonInfo):
    """
    Dragon duel calculation: attacker -> defender

    Rules:
    - Buffs are percentage points (e.g., 1500 = 1500%)
    - regenrate is flat
    - Healing cost is based on the DEFENDER (the one taking damage)
    - Output is presentation-ready:
        * raw damage: integer part
        * percent damage: 'X.XX%'
        * gold values: integer part
    """

    dragons = load_dragonBaseData()

    if attacker.level not in dragons:
        raise KeyError(f"Attacker dragon level {attacker.level} not found.")
    if defender.level not in dragons:
        raise KeyError(f"Defender dragon level {defender.level} not found.")

    A = dragons[attacker.level]
    B = dragons[defender.level]

    # Apply buffs (percentage points → multipliers)
    A_atk_total = A.base_dvd_attack * (1.0 + attacker.atkbuff / 100.0)
    B_def_total = B.base_dvd_defense * (1.0 + defender.defbuff / 100.0)
    B_hp_total  = B.base_health      * (1.0 + defender.healthbuff / 100.0)

    # Core damage math (A -> B)
    raw_dmg = A_atk_total / B_def_total
    percent_dmg = raw_dmg / B_hp_total

    # Healing economics (defender side)
    heal_mult = B.healing_multiplier
    heal_exp  = B.healing_exponent

    if defender.regenrate <= 0:
        raise ValueError("defender.regenrate must be > 0")

    gold_per_hit = heal_mult * (raw_dmg / defender.regenrate) ** heal_exp
    total_gold_full = heal_mult * (B_hp_total / defender.regenrate) ** heal_exp

    # === PRESENTATION NORMALIZATION ===
    return {
        "raw_damage": int(raw_dmg),                          # truncate
        "percent_damage": f"{percent_dmg * 100:.2f}%",      # formatted %
        "gold_per_hit": int(gold_per_hit),                   # truncate
        "total_gold": int(total_gold_full),                  # truncate
    }