import os
import json
from operator import attrgetter
from enum import StrEnum
from copy import deepcopy

import dcs


class UnitSetEntry:
    def __init__(self, dcs_obj_name:str, qty:int):
        self.dcs_obj_name = dcs_obj_name
        self.qty = qty

        try:
            self.dcs_obj = attrgetter(dcs_obj_name)(dcs)
        except:
            raise RuntimeError("Invalid DCS object name [{0}]".format(dcs_obj_name))

    @staticmethod
    def from_dict(d):
        return UnitSetEntry(
            dcs_obj_name = d["dcs_obj_name"],
            qty = d["qty"]
        )


class Formation:
    class FormationType(StrEnum):
        ADA = "ADA"
        ARMOR = "ARMOR"
        ARTY = "ARTY"
        ENG = "ENG"
        GUER = "GUER"
        HQ = "HQ"
        INF = "INF"
        LAT = "LAT"
        MECH = "MECH"
        MLRS = "MLRS"
        SF = "SF"
        
    def __init__(self, nation:Nation, formation_type:FormationType, zone_radius:int, dispersion_distance:int, unit_set:list):
        self.nation = nation
        self.formation_type = formation_type
        self.zone_radius = zone_radius
        self.dispersion_distance = dispersion_distance
        self.unit_set = unit_set

        self._name = None 
        self._position = None
        self._tags = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name:str):
        if type(name) is not str:
            raise TypeError("name must be type str")
        
        if name == "":
            raise ValueError("name cannot be empty")
        
        self._name = name

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position:dcs.mapping.Point):
        if position is None:
            raise ValueError("position cannot be None")
        
        if type(position) is not dcs.mapping.Point:
            raise TypeError("position must be type dcs.mapping.Point")

        self._position = position

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags:tuple):
        if tags is None:
            raise ValueError("tags cannot be None")

        if type(tags) not in [list, tuple]:
            raise TypeError("tags type must be list or tuple")

        if len(tags) == 0:
            raise ValueError("tags cannot be empty")

        self._tags = tuple(tags)

    @staticmethod
    def from_dict(nation, key, data):
        unit_set_raw = [UnitSetEntry.from_dict(entry) for entry in data["unit_set"]]
        
        unit_set = []
        for entry in unit_set_raw:
            unit_set.extend([entry.dcs_obj] * entry.qty)

        return Formation(
            nation = nation,
            formation_type = Formation.FormationType(key),
            zone_radius = data["zone_radius"],
            dispersion_distance = data["dispersion_distance"],
            unit_set = unit_set   
        )

    @staticmethod
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
                            formation = deepcopy(nation.formations.get(tag))

            if formation is None:
                print(f"WARN:  invalid formation {name}")
            else:
                formation.name = obj.name
                formation.position = obj.position
                formation.tags = tags
                formations[name] = formation

        return formations



class Nation:
    def __init__(self, faction:Faction, tag:str, formations:dict):
        self.faction = faction
        self.tag = tag
        self.formations = formations

    @staticmethod
    def from_dict(faction, key, data):
        nation = Nation(
            faction=faction,
            tag = key,
            formations = None
        )
        
        nation.formations = {
            formation.formation_type: formation for formation in
            (Formation.from_dict(nation, k, v) for k,v in data.items())
        }

        return nation


class Faction:
    def __init__(self, tag:str, unit_heading:int, nations:list):
        self.tag = tag
        self.unit_heading = unit_heading
        self.nations = nations

    @staticmethod
    def from_dict(key, data):
        faction = Faction(
            tag = key,
            unit_heading = data["unit_heading"],
            nations = None
        )
        faction.nations = {
            nation.tag: nation for nation in
            (Nation.from_dict(faction, k, v) for k,v in data["nations"].items())
        }
        return faction


class UnitMap:
    def __init__(self, miz_drawing_layer:str, factions:dict):
        self.miz_drawing_layer = miz_drawing_layer
        self.factions = factions

    @staticmethod
    def from_dict(data):
        return UnitMap(
            miz_drawing_layer = data["miz_drawing_layer"],
            factions = {
                faction.tag: faction for faction in
                (Faction.from_dict(k, v) for k,v in data["factions"].items())
            }
        )

    @staticmethod
    def from_json(path):
        """Imports unit mapping data from a json"""
        # Input Validation
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise RuntimeError(f"Path does not exist or is not a file [{path}]")

        data = None
        try:
            with open(path, 'r') as json_file:
                data = json.load(json_file)
        except Exception as e:
            raise RuntimeError(f"JSON load failure [{path}]") from e

        return UnitMap.from_dict(data)
