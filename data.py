import json

def load_troopBaseData():
    try:
        with open(r'data\TroopBaseStats.json', 'r') as file:
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
        with open(r"data\DragonTableData.json", "r", encoding="utf-8") as file:
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

            # normalize level key to int
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
        with open(r"data\DamageModifiers.json", "r", encoding="utf-8") as file:
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


class StatObject:
    def __init__(self, d):
        for k, v in d.items():
            key = k.lower().replace(" ", "_")
            # best-effort numeric coercion
            if isinstance(v, str):
                try:
                    v2 = float(v)
                    v = int(v2) if v2.is_integer() else v2
                except ValueError:
                    pass
            setattr(self, key, v)

    def __repr__(self):
        return str(self.__dict__)
