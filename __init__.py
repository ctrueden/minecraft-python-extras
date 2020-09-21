from mcapi import *

################# CONTAINERS #################

#class Region(object):
#    def __init__(self):
#        pass
#    def pos():
# Region is a collection of blocks
# Region is iterable

# Player is a 1-block Region aligned with a player's position.
# Box is an WxHxD Region.
# FloodFilled Region? With/without bounds?
# Support for composite Regions? (and/or)
# Other Regions are possible.

################# GAME MODES #################

from org.bukkit import GameMode

def creative(player=None):
    if player is None: player = player()
    player.gameMode = GameMode.CREATIVE

def survival(player=None):
    if player is None: player = player()
    player.gameMode = GameMode.SURVIVAL

#################### TIME ####################

# NB: 24000 ticks per cycle.

def dawn():
    time(22500)

def morning():
    time(0)

def noon():
    time(6000)

def dusk():
    time(12500)

def night():
    time(14000)

################## WEATHER ###################

def sun():
    weather(False, False)

def rain():
    weather(True, False)

def storm():
    weather(True, True)

################## VIOLENCE ##################

def zap():
    bolt(lookingat())

def boom(power=3):
    explosion(lookingat(), power)

################## POSITION ##################

def x(pl=None):
    if pl is None: pl = player()
    return int(round(pl.location.x))

def y(pl=None):
    if pl is None: pl = player()
    return int(round(pl.location.y))

def z(pl=None):
    if pl is None: pl = player()
    return int(round(pl.location.z))

def pos(pl=None):
    if pl is None: pl = player()
    return [x(pl), y(pl), z(pl)]

################## MOVEMENT ##################

def up(amount=1):
    teleport(x(), y() + amount, z())

def down(amount=1):
    teleport(x(), y() - amount, z())

def north(amount=1):
    teleport(x() - amount, y(), z())

def south(amount=1):
    teleport(x() + amount, y(), z())

def east(amount=1):
    teleport(x(), y(), z() - amount)

def west(amount=1):
    teleport(x(), y(), z() + amount)

reset_point = None

def mark():
    global reset_point
    reset_point = pos()

# go back to reset point
def reset():
    if reset_point:
        teleport(reset_point)

################## CREATION ##################

def spawn(entitytype):
    safe_entity = entity(entitytype)
    if safe_entity is None:
        raise Exception('Unknown entity type: ' + str(entitytype))
        return
    return _spawn(lookingat().location, safe_entity)

@synchronous()
def _spawn(location, entitytype):
    return WORLD.spawnEntity(location, entitytype)

def block(blocktype):
    blocks(0, 0, 0, blocktype)

def platform(blocktype=None, xradius=3, zradius=3):
    blocks(blocktype, xradius, 0, zradius)

def blocks(blocktype=None, xradius=3, yradius=3, zradius=3):
    safe_blocktype = material(blocktype)
    if safe_blocktype is None:
        raise Exception('Unknown material type: ' + str(blocktype))
        return
    _blocks(safe_blocktype, lookingat().location, xradius, yradius, zradius)

@synchronous()
def _blocks(block_material, location, xradius, yradius, zradius):
    for x in range(location.x - xradius, location.x + xradius + 1):
        for y in range(location.y - yradius, location.y + yradius + 1):
            for z in range(location.z - zradius, location.z + zradius + 1):
                WORLD.getBlockAt(x, y, z).type = block_material

@synchronous()
def fill(pos, blocktype, srctype=None, maxdepth=20):
    """
    Flood fills an area of one block type to a different type.
    """
    if srctype is None:
        srctype = WORLD.getBlockAt(pos[0], pos[1], pos[2]).type
    _fill(pos, material(blocktype), material(srctype), 0, maxdepth)

