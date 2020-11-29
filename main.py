"""
BY ANONYMOUS MELILLA
"""
import sys
import math

from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Tuple

# Action handling funcions
current_buffer = ""

def add_action(line):
    global current_buffer
    if current_buffer is not "":
        current_buffer += ";"
    current_buffer += line

def wait():
    add_action("WAIT")

def move(source, destination, cyborg_count):
    add_action("MOVE " + str(source) + " " + str(destination) + " " + str(cyborg_count))

def bomb(source, destination):
    add_action("BOMB " + str(source) + " " + str(destination))

def inc(factory):
    add_action("INC " + str(factory))

def send_buffer():
    global current_buffer
    print(current_buffer)
    current_buffer = ""


def enum(**enums):
    return type('Enum', (), enums)


Player          = enum(ALLY = 1,            OPPONENT = -1, NEUTRAL = 0)
ProductionLevel = enum(NONE = 0,            LOW = 1,       MEDIUM = 2, HIGH = 3)
EntityType      = enum(FACTORY = "FACTORY", TROOP = "TROOP")


@dataclass
class Entity:
    entity_id: int
    owner:     int = Player.NEUTRAL


@dataclass
class Factory(Entity):
    n_cyborgs:        int       = 0
    production_level: int       = 0
    l_attacking:      List[Tuple] = field(default_factory=lambda: [])  
    l_defending:      List[Tuple] = field(default_factory=lambda: [])  
    distances:        List[int] = field(default_factory=lambda: [])


@dataclass
class GameStatus:
    factory_count: int
    link_count:    int
    factories:     List[Factory]   = field(default_factory=lambda: [])
    entity_count:  int             = 0


@dataclass
class Troop(Entity):
    origin:      Factory = field(default_factory=lambda: None)
    destination: Factory = field(default_factory=lambda: None)
    n_cyborgs:   int     = 0
    distance:    int     = 0


def debug(* values: object):
    print(values, file=sys.stderr, flush=True) 


status = GameStatus(
    factory_count = int(input()),
    link_count    = int(input()),
    factories     = []
)


debug("Created status!")


def get_factory(factory_id):
    for factory in status.factories:
        if factory.entity_id is factory_id:
            return factory
    return None


def create_factory(factory_id):
    factory = Factory(
        distances = [0] * status.factory_count,
        entity_id = factory_id
    )
    return factory


def find_factory_with_most_production(owner,other):
    result = None
    for factory in status.factories:
        if (factory.owner == owner or (len(factory.l_attacking) > 0  and factory.owner == 0))  and (result is None or result.production_level <= factory.production_level) and other is not factory and len(factory.l_defending) == 0:
            result = factory
        else:
            debug(factory)
    return result


def attacking_troops(factory):
    suma = 0
    for troops, dist in factory.l_attacking:
        suma += troops
    return suma

def defending_troops(factory):
    suma = 0
    for troops, dist in factory.l_defending:
        suma += troops
    return suma

def find_nearest_factory(target_id, *owners):	
    result = None	
    for factory in status.factories:	
        if factory.owner in owners and (result is None or result.distances[target_id] > factory.distances[target_id]):	
            result = factory
    return result


# Surprise bomb strategy
available_bombs = 2
bomb_turn = 3
target_factories = [None, None]

def prepare_bomb(target_id=None):
    global turn
    global target_factories
    if target_id is None: 
        target_factories[0] = find_factory_with_most_production(Player.OPPONENT,None)
    else:
        target_factory =find_factory_with_most_production(Player.OPPONENT,target_factories[0])
        if target_factories[1] is None or target_factory.production_level > target_factories[1].production_level:
            target_factories[1] = target_factory
    debug(target_factories)


def send_bombs():
    global target_factories
    global available_bombs
    for target in target_factories:
        if target is not None and available_bombs > 0:
            source = find_nearest_factory(target.entity_id, Player.ALLY)
            available_bombs -= 1
            bomb(source.entity_id, target.entity_id)


def send_settlers():
    global target_factories
    for target in target_factories:
        debug(target)
        if target is not None:
            source = find_nearest_factory(target.entity_id, Player.ALLY)
            move(source.entity_id, target.entity_id, 1)

turn = 1

