# models.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping




class TroopType(str, Enum):
    INFANTRY = "inf"
    RANGED = "rng"
    CAVALRY = "cav"


def _to_int(x: Any, *, default: int = 0) -> int:
    if x is None:
        return default
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x)
    s = str(x).strip()
    if s == "":
        return default
    return int(float(s.replace(",", ".")))


def _to_float(x: Any, *, default: float = 0.0) -> float:
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "":
        return default
    return float(s.replace(",", "."))


def _to_percent_points(x: Any, *, default: float = 0.0) -> float:
    """
    Always returns percentage points.
    Examples:
      50      -> 50.0
      "50"    -> 50.0
      "50%"   -> 50.0
      0.5     -> 0.5   (still treated as 0.5 percentage points, not 50%)
    """
    if x is None:
        return default
    if isinstance(x, str):
        s = x.strip()
        if s.endswith("%"):
            s = s[:-1].strip()
        return _to_float(s, default=default)
    return _to_float(x, default=default)


@dataclass(frozen=True, slots=True)
class PlayerInfo:
    tier: int
    troop_type: TroopType
    role: str  # "attacker" or "defender"

    def __post_init__(self):
        r = self.role.lower().strip()
        if r not in ("attacker", "defender"):
            raise ValueError("role must be 'attacker' or 'defender'")
        object.__setattr__(self, "role", r)

    # Shared (both roles can have these vs-type buffs)
    atkvscav: float = 0.0
    atkvsinf: float = 0.0
    atkvsrng: float = 0.0
    defvscav: float = 0.0
    defvsinf: float = 0.0
    defvsrng: float = 0.0

    # Attack-side role-specific
    baseatkbuff: float = 0.0
    marcheratkbuff: float = 0.0        # attacker only
    atkatsopbuff: float = 0.0          # defender only
    defenderatkbuff: float = 0.0       # defender only

    # Defense-side role-specific
    basedefbuff: float = 0.0
    marcherdefbuff: float = 0.0        # attacker only
    defatsopbuff: float = 0.0          # defender only
    defenderdefbuff: float = 0.0       # defender only (your “defenderdefbuff”)

    # Health-side role-specific
    basehealthbuff: float = 0.0
    marcherhealthbuff: float = 0.0     # attacker only
    defenderhealthbuff: float = 0.0    # defender only
    healthatsopbuff: float = 0.0       # defender only

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "PlayerInfo":
        return PlayerInfo(
            tier=_to_int(d.get("tier"), default=1),
            troop_type=TroopType(str(d.get("type", "inf")).lower()),
            role=str(d.get("role", "attacker")).lower().strip(),  # "attacker" or "defender"

            # Shared vs-type buffs (same names regardless of role)
            atkvscav=_to_percent_points(d.get("atkvscav")),
            atkvsinf=_to_percent_points(d.get("atkvsinf")),
            atkvsrng=_to_percent_points(d.get("atkvsrng")),
            defvscav=_to_percent_points(d.get("defvscav")),
            defvsinf=_to_percent_points(d.get("defvsinf")),
            defvsrng=_to_percent_points(d.get("defvsrng")),

            # Shared base buffs (exist in both roles)
            baseatkbuff=_to_percent_points(d.get("baseatkbuff")),
            basedefbuff=_to_percent_points(d.get("basedefbuff")),
            basehealthbuff=_to_percent_points(d.get("basehealthbuff")),

            # Attacker-only
            marcheratkbuff=_to_percent_points(d.get("marcheratkbuff")),
            marcherdefbuff=_to_percent_points(d.get("marcherdefbuff")),
            marcherhealthbuff=_to_percent_points(d.get("marcherhealthbuff")),

            # Defender-only
            atkatsopbuff=_to_percent_points(d.get("atkatsopbuff")),
            defenderatkbuff=_to_percent_points(d.get("defenderatkbuff")),
            defatsopbuff=_to_percent_points(d.get("defatsopbuff")),
            defenderdefbuff=_to_percent_points(d.get("defenderdefbuff")),
            defenderhealthbuff=_to_percent_points(d.get("defenderhealthbuff")),
            healthatsopbuff=_to_percent_points(d.get("healthatsopbuff")),
        )


@dataclass(frozen=True, slots=True)
class DragonInfo:
    level: int

    # Buffs stored as percentage points
    atkbuff: float = 0.0
    defbuff: float = 0.0
    healthbuff: float = 0.0

    # Flat number
    regenrate: float = 0.0

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "DragonInfo":
        return DragonInfo(
            level=_to_int(d.get("level"), default=1),
            atkbuff=_to_percent_points(d.get("atkbuff")),
            defbuff=_to_percent_points(d.get("defbuff")),
            healthbuff=_to_percent_points(d.get("healthbuff")),
            regenrate=_to_float(d.get("regenrate"), default=0.0),
        )

