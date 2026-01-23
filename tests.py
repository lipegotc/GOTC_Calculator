# test_all.py
# Usage: python test_all.py
#
# This file runs:
#   1) a PlayerInfo attacker output test
#   2) a PlayerInfo defender output test
#   3) a DragonInfo duel test (P1->P2 and P2->P1)
#
# Adjust tiers/types/levels if your JSON does not contain those keys.

from models import PlayerInfo, DragonInfo, TroopType
from calculator import compute_player_outputs, dvdcalc_duel


def print_player(label, out):
    print(f"=== {label} ===")
    print("Role:", out["role"])
    print("Troop:", out["troop_key"], "| Tier:", out["tier"], "| Type:", out["troop_type"])
    print("Base:", "ATK", out["base_atk"], "DEF", out["base_def"], "HP", out["base_hp"])
    print("Total HP:", out["total_hp"])
    print("ATK vs INF/RNG/CAV:", out["atk_vs_inf"], out["atk_vs_rng"], out["atk_vs_cav"])
    print("DEF vs INF/RNG/CAV:", out["def_vs_inf"], out["def_vs_rng"], out["def_vs_cav"])
    print("DMG Mods:", out["damage_modifiers"])
    print()


def print_dragon(label, out):
    print(f"=== {label} ===")
    print("Raw damage:", out["raw_damage"])
    print("Percent damage:", out["percent_damage"])
    print("Gold per hit:", out["gold_per_hit"])
    print("Total gold:", out["total_gold"])
    print()


def main():
    # ---- Player tests ----
    # Attacker: baseatkbuff + marcheratkbuff, basedefbuff + marcherdefbuff, basehealthbuff + marcherhealthbuff
    p1 = PlayerInfo(
        tier=12,
        troop_type=TroopType.INFANTRY,
        role="attacker",

        baseatkbuff=5000,
        marcheratkbuff=3000,
        atkvsrng=500,
        atkvscav=1400,
        atkvsinf=1000,

        basedefbuff=1000,
        marcherdefbuff=2000,
        defvsinf=500,
        defvscav=800,
        defvsrng=400,

        basehealthbuff=500,
        marcherhealthbuff=2000,
    )

    # Defender: baseatkbuff + atkatsopbuff, basedefbuff + defatsopbuff + defenderdefbuff,
    #           basehealthbuff + defenderhealthbuff + healthatsopbuff
    p2 = PlayerInfo(
        tier=12,
        troop_type=TroopType.CAVALRY,
        role="defender",

        baseatkbuff=1000,
        atkatsopbuff=1500,
        defenderatkbuff=50,
        atkvsinf=400,
        atkvscav=600,
        atkvsrng=900,

        basedefbuff=1000,
        defatsopbuff=2000,
        defenderdefbuff=100,
        defvsrng=800,
        defvscav=500,
        defvsinf=400,

        basehealthbuff=500,
        defenderhealthbuff=80,
        healthatsopbuff=2500,
    )

    out1 = compute_player_outputs(p1)
    out2 = compute_player_outputs(p2)

    print_player("Player 1 (Attacker preset)", out1)
    print_player("Player 2 (Defender preset)", out2)

    # ---- Dragon duel tests ----
    d1 = DragonInfo(level=69, atkbuff=1000.0, defbuff=700.0, healthbuff=350.0, regenrate=15.0)
    d2 = DragonInfo(level=69, atkbuff=900.0, defbuff=500.0, healthbuff=300.0, regenrate=14.0)

    r12 = dvdcalc_duel(d1, d2)
    r21 = dvdcalc_duel(d2, d1)

    print_dragon("Dragon P1 -> P2", r12)
    print_dragon("Dragon P2 -> P1", r21)


if __name__ == "__main__":
    main()
