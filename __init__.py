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
    """
    Search for matching materials.
    :param s: String fragment that must appear in match material names.
    """
    return _matching_fields(s, Material.getFields())

def material(m):
    """
    Search for a matching material.

    If there are multiple matches, exact matches are preferred, followed by
    matches beginning with the given string, followed by a random match.

    :param s: String fragment that must appear in matching material's name.
    """
    return _single_match(m, Material)

def entities(s):
    """
    Search for matching materials.
    :param s: String fragment that must appear in matching entity names.
    """
    return _matching_fields(s, EntityType.getFields())

def entity(e):
    """
    Search for a matching entity.

    If there are multiple matches, exact matches are preferred, followed by
    matches beginning with the given string, followed by a random match.

    :param s: String fragment that must appear in matching entity's name.
    """
    return _single_match(e, EntityType)

def pov(player=None, world=None):
    """
    Creates a point-of-view object around the given player or world.

    Note that if you wrap a world rather than a player, some functions
    will not work, since the POV will not have an associated position.

    :param player: The player around whom to construct the point of view.
    :param world: The world around which to construct the point of view.
    """
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
    """An object encapsulating a point of view in the Minecraft universe."""

    def __init__(self, player=None, world=None):
        """
        Constructs a perspective around the given player or world.

        If only a player is given, the player's current world is used for
        world-specific commands. If only a world is given, the perspective will
        lack specific coordinates; commands requiring a player will not work.

        :param player: The player to wrap.
        :param world: The world to wrap.
        """
        self.player = player
        self._world = world
        self.mark_points = {}
        self.mark()

    ################# ACCESSORS ##################

    def world(self):
        """
        Gets the perspective's current world. Typically, this means the
        world in which the perspective's linked player currently resides.
        """
        return self._world if self._world else self.player.world

    def location(self, *args):
        """
        Gets the perspective's current location. Typically, this
        is the location of the perspective's linked player.
        """
        if len(args) == 0:
            return self.player.getLocation()
        if len(args) == 1:
            return args[0].getLocation()
        return Location(self.world(), *args)

    def lookingat(self, distance=100):
        """
        Gets the block the linked player is currently looking at.

        :param distance: The maximum distance of the looked-at block.
        """
        return lookingat(self.player, distance)

    def x(self):
        """Gets the linked player's X coordinate."""
        return int(round(self.player.location.x))

    def y(self):
        """Gets the linked player's Y coordinate."""
        return int(round(self.player.location.y))

    def z(self):
        """Gets the linked player's Z coordinate."""
        return int(round(self.player.location.z))

    def pos(self):
        """Gets the linked player's location as an [X, Y, Z] triple."""
        return [self.x(), self.y(), self.z()]

    ################# GAME MODES #################

    def creative(self, player):
        """Sets the linked player to creative mode."""
        self.player.gameMode = GameMode.CREATIVE

    def survival(self, player):
        """Sets the linked player to survival mode."""
        self.player.gameMode = GameMode.SURVIVAL

    #################### TIME ####################

    # NB: 24000 ticks per cycle.

    @synchronous()
    def time(self, time=None):
        """
        Gets or sets the time of the current world.

        :param time: If passed, changes the time to the given value.
                     There are 24000 ticks per daily cycle.
                     Some reference points:
                     - 0 = Morning
                     - 6000 = Noon
                     - 12500 = Dusk
                     - 14000 = Night
                     - 22500 = Dawn
        """
        if time is None:
            return self.world().getTime()
        self.world().setTime(time)

    def dawn(self):
        """Sets the time of the current world to early morning."""
        self.time(22500)

    def morning(self):
        """Sets the time of the current world to morning."""
        self.time(0)

    def noon(self):
        """Sets the time of the current world to midday."""
        self.time(6000)

    def dusk(self):
        """Sets the time of the current world to dusk."""
        self.time(12500)

    def night(self):
        """Sets the time of the current world to night."""
        self.time(14000)

    ################## WEATHER ###################

    @synchronous()
    def weather(self, raining=False, thunder=False):
        """
        Changes the weather of the current world.

        :param raining: If true, will be raining.
        :param thunder: If true, will be storming.
        """
        self.world().setStorm(raining)
        self.world().setThundering(thunder)

    def sun(self):
        """Sets the current world to sunny weather."""
        self.weather(raining=False, thunder=False)

    def rain(self):
        """Sets the current world to rainy weather."""
        self.weather(raining=True, thunder=False)

    def storm(self):
        """Sets the current world to stormy weather."""
        self.weather(raining=True, thunder=True)

    ################## VIOLENCE ##################

    @synchronous()
    def bolt(*args, **kwargs):
        """
        Drops a lightning bolt in the given location of the current world.

        :param x: X coordinate of the lightning bolt.
        :param y: Y coordinate of the lightning bolt.
        :param z: Z coordinate of the lightning bolt.
        """
        r = parseargswithpos(args, kwargs)
        return self.world().strikeLightning(self.location(r['x'], r['y'], r['z']))

    @synchronous()
    def explosion(*args, **kwargs):
        """
        Makes an explosion in the given location of the current world.

        :param power: Radius of the explosion.
        :param x: X coordinate of the explosion.
        :param y: Y coordinate of the explosion.
        :param z: Z coordinate of the explosion.
        """
        r = parseargswithpos(args, kwargs, ledger={'power':['power', 0, 8]})
        return self.world().createExplosion(r['x'], r['y'], r['z'], r['power'], True)

    def zap(self):
        """
        Drops a lightning bolt where the linked player is currently looking.
        """
        self.bolt(lookingat())

    def boom(self, power=3):
        """
        Makes an explosion where the linked player is currently looking.

        :param power: Radius of the explosion (default 3).
        """
        self.explosion(lookingat(), power)

    ################## MOVEMENT ##################

    @synchronous()
    def teleport(self, *args, **kwargs):
        """
        Teleports the specified player (or linked player) to the given position.
        If the player is on a different world, that world's coordinates will be
        used -- i.e., this function won't teleport someone between worlds.

        :param whom: Person to be teleported (default is the linked player).
        :param x: X coordinate of teleport destination.
        :param y: Y coordinate of teleport destination.
        :param z: Z coordinate of teleport destination.
        """
        r = parseargswithpos(args, kwargs, ledger={'whom':['whom', 0, None]})
        if not r['whom']:
            r['whom'] = self.player.getName()
        someone = player(r['whom'])
        someone.teleport(self.location(r['x'], r['y'], r['z']))

    def up(self, amount=1):
        """
        Teleports the linked player upward by the given amount.
        :param amount: Number of cubes upward to teleport.
        """
        self.teleport(self.x(), self.y() + amount, self.z())

    def down(self, amount=1):
        """
        Teleports the linked player downward by the given amount.
        :param amount: Number of cubes downward to teleport.
        """
        self.teleport(self.x(), self.y() - amount, self.z())

    def north(self, amount=1):
        """
        Teleports the linked player northward by the given amount.
        :param amount: Number of cubes northward to teleport.
        """
        self.teleport(self.x() - amount, self.y(), self.z())

    def south(self, amount=1):
        """
        Teleports the linked player southward by the given amount.
        :param amount: Number of cubes southward to teleport.
        """
        self.teleport(self.x() + amount, self.y(), self.z())

    def east(self, amount=1):
        """
        Teleports the linked player eastward by the given amount.
        :param amount: Number of cubes eastward to teleport.
        """
        self.teleport(self.x(), self.y(), self.z() - amount)

    def west(self, amount=1):
        """
        Teleports the linked player westward by the given amount.
        :param amount: Number of cubes westward to teleport.
        """
        self.teleport(self.x(), self.y(), self.z() + amount)

    def mark(self, label=None, pos=None):
        """
        Remembers the specified position with the given label.
        :param label: The name of the point to remember.
        :param pos: The position to remember (default current position).
        """
        self.mark_points[label] = pos if pos else self.pos()

    def reset(self, label=None):
        """
        Teleports to the point marked with the given label.
        :param label: The name of the point to teleport back to.
        """
        self.teleport(self.mark_points[label])

    ################## CREATION ##################

    def spawn(self, entitytype):
        """
        Creates an entity of the given type where
        the linked player is currently looking.

        :param entitytype: The type of entity to spawn.
        """
        safe_entity = entity(entitytype)
        if safe_entity is None:
            raise Exception('Unknown entity type: ' + str(entitytype))
            return
        return self._spawn(self.lookingat().location, safe_entity)

    @synchronous()
    def _spawn(self, location, entitytype):
        return self.world().spawnEntity(location, entitytype)

    def block(self, blocktype):
        """
        Assigns a block of the given type where
        the linked player is currently looking.

        :param blocktype: The type of block to assign.
        """
        self.cuboid(blocktype, 0, 0, 0)

    def platform(self, blocktype=None, xradius=3, zradius=3):
        """
        Creates a platform of the given type and specified radiuses,
        centered where the linked player is currently looking.

        :param blocktype: The type of block the platform will be made of.
        :param xradius: The platform's radius along the X axis.
        :param zradius: The platform's radius along the Z axis.
        """
        self.cuboid(blocktype, xradius, 0, zradius)

    def cuboid(self, blocktype=None, xradius=3, yradius=3, zradius=3):
        """
        Creates a cuboid of the given type and specified radiuses,
        centered where the linked player is currently looking.

        :param blocktype: The type of block the cuboid will be made of.
        :param xradius: The cuboid's radius along the X axis.
        :param yradius: The cuboid's radius along the Y axis.
        :param zradius: The cuboid's radius along the Z axis.
        """
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

        :param pos:
        :param blocktype:
        :param srctype:
        :param maxdepth:
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

        Example: transform('water')

        :param: blocktype The type of material your gaze shall inflict.
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
