# Native Dependencies
import os.path
import json
from operator import attrgetter

# External Dependencies
import dcs

# Internal Dependencies
from unit_map import UnitMap, Faction, Nation, Formation


class MizFormation:
    def __init__(self, name:str, tags:list, faction:UnitMap.Faction, nation:UnitMap.Nation, formation:UnitMap.Formation):
        self.name = name
        self.tags = tags
        self.faction = faction
        self.nation = nation
        self.formation = formation


def formations_from_miz(miz:dcs.Mission, unit_map:UnitMap):
    drawings = miz.drawings.get_layer_by_name(unit_map.miz_drawing_layer)

    formations = {}
    for obj in drawings.objects:
        if "_label" in obj.name:
            continue  # reject specific objects

        if obj.name in formations:
            continue  # reject duplicates

        name = obj.name
        tags = name.split("-")[1:]  # NOTE:  assuming no whitespace
        if len(tags) == 0:
            print(f"WARN:  tagless object [{name}]")  # TODO:  logging
            continue  # reject tagless item

        faction = None
        nation = None
        formation = None

        # Resolve Faction and Nation
        for tag in tags:
            # Match faction tag
            if faction is None:
                if tag in unit_map.factions.keys():
                    faction = unit_map.factions.get(tag)
                    continue  # next tag

            # Match nation tag
            if nation is None:
                if faction is not None:  # easy case first
                    if tag in faction.nations.keys():
                        nation = faction.nations.get(tag)
                        continue  # next tag
                else:
                    for _, f in unit_map.factions.items():
                        if tag in f.nations.keys():
                            faction = f
                            nation = faction.nations.get(tag)
        
        if faction is None:
            print(f"WARN:  invalid formation {name}")
            continue
        else:
            if nation is None:
                nation = faction.get("Default", None)

        if (faction is not None) and (nation is not None):
            for tag in tags:
                if tag in nation.formations.keys():
                    if formation is not None:
                        print(f"WARN:  multiple formation tags [{name}]")
                    else:
                        formation = nation.formations.get(tag)

        if formation is None:
            print(f"WARN:  invalid formation {name}")
        else:
            formations[name] = MizFormation(name, tags, faction, nation, formation)

    return formations


if __name__ == "__main__":
    target_file = "UTNS_ Uprising PRACTICE_fo_export (1).miz"  # TODO:  Add input argument
    unit_map_file = "unit_map.json"    # TODO: Add input argument
    output_file = "{0}_{1}.miz".format(os.path.splitext(target_file)[0], "fo2szpu")  # TODO: Add input argument with default as {target_file}_fo2szpu.miz
    print(f"INFO [fo2szpu]:  Configuration:  target_file= {target_file} | unit_map= {unit_map_file} | output_file={output_file}")  # TODO:  add logging


    unit_map = UnitMap.from_json(unit_map_file)

    miz = dcs.Mission(terrain=dcs.terrain.Kola())
    miz.load_file(target_file)
    print("INFO [fo2szpu]:  Mission Loaded")  # TODO:  add logging
    
    formations = formations_from_miz(miz, unit_map)
    print(f"INFO [fo2szpu]:  formations detected = {len(formations.keys())}")

    print(f"INFO [fo2szpu]:  Saving output: {target_file}")
    miz.save(output_file)


    print("INFO [fo2szpu]:  Done")  # TODO:  add logging