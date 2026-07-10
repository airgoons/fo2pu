# Native Dependencies
import os
import json
from operator import attrgetter
from datetime import datetime
import logging
import argparse

# External Dependencies
import dcs

# Internal Dependencies
from unit_map import UnitMap, Formation
from vehicle_set import VehicleSet

from unit_spawner import UnitSpawner

def initialize_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logging.addLevelName(logging.WARNING, "WARN")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    file_handler = logging.FileHandler(f"fo2pu.log", 'w')  # overwrite log on each run
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t", "--target",
        default="test_input.miz",
        help="path to input miz"
    )

    parser.add_argument(
        "-u", "--unit-map",
        default="unit_map.json",
        help="path to unit map json"
    )

    parser.add_argument(
        "-o", "--output",
        default="fo2pu.miz",
        help="path to output miz"
    )

    return parser.parse_args()


if __name__ == "__main__":
    logger = initialize_logging()
    arguments = parse_arguments()

    target_file = arguments.target
    unit_map_file = arguments.unit_map
    output_file = arguments.output

    if not os.path.isfile(target_file):
        logger.critical(f"path provided by -t/--target is not a file or does not exist [{target_file}]")

    elif not os.path.isfile(unit_map_file):
        logger.critical(f"path provided by -u/--unit_map is not a file or does not exist [{unit_map_file}]")
    
    else:
        logger.info(f"Configuration:  target_file= {target_file} | unit_map= {unit_map_file} | output_file={output_file}") 

        # Process Data
        unit_map = UnitMap.from_json(unit_map_file)

        miz = dcs.Mission(terrain=dcs.terrain.Kola())
        miz.load_file(target_file)
        logger.info("Mission Loaded")
        
        formations = Formation.formations_from_miz(miz, unit_map)

        vehicle_sets = VehicleSet.sets_from_formations(formations, miz)

        groups = UnitSpawner.add_vehicle_sets(miz, vehicle_sets)

        logger.info(f"Saving output: {output_file}")
        miz.save(output_file)

        # End
        logger.info("Done")
