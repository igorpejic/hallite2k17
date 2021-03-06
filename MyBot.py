# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("CarefulAttackerV3")
# Then we print our start message to the logs
logging.info("Starting my Settler bot!")
import time

from quad_tree_map import QuadTree
from cocos.rect import Rect

def get_planets_as_rects(all_planets):
    '''
    returns (x1, y1, x2, y2)
    '''
    rects = []
    for planet in all_planets:
        rects.append(
            Rect(planet.x - planet.radius,
                 planet.y - planet.radius,
                 planet.radius * 2,
                 planet.radius * 2
                 ))
    return rects

all_planets = game.map.all_planets()
blockers = get_planets_as_rects(all_planets)

quad_tree = QuadTree(0, 0, game.map.width, game.map.height, blockers, 0.5)
ship_trips = {}

class ProtectMission(object):
    def __init__(self, planet_to_protect, ship_id):
        self.planet_to_protect = planet_to_protect
        self.ship_id = ship_id
        ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_protect)

    def get_command(self, game_map, ship, enemy_planet=None, missions=None):
        return ship.navigate2(
            ship_trips,
            quad_tree,
            ship.closest_point_to(self.planet_to_protect),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=True)


class ColonizeMission(object):
    def __init__(self, planet_to_attack, ship_id):
        self.planet_to_attack = planet_to_attack
        self.ship_id = ship_id
        ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)

    def get_command(self, game_map, ship, enemy_planet=None, missions=None):
        docked_ships = self.planet_to_attack.all_docked_ships()
        logging.info('CAN DOCK {}'.format(ship.can_dock(self.planet_to_attack)))
        if docked_ships:
            docked_ship = docked_ships[0]
        else:
            docked_ship = self.planet_to_attack
        if not docked_ships and ship.can_dock(self.planet_to_attack):
            return ship.dock(self.planet_to_attack)
        return ship.navigate2(
            ship_trips,
            quad_tree,
            ship.closest_point_to(self.planet_to_attack),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            ignore_ships=False)


'''
class DockMission(object):
    def __init__(self, planet_to_attack, ship_id):
        self.planet_to_attack = planet_to_attack
        self.ship_id = ship_id

    def get_command(self, game_map, ship, enemy_planets=None, missions=None):
        if self.planet_to_attack.owner and self.planet_to_attack.owner.id != game_map.my_id:
            logging.info('Docking mission aborted')
            return attack_mission_command(enemy_planets, ship, missions)
        if self.planet_to_attack.is_full():
            logging.info('Docking mission aborted (planet full)')
            return attack_mission_command(enemy_planets, ship, missions)
        elif ship.can_dock(self.planet_to_attack):
            logging.info('Docking mission successful')
            return ship.dock(self.planet_to_attack)
        else:
            logging.info('Docking navigating to planet')
            return ship.navigate(
                ship.closest_point_to(self.planet_to_attack),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False)
'''

class ShipAttackMission(object):
    def __init__(self, planet_to_attack, ship_id):
        logging.info('Attack mission ({}) -> {}'.format(ship_id, planet_to_attack))
        self.planet_to_attack = planet_to_attack
        self.player_to_attack = planet_to_attack.owner.id
        self.ship_id = ship_id
        ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)

    def get_command(self, game_map, ship, enemy_ships, my_planets, missions=None):
        self.planet_to_attack = game_map.get_player(self.planet_to_attack.owner.id).get_ship(self.planet_to_attack.id)
        if not self.planet_to_attack:
            self.planet_to_attack = get_closest_enemy_ship(enemy_ships, ship)
            self.trip = None
        return ship.navigate2(
                ship_trips,
                quad_tree,
                ship.closest_point_to(self.planet_to_attack),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False)


def get_closest_enemy_ship(enemy_ships, ship):
    if not enemy_ships:
        return None
    closest_enemy_ship = min(
        enemy_ships,
        key=lambda x: ship.calculate_distance_between(x))
    return closest_enemy_ship

def get_furthest_planet(planets, ship):
    if not planets:
        return None
    furthest_planet = min(
        planets,
        key=lambda x: ship.calculate_distance_between(x))
    return furthest_planet