def _fill(pos, blocktype, srctype, depth, maxdepth):
    if depth >= maxdepth:
        return
    px = pos[0] 
    py = pos[1] 
    pz = pos[2] 
    block = WORLD.getBlockAt(px, py, pz)
    if block.type != srctype:
        return
    block.type = blocktype
    _fill([px+1, py, pz], blocktype, srctype, depth + 1, maxdepth)
    _fill([px-1, py, pz], blocktype, srctype, depth + 1, maxdepth)
    _fill([px, py, pz-1], blocktype, srctype, depth + 1, maxdepth)
    _fill([px, py, pz+1], blocktype, srctype, depth + 1, maxdepth)
    _fill([px, py-1, pz], blocktype, srctype, depth + 1, maxdepth)

################## SEARCHES ##################

import re
from java.lang import ClassLoader, Thread, Throwable
from java.util import ArrayList, List

def classes(s):
    """
    Searches for class names including the given string.
    """
    # HACK: Obtain the list of all classes loaded by the current class loader.
    # Maybe this is not ideal, because it won't find classes that have not
    # yet been loaded. Perhaps we should dig through all the JAR files...
    class_loader = Thread.currentThread().getContextClassLoader()
    classes_list = []
    try:
        classes_field = ClassLoader.getDeclaredField("classes")
        classes_field.setAccessible(True)
        # NB: Copy the list, to avoid ConcurrentModificationException.
        classes_list = ArrayList(classes_field.get(class_loader))
    except Throwable, t:
        t.printStackTrace()
    # NB: Iterate longhand, to try/except each element access.
    result = []
    for i in range(0, len(classes_list)):
        try:
            c = classes_list[i]
            if hasattr(c, 'name') and re.match(s, c.name):
                result.append(c)
        except:
            # NB: Ignore class loading exceptions e.g. NoClassDefFoundError.
            #t.printStackTrace()
            pass
    return result

from java.lang import Class

def funcs(obj):
    """
    Prints the functions the given object possesses.
    :param: obj The object to dissect.

    Examples:
    - funcs(player())
    - funcs(lookingat())
    - funcs(WORLD)
    - funcs(SERVER)
    """
    c = obj if isinstance(obj, Class) else obj.getClass()
    print(c.getPackage().getName() + "." + obj.getClass().getSimpleName() + ':')
    methods = set()
    for m in obj.getClass().getMethods():
        try:
            methods.add(m.getName() + "(" + ', '.join([p.getType().getSimpleName() for p in m.getParameters()]) + ")")
        except:
            methods.add(m.getName() + "(?)")
    for m in methods:
        print("- " + m)

@synchronous()
def transform(blocktype=Material.AIR):
    """
    Converts what you are looking at into a block of the given material.
    :param: blocktype The type of material your gaze shall inflict.

    Examples:
    - transform('water')
    """
    lookingat().type = material(blocktype)

def _matching_fields(s, fields):
    results = []
    for field in fields:
        if s.upper() in field.name:
            results.append(field.get(None))
    return results

def _single_match(v, clazz):
    if isinstance(v, clazz):
        return v
    results = _matching_fields(v, clazz.getFields())
    if not results: return None
    # Return an exact match first.
    exact = list(filter(lambda x: x.name().startswith(v), results))
    if exact: return choice(exact)
    # Return a match with same leading string if any.
    leading = list(filter(lambda x: x.name().startswith(v), results))
    if leading: return choice(leading)
    # Return anything!
    return choice(results)

def materials(s):
    return _matching_fields(s, Material.getFields())

def material(m):
    return _single_match(m, Material)

def entities(s):
    return _matching_fields(s, EntityType.getFields())

def entity(e):
    return _single_match(e, EntityType)

# FIND OBJECTS
#def findblock(pos, blocktype, maxradiusx=50, maxradiusy=50, maxradiusz=50):
#    """
#    Locates the nearest block of a particular type.
#    """
#    return WORLD.getBlockAt(r['x'], r['y'], r['z'])

################### IDEAS ####################

# 3D Python turtle
# copy/paste blocks of reality
# generate mathematical structures
# generate structures matching images
# dropping items
# spawning creatures