for i in range(status.link_count):
    factory_id1, factory_id2, distance = [int(token) for token in input().split()]
    factory1 = get_factory(factory_id1)
    factory2 = get_factory(factory_id2)
    if factory1 is None:
        factory1 = create_factory(factory_id1)
        status.factories.append(factory1)
    if factory2 is None:
        factory2 = create_factory(factory_id2)
        status.factories.append(factory2)
    factory1.distances[factory2.entity_id], factory2.distances[factory1.entity_id] = distance, distance

debug("Finished init!")

def best_choice(origen, attack, distances):
    best = 0
    best_node = origen
    for node in range(len(distances)):
        factory = get_factory(node)
        # No és l'origen
        extra = 0
        if factory.owner == Player.OPPONENT:
            extra = distances[node]*factory.production_level
        if distances[node] != 0 and factory.n_cyborgs + extra  < attack and factory.owner is not Player.ALLY:
            new = (factory.production_level)/(distances[node]*0.1 + (factory.n_cyborgs + 1))
            if new > best:
                best = new
                best_node = node

    return best_node

def n_hold(l_attacking, factory):
    attacking = factory.l_attacking
    attacking.sort(key=lambda x : x[1])
    extra_troops = 1

    if len(attacking) != 0:
        extra_troops = 0
        current_dist = -1
        current_troops = [0] * ((attacking[-1])[1])
        for n_troop, distance in attacking:
            if current_dist != distance:
                current_dist = distance
                current_troops[distance-1] = n_troop
            else:
                current_troops[distance-1] += n_troop
        
        for total_troops in current_troops:
            extra_troops += factory.production_level - total_troops       
    return extra_troops


# Autoupgrader
def auto_upgrade():
    for factory in status.factories:
        if factory.production_level != ProductionLevel.HIGH and n_hold(factory.l_attacking,factory) > 22 and factory.owner == Player.ALLY:
            inc(factory.entity_id)


# game loop
while True:
    l_attacking = list()
    status.entity_count = int(input())  # the number of entities (e.g. factories and troops)
    
    if turn is 4:
        send_settlers()
    if turn > 4:
        auto_upgrade()
    for i in range(status.entity_count):
        inputs = input().split()
        entity_id = int(inputs[0])
        entity_type = inputs[1]
        arg_1 = int(inputs[2])
        arg_2 = int(inputs[3])
        arg_3 = int(inputs[4])
        arg_4 = int(inputs[5])
        arg_5 = int(math.floor(float(inputs[6])))

        if entity_type == EntityType.FACTORY:
            factory = get_factory(entity_id)
            factory.owner = arg_1
            factory.n_cyborgs = arg_2
            factory.production_level = arg_3
            (factory.l_attacking).clear()
            factory.l_defending.clear()

        elif entity_type == EntityType.TROOP and arg_1 == Player.OPPONENT:
            get_factory(arg_3).l_attacking.append((arg_4,arg_5))
        elif entity_type == EntityType.TROOP and arg_1 == Player.ALLY:
            get_factory(arg_3).l_defending.append((arg_4,arg_5))
        
    if turn == bomb_turn:
        prepare_bomb()
        prepare_bomb(0)
            
    for factory in status.factories:
        if(factory.owner == Player.ALLY):
            extra_troops = n_hold(factory.l_attacking, factory)
            troops_to_hold = 1
            if extra_troops <= 0:
                troops_to_hold = abs(extra_troops)
            
            node_to_move = best_choice(
                factory.entity_id,
                factory.n_cyborgs - troops_to_hold,
                factory.distances
            )
            if node_to_move != factory.entity_id and turn > 4 and factory.distances[node_to_move] < 10:
                move(
                    factory.entity_id,
                    node_to_move,
                    factory.n_cyborgs - troops_to_hold
                )
            elif node_to_move != factory.entity_id and turn != 3 and node_to_move:
                move(
                    factory.entity_id,
                    node_to_move,
                    factory.n_cyborgs - 2
                )
    
    if turn is bomb_turn:
        send_bombs()
        if available_bombs > 0:
            bomb_turn += 2

    if(current_buffer == ""):
        wait()
    
    turn += 1

    send_buffer()
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr, flush=True)
