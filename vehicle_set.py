import random

import dcs
from unit_map import UnitMap, Faction, Nation, Formation

class Vehicle:
    def __init__(self, name:str, parent:VehicleSet, dcs_object, position:dcs.mapping.Point, is_static=True):
        if type(parent) is not VehicleSet:
            raise TypeError("parent must be type VehicleSet")

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
        self.vehicles = self.positioner.generate_positions(self, miz)

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

    _IADS_BASE_DESIGNATORS = {
        dcs.vehicles.AirDefence.Hawk_cwar: "Hawk_cwar",
        dcs.vehicles.AirDefence.Hawk_ln: "Hawk_ln",
        dcs.vehicles.AirDefence.Hawk_pcp: "Hawk_pcp",
        dcs.vehicles.AirDefence.Hawk_sr: "Hawk_sr",
        dcs.vehicles.AirDefence.Hawk_tr: "Hawk_tr",
        dcs.vehicles.AirDefence.SA_11_Buk_CC_9S470M1: "SA_11_Buk_CC_9S470M1",
        dcs.vehicles.AirDefence.SA_11_Buk_LN_9A310M1: "SA_11_Buk_LN_9A310M1",
        dcs.vehicles.AirDefence.SA_11_Buk_SR_9S18M1: "SA_11_Buk_SR_9S18M1",
        dcs.vehicles.AirDefence.M1097_Avenger: "M1097_Avenger",
        dcs.vehicles.AirDefence.x_2S6_Tunguska: "x_2S6_Tunguska",
        dcs.vehicles.AirDefence.HQ_7_LN_SP: "HQ_7_LN_SP",
        dcs.vehicles.AirDefence.Roland_Radar: "Roland_Radar",
        dcs.vehicles.AirDefence.Roland_ADS: "Roland_ADS"
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

    @staticmethod
    def check_air_defense_battery(formation:Formation):
        if formation.formation_type is Formation.FormationType.ADA:
            return True
        else:
            return False

    @staticmethod
    def normalize_heading(heading):
        theta = heading

        while theta > 360:
            theta = theta - 360
        
        while theta < 0:
            theta = theta + 360

        return theta

    @staticmethod
    def get_iads_designator(dcs_object):
        if dcs_object in VehiclePositioner._IADS_BASE_DESIGNATORS:
            return VehiclePositioner._IADS_BASE_DESIGNATORS.get(dcs_object) 

        else:
            return ""


    def __init__(self, zone_radius:int, dispersion_distance:int):
        self.zone_radius = zone_radius
        self.dispersion_distance = dispersion_distance
    
    
    def _generate_positions_default(self, vehicle_set:VehicleSet, miz:dcs.Mission):
        formation = vehicle_set.formation

        theta_0 = VehiclePositioner.normalize_heading(vehicle_set.faction.unit_heading)
        
        # combat area
        theta_1c_high = VehiclePositioner.normalize_heading(theta_0 + 70)
        theta_1c_low = VehiclePositioner.normalize_heading(theta_0 - 70)
        theta_1c = random.randint(theta_1c_low, theta_1c_high)

        combat_distance = random.randint(1, formation.zone_radius)

        combat_area_center = formation.position.point_from_heading(theta_1c, combat_distance)

        

        # support area
        theta_1s_high = VehiclePositioner.normalize_heading(theta_0 - 180 + 35)
        theta_1s_low = VehiclePositioner.normalize_heading(theta_0 - 180 - 35)
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
        for i in range(len(combat_units)):
            combat_unit = combat_units[i]
            position = None

            if i == 0:
                position = combat_area_center
            else:
                p0 = combat_area_center.point_from_heading(180, formation.dispersion_distance * i)
                theta_0 = int(combat_area_center.heading_between_point(p0))
                d0 = combat_area_center.distance_to_point(p0)
                theta_1 = VehiclePositioner.normalize_heading(random.randint(theta_0 - 10, theta_0 + 10))

                position = combat_area_center.point_from_heading(theta_1, d0)


            name = formation.name

            is_static = VehiclePositioner.check_static(combat_unit)
            if is_static:
                name += " STATIC"
            else:
                name += " ACTIVE"

            name += f" COMBAT {i}"
            
            vehicle = Vehicle(name, vehicle_set, combat_unit, position, is_static)
            vehicles.append(vehicle)

        # for support_unit in support_units:
        for j in range(len(support_units)):
            support_unit = support_units[j] 
            position = None
            if j == 0:
                position = support_area_center
            else:
                p0 = support_area_center.point_from_heading(180, formation.dispersion_distance * j)
                theta_0 = int(support_area_center.heading_between_point(p0))
                d0 = support_area_center.distance_to_point(p0)
                theta_1 = VehiclePositioner.normalize_heading(random.randint(theta_0 - 10, theta_0 + 10))
                
                position = support_area_center.point_from_heading(theta_1, d0)
            
            name = formation.name
            is_static = VehiclePositioner.check_static(support_unit)
            if is_static:
                name += " STATIC"
            else:
                name += " ACTIVE"

            name += f" SUPPORT {j}"

            vehicle = Vehicle(name, vehicle_set, support_unit, position, is_static)
            vehicles.append(vehicle) 

        return tuple(vehicles)


    def _generate_positions_ada(self, vehicle_set:VehicleSet, miz:dcs.Mission):
        formation = vehicle_set.formation

        if len(formation.unit_set) <= 0:
            raise ValueError("formation.unit_set must contain units")

        theta_0 = VehiclePositioner.normalize_heading(vehicle_set.faction.unit_heading)

        theta_1c_high = VehiclePositioner.normalize_heading(theta_0 + 70)
        theta_1c_low = VehiclePositioner.normalize_heading(theta_0 - 70)
        theta_1c = random.randint(theta_1c_low, theta_1c_high)

        area_distance = random.randint(1, formation.zone_radius)
        
        area_center = formation.position.point_from_heading(theta_1c, area_distance)
        
        delta_theta2 = int(360/(len(formation.unit_set)))

        vehicles = []
        for i in range(len(formation.unit_set)):
            position = None
            if i == 0:
                position = area_center
            else:
                theta2 = random.randint(
                    VehiclePositioner.normalize_heading(delta_theta2 * i - int(delta_theta2/3)),
                    VehiclePositioner.normalize_heading(delta_theta2 * i + int(delta_theta2/3))
                )
                position = area_center.point_from_heading(theta2, formation.dispersion_distance)


            
            unit = formation.unit_set[i]
            iads_designator = VehiclePositioner.get_iads_designator(unit)
            name = f"{formation.name} ACTIVE {i} {iads_designator}"

            vehicle = Vehicle(name, vehicle_set, unit, position, False)
            vehicles.append(vehicle)

        return tuple(vehicles)


    def generate_positions(self, vehicle_set:VehicleSet, miz:dcs.Mission):
        vehicles = None

        if VehiclePositioner.check_air_defense_battery(vehicle_set.formation):
            vehicles = self._generate_positions_ada(vehicle_set, miz)
        else:
            vehicles = self._generate_positions_default(vehicle_set, miz)

        return vehicles
        
        

