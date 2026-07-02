import dcs
from vehicle_set import VehicleSet, Vehicle

class UnitSpawner:
    @staticmethod
    def get_country(miz:dcs.Mission, vehicle_set:VehicleSet):
        country = None
        if vehicle_set.faction.tag == "BLUE":
            country = miz.country_by_id(dcs.countries.CombinedJointTaskForcesBlue.id)
        elif vehicle_set.faction.tag == "RED":
            country = miz.country_by_id(dcs.countries.CombinedJointTaskForcesRed.id)
        else:
            raise NotImplementedError(f"Invalid faction name [{data.faction.tag}]")
        return country

    @staticmethod
    def add_static_group(miz:dcs.Mission, name:str, vehicles:list[Vehicle]):
        if len(vehicles) > 0:
            group_name = f"{name} STATIC"

            static_point = dcs.point.StaticPoint(vehicles[0].position)

            static_group = dcs.unitgroup.StaticGroup(miz.next_group_id(), group_name)

            country = UnitSpawner.get_country(miz, vehicles[0].parent)
            heading = vehicles[0].parent.faction.unit_heading

            for vehicle in vehicles:
                if not vehicle.is_static:
                    raise ValueError(f"vehicle.is_static = False when creating static group... [{vehicle.name}]")

                unit = dcs.unit.Static(miz.next_unit_id(), vehicle.name, vehicle.dcs_object, miz.terrain)
                
                unit.position = vehicle.position
                unit.heading = heading

                static_group.add_unit(unit)
            
            static_group.hidden = False
            static_group.dead = False
            static_group.add_point(static_point)

            country.add_static_group(static_group)
            return static_group
        else:
            return None
    
    @staticmethod
    def add_active_group(miz:dcs.Mission, name:str, vehicles:list[Vehicle]):
        if len(vehicles) > 0:
            group_name = f"{name} ACTIVE"


            country = UnitSpawner.get_country(miz, vehicles[0].parent)
            heading = vehicles[0].parent.faction.unit_heading
            
            active_group = miz.vehicle_group(country, group_name, vehicles[0].dcs_object, vehicles[0].position, heading, 1)
            active_group.units[0].name = vehicles[0].name


            for vehicle in vehicles:
                if vehicle.is_static:
                    raise ValueError(f"vehicle.is_static = True when creating active group [{vehicle.name}]")

                unit = miz.vehicle(vehicle.name, vehicle.dcs_object)
                # unit = dcs.unit.Unit(miz.next_unit_id(), miz.terrain, vehicle.name, vehicle.dcs_object)
                unit.position = vehicle.position
                unit.heading = heading
                
                active_group.add_unit(unit)

            active_group.hidden_on_mfd = True
            active_group.hidden_on_planner = True

            return active_group
        else:
            return None

    @staticmethod
    def add_vehicle_set(miz:dcs.Mission, vehicle_set:VehicleSet):
        statics = [vehicle for vehicle in vehicle_set.vehicles if vehicle.is_static == True]
        actives = [vehicle for vehicle in vehicle_set.vehicles if vehicle.is_static == False]
        
        static_group = UnitSpawner.add_static_group(miz, vehicle_set.name, statics)
        active_group = UnitSpawner.add_active_group(miz, vehicle_set.name, actives)

        groups = [static_group, active_group]
        while None in groups:
            groups.remove(None)

        return groups


    @staticmethod
    def add_vehicle_sets(miz:dcs.Mission, vehicle_sets:list[VehicleSet]):
        groups = []

        if type(vehicle_sets) not in [list, tuple]:
            raise TypeError("vehicle_sets must be type list or tuple")

        for vehicle_set in vehicle_sets:
            if not isinstance(vehicle_set, VehicleSet):
                raise TypeError("items in vehicle_sets must each be of type VehicleSet")

        for vehicle_set in vehicle_sets:
            _groups = UnitSpawner.add_vehicle_set(miz, vehicle_set)
            groups.extend(_groups)
        
        return groups
