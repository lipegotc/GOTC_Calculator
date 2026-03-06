import json
from pathlib import Path


_DATA_DIR = Path(__file__).resolve().parent / "data"


def _open_data_file(filename: str):
    return (_DATA_DIR / filename).open("r", encoding="utf-8")

def load_troopBaseData():
    try:
        with _open_data_file("TroopBaseStats.json") as file:
            raw = json.load(file)

        troops = {}
        for troop_id, stats in raw.items():
            troops[troop_id] = StatObject(stats)

        return troops

    except FileNotFoundError:
        print("Error: The file 'TroopBaseStats.json' was not found.")
        return {}

def load_dragonBaseData():
    try:
        with _open_data_file("DragonTableData.json") as file:
            raw = json.load(file)

        # Expecting a list of dict rows
        if not isinstance(raw, list):
            raise TypeError(f"DragonTableData.json must be a list of rows, got {type(raw)}")

        by_level = {}
        for row in raw:
            if not isinstance(row, dict):
                continue

            lvl = row.get("Level")
            if lvl is None:
                continue

            try:
                lvl = int(lvl)
            except (ValueError, TypeError):
                continue

            by_level[lvl] = StatObject(row)

        return by_level

    except FileNotFoundError:
        print("Error: The file 'DragonTableData.json' was not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. Details: {e}")
        return {}
    except TypeError as e:
        print(f"Error: {e}")
        return {}

def load_damageModifiers():
    try:
        with _open_data_file("DamageModifiers.json") as file:
            raw = json.load(file)

        mods = raw.get("Modifiers")
        if not isinstance(mods, dict):
            raise TypeError("DamageModifiers.json must contain top-level key 'Modifiers' as an object.")

        return mods

    except FileNotFoundError:
        print("Error: The file 'DamageModifiers.json' was not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. Details: {e}")
        return {}
    except TypeError as e:
        print(f"Error: {e}")
        return {}

def load_siegestats():
    try:
        with _open_data_file("siegestats.json") as file:
            raw = json.load(file)
        by_tier = {}
        for row in raw:
            if not isinstance(row, dict):
                continue

            tier = row.get("Tier")
            if tier is None:
                continue

            try:
                tier = int(tier)
            except (ValueError, TypeError):
                continue

            by_tier[tier] = StatObject(row)

        return by_tier

        
    except FileNotFoundError:
        print("Error: The file 'siegestats.json' was not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. Details: {e}")
        return {}
    except TypeError as e:
        print(f"Error: {e}")
        return {}

def load_sophealth():
    try:
        with _open_data_file("sop_wallhealth.json") as file:
            raw = json.load(file)
        by_star = {}
        for row in raw:
            if not isinstance(row, dict):
                continue

            star = row.get("Stars")
            if star is None:
                continue

            by_star[star] = StatObject(row)

        return by_star
        
    except FileNotFoundError:
        print("Error: The file 'sop_wallhealth.json' was not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. Details: {e}")
        return {}
    except TypeError as e:
        print(f"Error: {e}")
        return {}

def load_maxedStats():
    try:
        with _open_data_file("MaxedStats.json") as file:
            raw = json.load(file)

        maxed = raw.get("MaxedStats")
        if not isinstance(maxed, dict):
            raise TypeError("MaxedStats.json must contain top-level key 'MaxedStats' as an object.")

        result = {}
        for troop_type, stats in maxed.items():
            result[troop_type] = StatObject(stats)

        return result

    except FileNotFoundError:
        print("Error: The file 'MaxedStats.json' was not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from the file. Details: {e}")
        return {}
    except TypeError as e:
        print(f"Error: {e}")
        return {}

class StatObject:
    def __init__(self, d):
        for k, v in d.items():
            key = k.lower().replace(" ", "_")
            if isinstance(v, str):
                try:
                    v2 = float(v)
                    v = int(v2) if v2.is_integer() else v2
                except ValueError:
                    pass
            setattr(self, key, v)

    def __repr__(self):
        return str(self.__dict__)