class AttackMission(object):
    def __init__(self, planet_to_attack, ship_id):
        logging.info('Attack mission ({}) -> {}'.format(ship_id, planet_to_attack))
        self.planet_to_attack = planet_to_attack
        self.ship_id = ship_id
        ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)

    def get_command(self, game_map, ship, enemy_planets, missions=None):
        try:
            self.planet_to_attack = game_map.get_planet(self.planet_to_attack.id)
        except:
            self.planet_to_attack = get_closest_enemy_planet(enemy_planets, ship)
            if not self.planet_to_attack:
                return None
        if not self.planet_to_attack:
            self.planet_to_attack = get_closest_enemy_planet(enemy_planets, ship)
            ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)

        # if i am owner
        if self.planet_to_attack.owner and self.planet_to_attack.owner.id == game_map.my_id:
            # if its full
            if self.planet_to_attack.is_full():
                logging.info('{} Attacker finding different target'.format(ship.id))
                closest_enemy_planet = get_closest_enemy_planet(enemy_planets, ship)
                if closest_enemy_planet:
                    self.planet_to_attack = closest_enemy_planet
                    ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)
                    return ship.navigate2(
                        ship_trips,
                        quad_tree,
                        ship.closest_point_to(self.planet_to_attack),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False)
                else:
                    logging.info("NO closest enemy planet")
            # if its not full
            elif ship.can_dock(self.planet_to_attack):
                logging.info('{} Attacker docking to our planet'.format(ship.id))
                return ship.dock(self.planet_to_attack)
            else:
                self.planet_to_attack = get_closest_enemy_planet(enemy_planets, ship)
                ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)
                if self.planet_to_attack:
                    return ship.navigate2(
                        ship_trips,
                        quad_tree,
                        ship.closest_point_to(self.planet_to_attack),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False)
        # if its unoccupied
        elif not self.planet_to_attack.owner:
            if ship.can_dock(self.planet_to_attack):
                logging.info('{} Attacker docking to non-taken planet'.format(ship.id))
                return ship.dock(self.planet_to_attack)
            else:
                logging.info('{} Attacker navigating to dock position'.format(ship.id))
                return ship.navigate2(
                    ship_trips,
                    quad_tree,
                    ship.closest_point_to(self.planet_to_attack),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False)

        else:
            docked_ships = [ship for ship in self.planet_to_attack.all_docked_ships() if ship.owner.id != game_map.my_id]
            # if it has docked ships
            if docked_ships:
                docked_ship = docked_ships[0]
                logging.info('{} Attacker navigating to docked ship'.format(ship.id))
                logging.info('{} - {} - {}'.format(docked_ship, ship, ship.closest_point_to(docked_ship)))
                return ship.navigate2(
                    ship_trips,
                    quad_tree,
                    ship.closest_point_to(docked_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False)
            else:
                if ship.can_dock(self.planet_to_attack):
                    logging.info('Attacker docking to destroyed planet')
                    return ship.dock(self.planet_to_attack)
                else:
                    self.planet_to_attack = get_closest_enemy_planet(enemy_planets, ship)
                    ship_trips[self.ship_id] = ship.get_ship_trip(quad_tree, self.planet_to_attack)
                    logging.info('Attacker navigating to planet with ships')
                    return ship.navigate2(
                        ship_trips,
                        quad_tree,
                        ship.closest_point_to(self.planet_to_attack),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False)


def get_closest_unfilled_planet(planets, element):
    unfilled_planets = [p for p in planets if not p.is_full()]
    if unfilled_planets:
        closest_unfilled = min(
            unfilled_planets,
            key=lambda x: element.calculate_distance_between(x))
    else:
        closest_unfilled = None
    return closest_unfilled

def get_closest_enemy_planet(enemy_planets, element):
    if not enemy_planets:
        return None
    closest_enemy_planet = min(
        enemy_planets,
        key=lambda x: element.calculate_distance_between(x))
    return closest_enemy_planet


def attack_mission_command(enemy_planets, ship, missions):
    closest_enemy_planet = get_closest_enemy_planet(enemy_planets, ship)
    if closest_enemy_planet:
        missions[ship.id] = AttackMission(
            closest_enemy_planet, ship.id)
        ship_command = missions[ship.id].get_command(
            game_map, ship, enemy_planets, missions)
        return ship_command
    else:
        logging.info("NO closest enemy planet; cant give mission")
        return None


def ship_attack_mission_command(enemy_ships, ship, missions, my_planets):
    closest_enemy_ship = get_closest_enemy_ship(enemy_ships, ship)
    furthest_planet = get_furthest_planet(my_planets, ship)
    if (closest_enemy_ship and furthest_planet and
        ship.calculate_distance_between(furthest_planet) + 4 > ship.calculate_distance_between(closest_enemy_ship)):
        missions[ship.id] = ShipAttackMission(
            closest_enemy_ship, ship.id)
        ship_command = missions[ship.id].get_command(
            game_map, ship, enemy_ships, missions)
        return ship_command
    else:
        logging.info("NO closest enemy ship; cant give mission")
        return None

import pickle
game_map = game.map
with open('game_map.pkl', 'wb') as output:
    pickle.dump(game.map, output)

turn = 0
missions = {}

while True:
    turn += 1
    logging.info(ship_trips)
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    start = time.time()
    my_id = game_map.my_id
    command_queue = []
    all_me = game_map.get_me()
    total_ships = all_me.all_ships()
    ship_ids = [ship.id for ship in total_ships]
    ids_to_remove = []
    for ship_id in ship_trips.keys():
        if ship_id not in ship_ids:
            ids_to_remove.append(ship_id)
    for i in ids_to_remove:
        del ship_trips[i]
    planets_to_be_attacked = []
    planets = game_map.all_planets()
    my_planets = [p for p in planets if p.owner and p.owner.id == my_id]
    enemy_planets = [p for p in planets if not p.owner or p.owner.id != my_id]
    non_taken_planets = [p for p in planets if not p.owner]
    all_enemy_ships = [ship for ship in game_map._all_ships() if ship.owner.id != my_id]

    if turn <= 2:
        taken_enemy_planets = [p for p in planets if p.owner and p.owner.id != my_id]
        closest_enemy_planets = planets
        ships_to_expand = total_ships[:3]
        for i, ship in enumerate(ships_to_expand):
            closest_enemy_planets = sorted(
                closest_enemy_planets,
                key=lambda x: ship.calculate_distance_between(x))
            closest_enemy_planet = closest_enemy_planets[0]
            # closest_enemy_planets.remove(closest_enemy_planet)
            missions[ship.id] = ColonizeMission(
                closest_enemy_planet, ship.id)
            ship_command = missions[ship.id].get_command(
                game_map, ship)
            if ship_command:
                command_queue.append(ship_command)
        # if len(total_ships) > 2:
        #     if taken_enemy_planets:
        #         logging.info(enemy_planets)
        #         missions[total_ships[2].id] = attack_mission_command(enemy_planets, ship, missions)
        #     else:
        #         closest_enemy_ship = min(
        #             all_enemy_ships,
        #             key=lambda x: ship.calculate_distance_between(x)
        #         )
        #         logging.info(closest_enemy_ship)
        #         missions[total_ships[2].id] = ShipAttackMission(
        #             closest_enemy_ship, ship.id)
        #         ship_command = missions[ship.id].get_command(
        #             game_map, ship, all_enemy_ships, missions)
        game.send_command_queue(command_queue)

    else:
        for ship in total_ships:
            ship_command = None
            end_time = time.time() - start
            if end_time >= 1.25:
                game.send_command_queue(command_queue)
                break
            # If the ship is docked
            if ship.docking_status == ship.DockingStatus.DOCKED or ship.docking_status == ship.DockingStatus.DOCKING:
                # Skip this ship
                continue
            if ship.id in missions.keys():
                if enemy_planets:
                    if isinstance(missions[ship.id], ShipAttackMission):
                        ship_command = missions[ship.id].get_command(
                            game_map, ship, all_enemy_ships, my_planets, missions)
                    else: # AttackMission ; ColonizeMission
                        ship_command = missions[ship.id].get_command(
                            game_map, ship, enemy_planets, missions)
            elif ship.id % 2 == 0 or turn < 50:
                closest_unfilled = get_closest_unfilled_planet(my_planets, ship)
                if closest_unfilled:
                    missions[ship.id] = AttackMission(
                        closest_unfilled, ship.id)
                    ship_command = missions[ship.id].get_command(
                        game_map, ship, enemy_planets, missions)
                elif non_taken_planets:
                    ship_command = attack_mission_command(non_taken_planets, ship, missions)
                else:
                    ship_command = attack_mission_command(enemy_planets, ship, missions)
            elif ship.id % 3 == 0:
                ship_command = ship_attack_mission_command(all_enemy_ships, ship, missions, my_planets)
            elif ship.id not in missions.keys():
                ship_command = attack_mission_command(enemy_planets, ship, missions)
            logging.info("{} {}".format(ship_command, ship))
            if ship_command:
                command_queue.append(ship_command)
                # Send our set of commands to the Halite engine for this turn
            else:
                logging.info("NO ship command")
        game.send_command_queue(command_queue)
    # TURN END
# GAME END
