import random

import dcs
from unit_map import UnitMap, Faction, Nation, Formation

class Vehicle:
    def __init__(self, name:str, parent:VehicleSet, dcs_object, position:dcs.mapping.Point, is_static=True):
        self.name = name
        self.parent = parent
        self.dcs_object = dcs_object
        self.position = position
        self.is_static = is_static


class VehicleSet:
    def __init__(self, name:str, tags:list, faction:Faction, nation:Nation, formation:Formation, position:dcs.mapping.Point, miz):
        self.name = name
        self.tags = tags
        self.faction = faction
        self.nation = nation
        self.formation = formation
        self.position = position
        self.positioner = VehiclePositioner(formation.zone_radius, formation.dispersion_distance)
        self.vehicles = self.positioner.generate_positions(formation, miz)

    @staticmethod
    def sets_from_formations(formations:dict, miz:dcs.Mission):
        sets = []

        for name, formation in formations.items():
            vehicle_set = VehicleSet(name, formation.tags, formation.nation.faction, formation.nation, formation, formation.position, miz)
            sets.append(vehicle_set)

        return sets
        

class VehiclePositioner:
    """
    governs the positionining logic of unit_map.Formations
        zone_radius:            the maximum distance from the formation's given approximate position
        dispersion_distance:    the distance between vehicles

    """
    _STATIC_SPAWN_OVERRIDE = {
        dcs.vehicles.AirDefence: True
    }

    _SUPPORT_VEHICLE_OVERRIDE = {
        dcs.vehicles.Unarmed: True
    }
    @staticmethod
    def _check_property(unit, prop):
        for vehicle_class, override in prop.items():
                _name = unit.__name__
                _dict = vehicle_class.__dict__
                if _name in _dict:
                    return override
        return False

    @staticmethod
    def check_static(unit):
        return not(VehiclePositioner._check_property(unit, VehiclePositioner._STATIC_SPAWN_OVERRIDE))

    @staticmethod
    def check_support(unit):
        return VehiclePositioner._check_property(unit, VehiclePositioner._SUPPORT_VEHICLE_OVERRIDE)

    def __init__(self, zone_radius:int, dispersion_distance:int):
        self.zone_radius = zone_radius
        self.dispersion_distance = dispersion_distance
    
    

    def generate_positions(self, formation:Formation, miz:dcs.Mission):
        def normalize_heading(heading):
            theta = heading

            while theta > 360:
                theta = theta - 360
            
            while theta < 0:
                theta = theta + 360

            return theta
        
        theta_0 = normalize_heading(formation.nation.faction.unit_heading)
        
        # combat area
        theta_1c_high = normalize_heading(theta_0 + 70)
        theta_1c_low = normalize_heading(theta_0 - 70)
        theta_1c = random.randint(theta_1c_low, theta_1c_high)

        combat_distance = random.randint(1, formation.zone_radius)

        combat_area_center = formation.position.point_from_heading(theta_1c, combat_distance)

        

        # support area
        theta_1s_high = normalize_heading(theta_0 - 180 + 70)
        theta_1s_low = normalize_heading(theta_0 - 180 - 70)
        theta_1s = random.randint(theta_1s_low, theta_1s_high)


        support_distance_0 = random.randint(0, int(formation.zone_radius/2))
        support_distance_1 = random.randint(2*formation.dispersion_distance, 3*formation.dispersion_distance)  # ensure spacing between combat and support sections 
        support_distance = support_distance_0 + support_distance_1
        support_area_center = combat_area_center.point_from_heading(theta_1s, support_distance)

        # split formation into combat and support types
        combat_units = []
        support_units = []

        for unit in formation.unit_set:            
            if VehiclePositioner.check_support(unit):
                support_units.append(unit)
            else:
                combat_units.append(unit)

        vehicles = []
        for combat_unit in combat_units:
            vehicle = None
            position = None
            if len(vehicles) == 0:
                position = combat_area_center
            else:
                p0 = combat_area_center.point_from_heading(180, formation.dispersion_distance)
                theta_0 = int(formation.position.heading_between_point(p0))
                d0 = formation.position.distance_to_point(p0)
                theta_1 = normalize_heading(random.randint(theta_0 - 5, theta_0 + 5))

                position = formation.position.point_from_heading(theta_1, d0)


            name = f"{formation.name} {len(vehicles)}"
            is_static = VehiclePositioner.check_static(combat_unit)
            if is_static:
                name += " STATIC"
            else:
                name += " ACTIVE"
            
            vehicle = Vehicle(name, self, combat_unit, position, is_static)
            vehicles.append(vehicle) 

        for support_unit in support_units:
            vehicle = None
            position = None
            if len(vehicles) == 0:
                position = support_area_center
            else:
                p0 = support_area_center.point_from_heading(180, formation.dispersion_distance)
                theta_0 = int(formation.position.heading_between_point(p0))
                d0 = formation.position.distance_to_point(p0)
                theta_1 = normalize_heading(random.randint(theta_0 - 5, theta_0 + 5))
                
                position = formation.position.point_from_heading(theta_1, d0)
            
            
            name = f"{formation.name} {len(vehicles)}"
            is_static = VehiclePositioner.check_static(support_unit)
            if is_static:
                name += " STATIC"
            else:
                name += " ACTIVE"

            vehicle = Vehicle(name, formation, support_unit, position, is_static)
            vehicles.append(vehicle) 


        return tuple(vehicles)

