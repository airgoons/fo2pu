# Native Dependencies
from types import SimpleNamespace
import os.path
import json
from operator import attrgetter

# External Dependencies
import dcs


def json_data_to_namespace(data):
    """Utility function to cleanly bring data into an object's namespace"""
    if isinstance(data, dict):
        return SimpleNamespace(**{
            k: json_data_to_namespace(v)
            for k, v in data.items()
        })
    return data


class UnitMap:
    def __init__(self, unit_type_tag_map:dict, factions:dict):
        self.unit_type_tag_map = unit_type_tag_map
        self.factions = factions

    @classmethod
    def from_json(cls, path:str):
        """Imports unit mapping data from a json"""
        # Input Validation
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise RuntimeError("Path does not exist or is not a file [{0}]".format(self._path))

        data = None
        try:
            with open(path, 'r') as json_file:
                data = json.load(json_file)
        except:
            print("ERROR:  JSON mangled [{0}]".format(path))  # TODO:  add logging
            raise

        return cls(
                    unit_type_tag_map = data.get("unit_type_tag_map"),
                    factions = data.get("factions")
                )
    
    class VehicleGroup:
        def __init__(self, spawn_radius:int, unit_group:list):
            self.spawn_radius = spawn_radius
            self.unit_group = unit_group


def nation_unit_string_to_pydcs_units(string_data):
    """Parses unit/quantity strings from within the dataset to a list of pydcs objects"""
    # expectation is a comma separated string of the form "pydcs_unit_object, quantity"

    try:
        unit_str, qty_str = [item.strip() for item in string_data.split(",")]  # ignore whitespace
    except:
        print("ERROR:  mangled data [{0}]".format(string_data))
        raise

    try:
        unit_ref = attrgetter(unit_str)(dcs)
        qty = int(qty_str)

        return (unit_ref, qty)
    
    except:
        print("ERROR:  mangled data --- unit_str={0} | qty_str={1}".format(unit_str, qty_str))
        raise


def formation_tag_to_pydcs_units(map:SimpleNamespace, faction:str, nation:str, formation_tag:str):   
    if faction not in ["BLUE", "RED"]:
        raise ValueError("ERROR:  Invalid faction [{0}]".format(faction))    

    # TODO:  check if nation is mappable for the given faction, if not then Default
    if nation is None:
        nation = "Default"

    try:
        unit_type_data = attrgetter("factions.{0}.nation_unit_map.{1}.{2}".format(faction, nation, formation_tag))(map)
        
        units = []
        for formation_data in unit_type_data.unit_list:
            unit_ref, qty = nation_unit_string_to_pydcs_units(formation_data)
            
            units.extend([unit_ref] * qty)

        return units

    except:
        print("ERROR:  mangled data")
        raise


class Formation:
    def __init__(self, name:str, faction:str, nation_tag:str, type_tag:str, position:dcs.mapping.Point, heading:int, vehicle_group:UnitMap.VehicleGroup):
        self.name = name
        self.faction = faction
        self.nation_tag = nation_tag
        self.type_tag = type_tag
        self.position = position
        self.heading = heading
        self.vehicle_group = vehicle_group

def formations_from_miz(miz:dcs.Mission, unit_map:UnitMap):
    drawings = miz.drawings.get_layer_by_name("Author")

    unit_type_tags = unit_map.unit_type_tag_map.values()

    formations = {}

    for faction_name, faction_data in unit_map.factions.items():
        print("INFO:  Processing faction [{0}]".format(faction_name))  # TODO:  logging
        nation_tags = faction_data.get("nation_name_tag_map").values()
        

        for obj in drawings.objects:
            if "_label" in obj.name:
                continue  # reject specific objects

            if obj.name not in formations:  # avoid duplication
                name = obj.name
                tags = name.split("-")[1:]  # NOTE:  assuming no whitespace
                faction = None
                nation_tag = None
                type_tag  = None
                
                if len(tags) == 0:
                    print("WARN:  tagless object [{0}]".format(obj.name))  # TODO:  logging
                    continue  # reject tagless items

                if faction_name in tags:
                    faction = faction_name

                for tag in tags:
                    if tag in nation_tags:
                        if nation_tag is not None:
                            print("WARN:  multiple nation tags [{0}]".format(obj.name))  # TODO:  logging
                            continue
                        else:
                            if faction is None:
                                faction = faction_name

                            nation_tag = tag
                        
                    if tag in unit_type_tags:
                        if type_tag is not None:
                            print("WARN:  multiple unit type tags [{0}]".format(obj.name))  # TODO:  logging
                            continue
                        else:
                            type_tag = tag

                if (faction is None) or (nation_tag is None) or (type_tag is None):
                    print("WARN:  invalid formation [{0}]".format(obj.name))  # TODO:  logging
                    continue  # invalid formation
                else:
                    vehicle_group_raw = unit_map.factions.get(faction).get("nation_unit_map").get(nation_tag).get(type_tag)
                    unit_group = []
                    for unit in vehicle_group_raw.get("unit_group"):
                        unit_ref = attrgetter(unit.get("unit_name"))(dcs)
                        unit_group.extend([unit_ref] * unit.get("qty"))
                        
                    vehicle_group = UnitMap.VehicleGroup(vehicle_group_raw.get("spawn_radius"), unit_group)

                    heading = unit_map.factions.get(faction).get("unit_heading")

                    formations[obj.name] = Formation(name, faction, nation_tag, type_tag, obj.position, heading, vehicle_group)  # NOTE:  duplication checked above
       
    return formations


def add_groups_from_formations(miz:dcs.Mission, unit_map:UnitMap, formations:dict):
    for formation_name, formation_obj in formations.items():
        dcs_country = None
        if formation_obj.faction == "BLUE":
            dcs_country = dcs.countries.CombinedJointTaskForcesBlue
        elif formation_obj.faction == "RED":
            dcs_country = dcs.countries.CombinedJointTaskForcesRed
        else:
            raise ValueError("Invalid faction [{0}]".format(formation_obj.faction))

        group = miz.vehicle_group_platoon(
            country=dcs_country,
            name=formation_name,
            types=formation_obj.vehicle_group.unit_group,
            position=formation_obj.position,
            heading=formation_obj.heading
        )


if __name__ == "__main__":
    target_file = "UTNS_ Uprising PRACTICE_fo_export (1).miz"  # TODO:  Add input argument
    unit_map_file = "unit_map.json"    # TODO: Add input argument
    output_file = "{0}_{1}.miz".format(os.path.splitext(target_file)[0], "fo2szpu")  # TODO: Add input argument with default as {target_file}_fo2szpu.miz
    print("INFO [fo2szpu]:  Configuration:  target_file= {0} | unit_map= {1} | output_file={2}".format(target_file, unit_map_file, output_file))  # TODO:  add logging


    unit_map = UnitMap.from_json(unit_map_file)

    miz = dcs.Mission(terrain=dcs.terrain.Kola())
    miz.load_file(target_file)
    print("INFO [fo2szpu]:  Mission Loaded")  # TODO:  add logging
    
    formations = formations_from_miz(miz, unit_map)
    print("INFO [fo2szpu]:  Formations found= {0}".format(len(formations)))  # TODO:  add logging

    vehicle_groups = add_groups_from_formations(miz, unit_map, formations)

    print("INFO [fo2szpu]:  Saving output: {0}".format(target_file))
    miz.save(output_file)

    print("INFO [fo2szpu]:  Done")  # TODO:  add logging