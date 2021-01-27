import math
from mcapi import *
from org.bukkit import GameMode

################## SEARCHES ##################

import re
from java.lang import Class, ClassLoader, Thread, Throwable
from java.util import ArrayList, List

def classes(s):
    """
    Searches for class names including the given string.

    :param s: String fragment to match in class names.
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

def pov(player=None, world=None):
    return Perspective(player, world)

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

class Perspective:
    def __init__(self, player=None, world=None):
        self.player = player
        self._world = world
        self.mark_points = {}
        self.mark()

    ################# ACCESSORS ##################

    def world(self):
        return self._world if self._world else self.player.world

    def location(self, *args):
        if len(args) == 0:
            return self.player.getLocation()
        if len(args) == 1:
            return args[0].getLocation()
        return Location(self.world(), *args)

    def lookingat(self, distance=100):
        return lookingat(self.player, distance)

    ################# GAME MODES #################

    def creative(self, player):
        self.player.gameMode = GameMode.CREATIVE

    def survival(self, player):
        self.player.gameMode = GameMode.SURVIVAL

    #################### TIME ####################

    # NB: 24000 ticks per cycle.

    @synchronous()
    def time(self, time=None):
        if time is None:
            return self.world().getTime()
        self.world().setTime(time)

    def dawn(self):
        self.time(22500)

    def morning(self):
        self.time(0)

    def noon(self):
        self.time(6000)

    def dusk(self):
        self.time(12500)

    def night(self):
        self.time(14000)

    ################## WEATHER ###################

    @synchronous()
    def weather(self, raining=False, thunder=False):
        self.world().setStorm(raining)
        self.world().setThundering(thunder)

    def sun(self):
        self.weather(raining=False, thunder=False)

    def rain(self):
        self.weather(raining=True, thunder=False)

    def storm(self):
        self.weather(raining=True, thunder=True)

    ################## VIOLENCE ##################

    @synchronous()
    def bolt(*args, **kwargs):
        r = parseargswithpos(args, kwargs)
        return self.world().strikeLightning(location(r['x'], r['y'], r['z']))

    @synchronous()
    def explosion(*args, **kwargs):
        r = parseargswithpos(args, kwargs, ledger={'power':['power', 0, 8]})
        return self.world().createExplosion(r['x'], r['y'], r['z'], r['power'], True)

    def zap(self):
        self.bolt(lookingat())

    def boom(self, power=3):
        self.explosion(lookingat(), power)

    ################## POSITION ##################

    @synchronous()
    def teleport(self, *args, **kwargs):
        r = parseargswithpos(args, kwargs, ledger={'whom':['whom', 0, None]})
        if not r['whom']:
            r['whom'] = self.player.getName()
        someone = player(r['whom'])
        someone.teleport(self.location(r['x'], r['y'], r['z']))

    def x(self):
        return int(round(self.player.location.x))

    def y(self):
        return int(round(self.player.location.y))

    def z(self):
        return int(round(self.player.location.z))

    def pos(self):
        return [self.x(), self.y(), self.z()]

    ################## MOVEMENT ##################

    def up(self, amount=1):
        self.teleport(self.x(), self.y() + amount, self.z())

    def down(self, amount=1):
        self.teleport(self.x(), self.y() - amount, self.z())

    def north(self, amount=1):
        self.teleport(self.x() - amount, self.y(), self.z())

    def south(self, amount=1):
        self.teleport(self.x() + amount, self.y(), self.z())

    def east(self, amount=1):
        self.teleport(self.x(), self.y(), self.z() - amount)

    def west(self, amount=1):
        self.teleport(self.x(), self.y(), self.z() + amount)

    def mark(self, label=None, pos=None):
        """
        Store the specified position with the given label.
        """
        self.mark_points[label] = pos if pos else self.pos()

    def reset(self, label=None):
        """
        Go to the point marked with the given label.
        """
        self.teleport(self.mark_points[label])

    ################## CREATION ##################

    def spawn(self, entitytype):
        safe_entity = entity(entitytype)
        if safe_entity is None:
            raise Exception('Unknown entity type: ' + str(entitytype))
            return
        return self._spawn(lookingat().location, safe_entity)

    @synchronous()
    def _spawn(self, location, entitytype):
        return self.world().spawnEntity(location, entitytype)

    def block(self, blocktype):
        self.blocks(blocktype, 0, 0, 0)

    def platform(self, blocktype=None, xradius=3, zradius=3):
        self.blocks(blocktype, xradius, 0, zradius)

    def blocks(self, blocktype=None, xradius=3, yradius=3, zradius=3):
        if blocktype is None:
            safe_blocktype = self.lookingat().type
        else:
            safe_blocktype = material(blocktype)
        if safe_blocktype is None:
            raise Exception('Unknown material type: ' + str(blocktype))
            return
        self._blocks(safe_blocktype, lookingat().location, xradius, yradius, zradius)

    @synchronous()
    def _blocks(self, block_material, location, xradius, yradius, zradius):
        irange = lambda a, b: range(int(math.floor(a)), int(math.floor(b + 1)))
        for x in irange(location.x - xradius, location.x + xradius):
            for y in irange(location.y - yradius, location.y + yradius):
                for z in irange(location.z - zradius, location.z + zradius):
                    self.world().getBlockAt(x, y, z).type = block_material

    @synchronous()
    def fill(self, pos, blocktype, srctype=None, maxdepth=20):
        """
        Flood fills an area of one block type to a different type.
        """
        if srctype is None:
            srctype = self.world().getBlockAt(pos[0], pos[1], pos[2]).type
        _fill(pos, material(blocktype), material(srctype), 0, maxdepth)

    def _fill(self, pos, blocktype, srctype, depth, maxdepth):
        if depth >= maxdepth:
            return
        px = pos[0]
        py = pos[1]
        pz = pos[2]
        block = self.world().getBlockAt(px, py, pz)
        if block.type != srctype:
            return
        block.type = blocktype
        self._fill([px+1, py, pz], blocktype, srctype, depth + 1, maxdepth)
        self._fill([px-1, py, pz], blocktype, srctype, depth + 1, maxdepth)
        self._fill([px, py, pz-1], blocktype, srctype, depth + 1, maxdepth)
        self._fill([px, py, pz+1], blocktype, srctype, depth + 1, maxdepth)
        self._fill([px, py-1, pz], blocktype, srctype, depth + 1, maxdepth)

    @synchronous()
    def transform(self, blocktype=Material.AIR):
        """
        Converts what you are looking at into a block of the given material.
        :param: blocktype The type of material your gaze shall inflict.

        Examples:
        - transform('water')
        """
        self.lookingat().type = material(blocktype)


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