@dataclass(frozen=True, slots=True)
class attackBattleStats:
    TroopType: TroopType
    TroopTier: int = 0
    baseAttackBuff: float = 0.0
    marcherAttackBuff: float = 0.0
    baseDefenseBuff: float = 0.0
    marcherDefenseBuff: float = 0.0
    baseHealthBuff: float = 0.0
    marcherHealthBuff: float = 0.0
    attvscav: float = 0.0
    attvsinf: float = 0.0
    attvsrng: float = 0.0
    defvscav: float = 0.0
    defvsinf: float = 0.0
    defvsrng: float = 0.0
    msizeAtt: int = 0

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "attackBattleStats":
        return attackBattleStats(
            TroopType=TroopType(str(d.get("TroopType")).lower()),
            TroopTier=_to_int(d.get("TroopTier"), default=1),
            msizeAtt=_to_int(d.get("msizeAtt"), default=1),
            baseAttackBuff=_to_percent_points(d.get("baseAttackBuff")),
            marcherAttackBuff=_to_percent_points(d.get("marcherAttackBuff")),
            baseDefenseBuff=_to_percent_points(d.get("baseDefenseBuff")),
            marcherDefenseBuff=_to_percent_points(d.get("marcherDefenseBuff")),
            baseHealthBuff=_to_percent_points(d.get("baseHealthBuff")),
            marcherHealthBuff=_to_percent_points(d.get("marcherHealthBuff")),
            attvscav=_to_percent_points(d.get("attvscav")),
            attvsinf=_to_percent_points(d.get("attvsinf")),
            attvsrng=_to_percent_points(d.get("attvsrng")),
            defvscav=_to_percent_points(d.get("defvscav")),
            defvsinf=_to_percent_points(d.get("defvsinf")),
            defvsrng=_to_percent_points(d.get("defvsrng")),
        )

@dataclass(frozen=True, slots=True)
class defenseBattleStats:
    TroopType: TroopType
    TroopTier: int = 0
    msizeDef: int = 0
    baseAttackBuff: float = 0.0
    attackatsopBuff: float = 0.0
    defenderattackbuff: float = 0.0
    baseDefenseBuff: float = 0.0
    baseHealthBuff: float = 0.0
    defenseatsopBuff: float = 0.0
    healthatsopBuff: float = 0.0
    attvscav: float = 0.0
    attvsinf: float = 0.0
    attvsrng: float = 0.0
    defvscav: float = 0.0
    defvsinf: float = 0.0
    defvsrng: float = 0.0
    defenderdefensebuff: float = 0.0
    defenderhealthbuff: float = 0.0

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "defenseBattleStats":
        return defenseBattleStats(
            TroopType=TroopType(str(d.get("TroopType")).lower()),
            TroopTier=_to_int(d.get("TroopTier"), default=1),
            msizeDef=_to_int(d.get("msizeDef"), default=1),
            baseAttackBuff=_to_percent_points(d.get("baseAttackBuff")),
            attackatsopBuff=_to_percent_points(d.get("attackatsopBuff")),
            defenderattackbuff=_to_percent_points(d.get("defenderattackbuff")),
            baseDefenseBuff=_to_percent_points(d.get("baseDefenseBuff")),
            baseHealthBuff=_to_percent_points(d.get("baseHealthBuff")),
            attvscav=_to_percent_points(d.get("attvscav")),
            attvsinf=_to_percent_points(d.get("attvsinf")),
            attvsrng=_to_percent_points(d.get("attvsrng")),
            defvscav=_to_percent_points(d.get("defvscav")),
            defvsinf=_to_percent_points(d.get("defvsinf")),
            defvsrng=_to_percent_points(d.get("defvsrng")),
            defenseatsopBuff=_to_percent_points(d.get("defenseatsopBuff")),
            healthatsopBuff=_to_percent_points(d.get("healthatsopBuff")),
            defenderdefensebuff=_to_percent_points(d.get("defenderdefensebuff")),
            defenderhealthbuff=_to_percent_points(d.get("defenderhealthbuff")),
        )
    
@dataclass(frozen=True, slots=True)
class siege:
    tier: int = 0
    msize: int = 0
    wdb: float = 0
    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "siege":
        return siege(
            tier = _to_int(d.get("tier"), default=1),
            msize = _to_int(d.get("msize"), default=1),
            wdb = _to_percent_points(d.get("wdb"))
        )

