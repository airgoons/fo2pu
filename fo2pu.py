# Native Dependencies
import os.path
import json
from operator import attrgetter

# External Dependencies
import dcs

# Internal Dependencies
from unit_map import UnitMap, Formation
from vehicle_set import VehicleSet

from unit_spawner import UnitSpawner


def formations_to_miz_unitgroups(miz:dcs.Mission, formations:dict):
    """ Deprecated """
    for name, data in formations.items():
        print(f"INFO:  adding group [{name}]")

        country = None
        if data.faction.tag == "BLUE":
            country = miz.country_by_id(dcs.countries.CombinedJointTaskForcesBlue.id)
        elif data.faction.tag == "RED":
            country = miz.country_by_id(dcs.countries.CombinedJointTaskForcesRed.id)
        else:
            raise NotImplementedError(f"Invalid faction name [{data.faction.tag}]")

        vehicle_group = miz.vehicle_group_platoon(
            country = country,
            name = name,
            types = data.formation.unit_set,
            position = data.position,
            heading = data.faction.unit_heading,
            formation = dcs.unitgroup.VehicleGroup.Formation.Scattered,
            move_formation = dcs.unitgroup.PointAction.OffRoad
        )



if __name__ == "__main__":
    target_file = "UTNS_ Uprising PRACTICE_fo_export (1).miz"  # TODO:  Add input argument
    unit_map_file = "unit_map.json"    # TODO: Add input argument
    output_file = "{0}_{1}.miz".format(os.path.splitext(target_file)[0], "fo2szpu")  # TODO: Add input argument with default as {target_file}_fo2szpu.miz
    print(f"INFO [fo2szpu]:  Configuration:  target_file= {target_file} | unit_map= {unit_map_file} | output_file={output_file}")  # TODO:  add logging


    unit_map = UnitMap.from_json(unit_map_file)

    miz = dcs.Mission(terrain=dcs.terrain.Kola())
    miz.load_file(target_file)
    print("INFO [fo2szpu]:  Mission Loaded")  # TODO:  add logging
    
    formations = Formation.formations_from_miz(miz, unit_map)

    vehicle_sets = VehicleSet.sets_from_formations(formations, miz)

    groups = UnitSpawner.add_vehicle_sets(miz, vehicle_sets)

    print(f"INFO [fo2szpu]:  Saving output: {output_file}")
    miz.save(output_file)


    print("INFO [fo2szpu]:  Done")  # TODO:  add logging
