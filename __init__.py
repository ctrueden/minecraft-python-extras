import collections, math
from mcapi import *
from df_maze import Maze

from java.awt.image import BufferedImage
from java.io import File
from java.net import URL
from javax.imageio import ImageIO
from org.bukkit import GameMode

################## UTILITY ###################

def sign(n):
    if n == 0: return 0
    return 1 if n > 0 else -1

############## BLOCK ITERATION ###############

def airy(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.AIR or \
           t == Material.CAVE_AIR or \
           t == Material.VOID_AIR

def watery(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.WATER

def airorwater(block):
    return airy(block) or watery(block)

def grassy(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.GRASS_BLOCK

def planty(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.GRASS or \
           t == Material.TALL_GRASS or \
           t == Material.AZURE_BLUET or \
           t == Material.CORNFLOWER or \
           t == Material.DANDELION or \
           t == Material.OXEYE_DAISY or \
           t == Material.POPPY

def dirty(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.GRASS_BLOCK or \
           t == Material.DIRT or \
           t == Material.COARSE_DIRT

def stony(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.STONE or \
           t == Material.COBBLESTONE or \
           t == Material.GRANITE or \
           t == Material.ANDESITE or \
           t == Material.DIORITE

def sandy(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.SAND or \
           t == Material.SANDSTONE

def glowing(block):
    t = block.type if hasattr(block, 'type') else block
    return t == Material.TORCH or \
           t == Material.GLOWSTONE or \
           t == Material.SEA_LANTERN or \
           t == Material.LANTERN or \
           t == Material.REDSTONE_LAMP

class LocationQueue:
    def __init__(self, origin, limit):
        self.origin = origin
        self.limit = limit
        self.visited = {}
        self.pending = collections.deque()
        self.push(origin.x, origin.y, origin.z)

    def push(self, x, y, z):
        p = (x, y, z)
        dist = abs(self.origin.x - x) + \
               abs(self.origin.y - y) + \
               abs(self.origin.z - z)
        if dist <= self.limit and not p in self.visited:
            self.visited[p] = True
            self.pending.append(p)

    def pop(self):
        return self.pending.popleft()

    def __nonzero__(self):
        return bool(self.pending)

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

################### COLORS ###################

color_values = [
    [  0,   0,   0], # black
    [  0,   0, 255], # blue
    [160,  48,  48], # brown
    [  0, 128, 128], # cyan
    [ 85,  85,  85], # gray
    [  0, 255,   0], # green
    [  0, 255, 255], # light blue
    [171, 171, 171], # light gray
    [128, 255, 128], # lime
    [255,   0, 255], # magenta
    [255, 128,   0], # orange
    [255, 192, 192], # pink
    [128,   0, 128], # purple
    [255,   0,   0], # red
    [255, 255, 255], # white
    [255, 255,   0]  # yellow
]

color_materials = {
    'carpet': [
        Material.BLACK_CARPET,
        Material.BLUE_CARPET,
        Material.BROWN_CARPET,
        Material.CYAN_CARPET,
        Material.GRAY_CARPET,
        Material.GREEN_CARPET,
        Material.LIGHT_BLUE_CARPET,
        Material.LIGHT_GRAY_CARPET,
        Material.LIME_CARPET,
        Material.MAGENTA_CARPET,
        Material.ORANGE_CARPET,
        Material.PINK_CARPET,
        Material.PURPLE_CARPET,
        Material.RED_CARPET,
        Material.WHITE_CARPET,
        Material.YELLOW_CARPET
    ],
    'concrete': [
        Material.BLACK_CONCRETE,
        Material.BLUE_CONCRETE,
        Material.BROWN_CONCRETE,
        Material.CYAN_CONCRETE,
        Material.GRAY_CONCRETE,
        Material.GREEN_CONCRETE,
        Material.LIGHT_BLUE_CONCRETE,
        Material.LIGHT_GRAY_CONCRETE,
        Material.LIME_CONCRETE,
        Material.MAGENTA_CONCRETE,
        Material.ORANGE_CONCRETE,
        Material.PINK_CONCRETE,
        Material.PURPLE_CONCRETE,
        Material.RED_CONCRETE,
        Material.WHITE_CONCRETE,
        Material.YELLOW_CONCRETE
    ],
    'glass': [
        Material.BLACK_STAINED_GLASS,
        Material.BLUE_STAINED_GLASS,
        Material.BROWN_STAINED_GLASS,
        Material.CYAN_STAINED_GLASS,
        Material.GRAY_STAINED_GLASS,
        Material.GREEN_STAINED_GLASS,
        Material.LIGHT_BLUE_STAINED_GLASS,
        Material.LIGHT_GRAY_STAINED_GLASS,
        Material.LIME_STAINED_GLASS,
        Material.MAGENTA_STAINED_GLASS,
        Material.ORANGE_STAINED_GLASS,
        Material.PINK_STAINED_GLASS,
        Material.PURPLE_STAINED_GLASS,
        Material.RED_STAINED_GLASS,
        Material.WHITE_STAINED_GLASS,
        Material.YELLOW_STAINED_GLASS
    ],
    'glazed': [
        Material.BLACK_GLAZED_TERRACOTTA,
        Material.BLUE_GLAZED_TERRACOTTA,
        Material.BROWN_GLAZED_TERRACOTTA,
        Material.CYAN_GLAZED_TERRACOTTA,
        Material.GRAY_GLAZED_TERRACOTTA,
        Material.GREEN_GLAZED_TERRACOTTA,
        Material.LIGHT_BLUE_GLAZED_TERRACOTTA,
        Material.LIGHT_GRAY_GLAZED_TERRACOTTA,
        Material.LIME_GLAZED_TERRACOTTA,
        Material.MAGENTA_GLAZED_TERRACOTTA,
        Material.ORANGE_GLAZED_TERRACOTTA,
        Material.PINK_GLAZED_TERRACOTTA,
        Material.PURPLE_GLAZED_TERRACOTTA,
        Material.RED_GLAZED_TERRACOTTA,
        Material.WHITE_GLAZED_TERRACOTTA,
        Material.YELLOW_GLAZED_TERRACOTTA
    ],
    'pane': [
        Material.BLACK_STAINED_GLASS_PANE,
        Material.BLUE_STAINED_GLASS_PANE,
        Material.BROWN_STAINED_GLASS_PANE,
        Material.CYAN_STAINED_GLASS_PANE,
        Material.GRAY_STAINED_GLASS_PANE,
        Material.GREEN_STAINED_GLASS_PANE,
        Material.LIGHT_BLUE_STAINED_GLASS_PANE,
        Material.LIGHT_GRAY_STAINED_GLASS_PANE,
        Material.LIME_STAINED_GLASS_PANE,
        Material.MAGENTA_STAINED_GLASS_PANE,
        Material.ORANGE_STAINED_GLASS_PANE,
        Material.PINK_STAINED_GLASS_PANE,
        Material.PURPLE_STAINED_GLASS_PANE,
        Material.RED_STAINED_GLASS_PANE,
        Material.WHITE_STAINED_GLASS_PANE,
        Material.YELLOW_STAINED_GLASS_PANE
    ],
    'powder': [
        Material.BLACK_CONCRETE_POWDER,
        Material.BLUE_CONCRETE_POWDER,
        Material.BROWN_CONCRETE_POWDER,
        Material.CYAN_CONCRETE_POWDER,
        Material.GRAY_CONCRETE_POWDER,
        Material.GREEN_CONCRETE_POWDER,
        Material.LIGHT_BLUE_CONCRETE_POWDER,
        Material.LIGHT_GRAY_CONCRETE_POWDER,
        Material.LIME_CONCRETE_POWDER,
        Material.MAGENTA_CONCRETE_POWDER,
        Material.ORANGE_CONCRETE_POWDER,
        Material.PINK_CONCRETE_POWDER,
        Material.PURPLE_CONCRETE_POWDER,
        Material.RED_CONCRETE_POWDER,
        Material.WHITE_CONCRETE_POWDER,
        Material.YELLOW_CONCRETE_POWDER],
    'terracotta': [
        Material.BLACK_TERRACOTTA,
        Material.BLUE_TERRACOTTA,
        Material.BROWN_TERRACOTTA,
        Material.CYAN_TERRACOTTA,
        Material.GRAY_TERRACOTTA,
        Material.GREEN_TERRACOTTA,
        Material.LIGHT_BLUE_TERRACOTTA,
        Material.LIGHT_GRAY_TERRACOTTA,
        Material.LIME_TERRACOTTA,
        Material.MAGENTA_TERRACOTTA,
        Material.ORANGE_TERRACOTTA,
        Material.PINK_TERRACOTTA,
        Material.PURPLE_TERRACOTTA,
        Material.RED_TERRACOTTA,
        Material.WHITE_TERRACOTTA,
        Material.YELLOW_TERRACOTTA
    ],
    'wool': [
        Material.BLACK_WOOL,
        Material.BLUE_WOOL,
        Material.BROWN_WOOL,
        Material.CYAN_WOOL,
        Material.GRAY_WOOL,
        Material.GREEN_WOOL,
        Material.LIGHT_BLUE_WOOL,
        Material.LIGHT_GRAY_WOOL,
        Material.LIME_WOOL,
        Material.MAGENTA_WOOL,
        Material.ORANGE_WOOL,
        Material.PINK_WOOL,
        Material.PURPLE_WOOL,
        Material.RED_WOOL,
        Material.WHITE_WOOL,
        Material.YELLOW_WOOL
    ]
}

def colortable(name):
    return dict(zip(color_materials[name], color_values))

def _color_distance(rgb, r, g, b):
    rdist = abs(rgb[0] - r)
    gdist = abs(rgb[1] - g)
    bdist = abs(rgb[2] - b)
    return rdist ** 2 + gdist ** 2 + bdist ** 2

def _closest_material(materials, r, g, b):
    best_material = None
    best_distance = float('inf')
    for material, rgb in materials.items():
        dist = _color_distance(rgb, r, g, b)
        if dist < best_distance:
            best_distance = dist
            best_material = material
    return best_material

################ ENTRY POINT #################

def pov(who=None, world=None, where=None):
    """
    Creates a point-of-view object around the given player or world.

    Note that if you wrap a world rather than a player, some functions
    will not work, since the POV will not have an associated position.

    :param who: Name of the player around whom to construct the point of view.
    :param world: The world around which to construct the point of view.
    :param where: The location around which to construct the point of view.
    """
    who = player(who) if who else None
    return Perspective(who, world, where) if who or world or where else None

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

    def __init__(self, player=None, world=None, where=None):
        """
        Constructs a perspective around the given player, or world & location.

        If only a player is given, the player's current world and location are
        used for world-specific commands. Alternately, if a world and location
        are given, the perspective will be fixed at that point.

        :param player: The Player to wrap.
        :param world: The World to wrap.
        :param where: Location to wrap.
        """
        self._player = player
        self._world = world
        self._loc = None if self._player else self.location(where)
        self.mark_points = {}
        self.mark()

    ################# ACCESSORS ##################

    def player(self, who=None):
        """
        Looks up the player with the given name.
        :param who: The player to look up (default linked player).
        """
        if who is None:
            return self._player if hasattr(self, '_player') else None
        if type(who).__name__ == 'CraftPlayer':
            return who
        return player(who)

    def world(self):
        """
        Gets the perspective's world. For player-based perspectives, this means
        the world in which the perspective's linked player currently resides.
        """
        # TODO: add optional where param, to get world of the given place.
        return self._world if self._world else self.player().world

    def location(self, where=None, looking=False):
        """
        Gets a place's coordinates as a Location object.
        :param where: The place or thing to wrap into a Location.
                      Can be an Entity, a Location, or a position.
                      Default is the perspective's linked location,
                      or the lookingat() location if looking=True.
        :param looking: If true, changes the default from the linked
                        location to the lookingat() location.
        """
        if where is None:
            if looking:
                where = self.lookingat()
            elif hasattr(self, '_loc') and self._loc:
                where = self._loc
            else:
                where = self.player()
        if where is None:
            raise 'Perspective has no linked location'
        if isinstance(where, Location):
            return where
        if hasattr(where, 'getLocation'):
            return where.getLocation()
        if len(where) == 3:
            return Location(self.world(), where[0], where[1], where[2])
        raise 'Unknown place type: ' + str(type(where))

    def fpos(self, where=None):
        """
        Gets a place's coordinates as an [X, Y, Z] position triple
        of floating point values.

        :param where: Place whose coordinates are desired (default linked location).
        """
        loc = self.location(where)
        return [loc.x, loc.y, loc.z]

    def ipos(self, where=None):
        """
        Gets a place's coordinates as an [X, Y, Z] position triple
        of integer values.

        :param where: Place whose coordinates are needed (default linked location).
        """
        loc = self.location(where)
        return [self.ix(loc), self.iy(loc), self.iz(loc)]

    def fx(self, where=None):
        """
        Gets a place's X coordinate as a float.
        :param where Place whose X coordinate is needed (default current location).
        """
        return self.location(where).x

    def fy(self, where=None):
        """
        Gets a place's Y coordinate as a float.
        :param where Place whose Y coordinate is needed (default current location).
        """
        return self.location(where).y

    def fz(self, where=None):
        """
        Gets a place's Z coordinate as a float.
        :param where Place whose Z coordinate is needed (default current location).
        """
        return self.location(where).z

    def ix(self, where=None):
        """
        Gets a place's X coordinate as an integer.
        :param where Place whose X coordinate is needed (default current location).
        """
        loc = self.location(where)
        return int(round(self.fx(loc)))

    def iy(self, where=None):
        """
        Gets a place's Y coordinate as an integer.
        :param loc Location to convert (default current location).
        """
        loc = self.location(where)
        return int(round(self.fy(loc)))

    def iz(self, where=None):
        """
        Gets a place's Z coordinate as an integer.
        :param loc Location to convert (default current location).
        """
        loc = self.location(where)
        return int(round(self.fz(loc)))

    def lookingat(self, who=None, distance=100):
        """
        Gets the block the given player is currently looking at.
        :param who: The player whose gaze will be analyzed (default linked player).
        :param distance: The maximum distance of the looked-at block.
        """
        return lookingat(self.player(who), distance)

    ################# GAME MODES #################

    @synchronous()
    def creative(self, who=None):
        """
        Sets the given player to creative mode.
        :param who: The player to set to creative mode (default linked player).
        """
        self.player(who).gameMode = GameMode.CREATIVE

    @synchronous()
    def survival(self, who=None):
        """
        Sets the given player to survival mode.
        :param who: The player to set to creative mode (default linked player).
        """
        self.player(who).gameMode = GameMode.SURVIVAL

    #################### TIME ####################

    # NB: 24000 ticks per cycle.

    @synchronous()
    def time(self, time=None):
        """
        Gets or sets the time of the current world.

        :param time: If given, changes the time to the given value.
                     There are 24000 ticks per daily cycle:
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
    def zap(self, where=None):
        """
        Drops a lightning bolt.
        :param where: The place to drop the lightning bolt (default lookingat()).
        """
        loc = self.location(where, looking=True)
        return self.world().strikeLightning(loc)

    @synchronous()
    def boom(self, power=3, where=None):
        """
        Makes an explosion.

        :param power: Radius of the explosion (default 3).
        :param where: The place to explode (default lookingat()).
        """
        loc = self.location(where, looking=True)
        return self.world().createExplosion(loc, power, True)

    ################## MOVEMENT ##################

    @synchronous()
    def teleport(self, where=None, who=None):
        """
        Teleports the specified player (or linked player) to the given position.
        If the player is on a different world, that world's coordinates will be
        used -- i.e., this function won't teleport someone between worlds.

        :param where: The place to teleport (default lookingat()).
        :param who: Person to be teleported (default linked player).
        """
        # TODO: Tweak location by +/-1 on each axis, based on current location.
        # This would avoid being teleported inside a block and then shunted.
        # Maybe best would be a new function nextto()? But it's tricky to
        # decide which edge. We need air adjacent, and NOT air below!
        loc = self.location(where, looking=True)
        self.player(who).teleport(loc)

    def up(self, amount=1, who=None):
        """
        Teleports the linked player upward by the given amount.
        :param amount: Number of cubes upward to teleport.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport([self.fx(), self.fy() + amount, self.fz()], who)

    def down(self, amount=1, who=None):
        """
        Teleports the linked player downward by the given amount.
        :param amount: Number of cubes downward to teleport.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport([self.fx(), self.fy() - amount, self.fz()], who)

    def north(self, amount=1, who=None):
        """
        Teleports the linked player northward by the given amount.
        :param amount: Number of cubes northward to teleport.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport([self.fx(), self.fy(), self.fz() - amount], who)

    def south(self, amount=1, who=None):
        """
        Teleports the linked player southward by the given amount.
        :param amount: Number of cubes southward to teleport.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport([self.fx(), self.fy(), self.fz() + amount], who)

    def west(self, amount=1, who=None):
        """
        Teleports the linked player westward by the given amount.
        :param amount: Number of cubes westward to teleport.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport([self.fx() - amount, self.fy(), self.fz()], who)

    def east(self, amount=1, who=None):
        """
        Teleports the linked player eastward by the given amount.
        :param amount: Number of cubes eastward to teleport.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport([self.fx() + amount, self.fy(), self.fz()], who)

    def mark(self, label=None, where=None):
        """
        Remembers the specified position with the given label.
        :param label: The name of the point to remember.
        :param where: The place to remember (default linked location).
        """
        self.mark_points[label] = where or self.location()

    def reset(self, label=None, who=None):
        """
        Teleports the given player to the point marked with the given label.
        :param label: The name of the point to teleport back to.
        :param who: Person to be teleported (default linked player).
        """
        self.teleport(self.mark_points[label], who)

    ################## CREATION ##################

    def spawn(self, entitytype, where=None):
        """
        Creates an entity of the given type where
        the linked player is currently looking.

        :param entitytype: The type of entity to spawn.
        :param where: The place to spawn the entity (default lookingat()).
        """
        safe_entity = entity(entitytype)
        if safe_entity is None:
            raise Exception('Unknown entity type: ' + str(entitytype))
            return
        return self._spawn(self.location(where), safe_entity)

    @synchronous()
    def _spawn(self, loc, entitytype):
        return self.world().spawnEntity(loc, entitytype)

    def lettherebelight(self, where=None, limit=50, blocktype=Material.GLOWSTONE, minlight=7):
        """
        Fills up dark nooks with the given block type.
        """
        origin = self.location(where)

        if not airorwater(origin.block):
            return
        queue = LocationQueue(origin, limit)
        while queue:
            loc = self.location(queue.pop())
            if not airorwater(loc.block):
                continue
            n = self.location([loc.x-1, loc.y, loc.z]).block
            s = self.location([loc.x+1, loc.y, loc.z]).block
            w = self.location([loc.x, loc.y, loc.z-1]).block
            e = self.location([loc.x, loc.y, loc.z+1]).block
            u = self.location([loc.x, loc.y+1, loc.z]).block
            d = self.location([loc.x, loc.y-1, loc.z]).block
            queue.push(n.x, n.y, n.z)
            queue.push(s.x, s.y, s.z)
            queue.push(e.x, e.y, e.z)
            queue.push(w.x, w.y, w.z)
            queue.push(u.x, u.y, u.z)
            queue.push(d.x, d.y, d.z)
            if loc.block.lightLevel >= minlight:
                continue
            airs = [airorwater(n), airorwater(s), airorwater(e), airorwater(w), airorwater(u), airorwater(d)].count(True)
            if airs <= 3:
                self.block(blocktype, loc)

    def torchline(self, where=None, limit=100, torchtype=Material.TORCH, fencetype=None):
        """
        Places a line of torches along a fence line in the given location.

        :param where:
        :param limit: Default 100.
        :param torchtype: Default normal torches.
        :param fencetype: Default is the block type of the given location.
        """
        if limit < 0:
            return
        loc = self.location(where, looking=True)
        if fencetype is None:
            fencetype = loc.block.type
        u = self.location([loc.x, loc.y+1, loc.z])
        d = self.location([loc.x, loc.y-1, loc.z])
        if airy(loc.block) and loc.y >= 0:
            # we are too high -- drop down
            self.torchline(d, limit, torchtype, fencetype)
            return
        if loc.block.type != fencetype:
            # not a fence this way -- stop
            return
        if u.block.type == fencetype:
            # fence goes higher -- jump up
            self.torchline(u, limit, torchtype, fencetype)
            return
        if airy(u.block):
            # at the top of a fence -- put a torch on top
            self.block(torchtype, u)
            # and check adjacent squares
            n = self.location([loc.x-1, loc.y, loc.z])
            s = self.location([loc.x+1, loc.y, loc.z])
            w = self.location([loc.x, loc.y, loc.z-1])
            e = self.location([loc.x, loc.y, loc.z+1])
            nw = self.location([loc.x-1, loc.y, loc.z-1])
            sw = self.location([loc.x+1, loc.y, loc.z-1])
            ne = self.location([loc.x-1, loc.y, loc.z+1])
            se = self.location([loc.x+1, loc.y, loc.z+1])
            for b in (n, s, e, w, ne, se, nw, sw):
                self.torchline(b, limit-1, torchtype, fencetype)

    @synchronous()
    def astroturf(self, where=None, limit=50):
        """
        Converts grass blocks into astroturf: jack-o-lanterns with green carpet
        on top. This is a form of hidden lighting, to keep mobs off your lawn.

        :param where:
        :param limit: Default 50.
        """
        if limit < 0:
            return
        origin = self.location(where, looking=True)

        def carpetable(b):
            return airy(b) or glowing(b) or planty(b)

        def turfable(b):
            return grassy(b) or dirty(b) or stony(b) or \
                   sandy(b) or b.type == Material.JACK_O_LANTERN

        queue = LocationQueue(origin, limit)
        while queue:
            loc = self.location(queue.pop())
            while loc.block.type != Material.GRASS_BLOCK \
                    and turfable(loc.block) \
                    and not carpetable(loc.block):
                # block may be underground; check upward
                loc = self.location([loc.x, loc.y+1, loc.z])
            while carpetable(loc.block):
                # block may be above ground; check downward
                loc = self.location([loc.x, loc.y-1, loc.z])
            u = self.location([loc.x, loc.y+1, loc.z]).block
            d = self.location([loc.x, loc.y-1, loc.z]).block
            n = self.location([loc.x-1, loc.y, loc.z]).block
            s = self.location([loc.x+1, loc.y, loc.z]).block
            w = self.location([loc.x, loc.y, loc.z-1]).block
            e = self.location([loc.x, loc.y, loc.z+1]).block
            nw = self.location([loc.x-1, loc.y, loc.z-1]).block
            sw = self.location([loc.x+1, loc.y, loc.z-1]).block
            ne = self.location([loc.x-1, loc.y, loc.z+1]).block
            se = self.location([loc.x+1, loc.y, loc.z+1]).block
            dn = self.location([loc.x-1, loc.y-1, loc.z]).block
            ds = self.location([loc.x+1, loc.y-1, loc.z]).block
            dw = self.location([loc.x, loc.y-1, loc.z-1]).block
            de = self.location([loc.x, loc.y-1, loc.z+1]).block
            dnw = self.location([loc.x-1, loc.y-1, loc.z-1]).block
            dsw = self.location([loc.x+1, loc.y-1, loc.z-1]).block
            dne = self.location([loc.x-1, loc.y-1, loc.z+1]).block
            dse = self.location([loc.x+1, loc.y-1, loc.z+1]).block
            if dirty(loc.block) \
                    and carpetable(u) and turfable(d) \
                    and turfable(n) and turfable(s) \
                    and turfable(w) and turfable(e) \
                    and turfable(nw) and turfable(sw) \
                    and turfable(ne) and turfable(se) \
                    and turfable(dn) and turfable(ds) \
                    and turfable(dw) and turfable(de) \
                    and turfable(dnw) and turfable(dsw) \
                    and turfable(dne) and turfable(dse):
                loc.block.type = Material.JACK_O_LANTERN
                u.type = Material.GREEN_CARPET
            queue.push(n.x, n.y, n.z)
            queue.push(s.x, s.y, s.z)
            queue.push(e.x, e.y, e.z)
            queue.push(w.x, w.y, w.z)

    def block(self, blocktype, where=None):
        """
        Assigns a block of the given type to the specified location.

        :param blocktype: The type of block to assign.
        :param where: The location to place the block (default lookingat()).
        """
        self.cuboid(blocktype, 0, 0, 0, where)

    def platform(self, blocktype=None, xradius=3, zradius=3, where=None):
        """
        Creates a platform of the given type and specified radiuses,
        centered where the linked player is currently looking.

        :param blocktype: The type of block the platform will be made of.
        :param xradius: The platform's radius along the X axis.
        :param zradius: The platform's radius along the Z axis.
        :param where: The platform's center (default lookingat()).
        """
        self.cuboid(blocktype, xradius, 0, zradius, where)

    def cuboid(self, blocktype=None, xradius=3, yradius=3, zradius=3, where=None):
        """
        Creates a cuboid of the given type and specified radiuses,
        centered at the given location.

        :param blocktype: The type of block the cuboid will be made of.
        :param xradius: The cuboid's radius along the X axis.
        :param yradius: The cuboid's radius along the Y axis.
        :param zradius: The cuboid's radius along the Z axis.
        :param where: The cuboid's center (default lookingat()).
        """
        if blocktype is None:
            safe_blocktype = self.lookingat().type
        else:
            safe_blocktype = material(blocktype)
        if safe_blocktype is None:
            raise Exception('Unknown material type: ' + str(blocktype))
            return
        loc = self.location(where, looking=True)
        self._blocks(loc, xradius, yradius, zradius, lambda x,y,z: safe_blocktype)

    def ellipsoid(self, outertype, innertype=Material.AIR,
                 xradius=7, yradius=7, zradius=7, where=None):
        """
        Creates an ellipsoid of the given types and specified radiuses,
        centered at the given location.

        :param outertype: The type of block the ellipsoid will have outside.
        :param innertype: The type of block the ellipsoid will have inside.
        :param xradius: The ellipsoid's radius along the X axis.
        :param yradius: The ellipsoid's radius along the Y axis.
        :param zradius: The ellipsoid's radius along the Z axis.
        :param where: The ellipsoid's center (default lookingat()).
        """
        loc = self.location(where, looking=True)
        xradsq = xradius * xradius
        yradsq = yradius * yradius
        zradsq = zradius * zradius
        def blocktype_function(x, y, z):
            xdist = abs(loc.x - x)
            ydist = abs(loc.y - y)
            zdist = abs(loc.z - z)
            xdistsq = xdist * xdist
            ydistsq = ydist * ydist
            zdistsq = zdist * zdist
            if xdistsq / xradsq + ydistsq / yradsq + zdistsq / zradsq <= 1:
                return innertype
            return None # outside the ellipsoid
        self._blocks(loc, xradius, yradius, zradius, blocktype_function)

    @synchronous()
    def image(self, colortable, image, where=None, wstep=(1, 0, 0), hstep=(0, -1, 0)):
        """
        Draws an image from the given source, using materials from the
        given color table to approximate the color of each image pixel.

        :param colortable: Dictionary mapping material types to color RGB triples.
        :param image: The image to draw.
        :param where: The image's center (default lookingat()).
        :param wstep: (X, Y, Z) tuple defining how each dimensional axis
                      moves along the image's X/width axis. The default
                      is (1, 0, 0), which maps the image X axis to
                      Minecraft's X axis in the positive direction.
        :param hstep: (X, Y, Z) tuple defining how each dimensional axis
                      moves along the image's Y/height axis. The default
                      is (0, -1, 0), which maps the image Y axis to
                      Minecraft's Y axis in the negative direction
                      (so that the image appears right-side up).

        Example:

          from java.net import URL
          url = URL('https://pixelarticons.com/static/3c32cbcff1a695d60899acaf6993aa84/coffee-alt.png')
          image(colortable('wool'), url)
        """
        if not isinstance(image, BufferedImage):
            if type(image) == str:
                # Autodetect files versus URLs.
                image = File(image)
                if not image.exists():
                    image = URL(image)
            image = ImageIO.read(image)

        loc = self.location(where, looking=True)

        def coord(d, ix, iy):
            return wstep[d] * ix + hstep[d] * iy

        cix = image.width / 2
        ciy = image.height / 2

        for iy in range(0, image.height):
            for ix in range(0, image.width):
                argb = image.getRGB(ix, iy)
                a = 0xff & (argb >> 24)
                r = 0xff & (argb >> 16)
                g = 0xff & (argb >> 8)
                b = 0xff & argb
                if a < 64:
                    continue
                x = int(loc.x + coord(0, ix - cix, iy - ciy))
                y = int(loc.y + coord(1, ix - cix, iy - ciy))
                z = int(loc.z + coord(2, ix - cix, iy - ciy))
                block_material = _closest_material(colortable, r, g, b)
                self.world().getBlockAt(x, y, z).type = block_material

    @synchronous()
    def _blocks(self, loc, xradius, yradius, zradius, block_function):
        irange = lambda a, b: range(int(math.floor(a)), int(math.floor(b + 1)))
        for x in irange(loc.x - xradius, loc.x + xradius):
            for y in irange(loc.y - yradius, loc.y + yradius):
                for z in irange(loc.z - zradius, loc.z + zradius):
                    block_material = block_function(x, y, z)
                    if block_material:
                        self.world().getBlockAt(x, y, z).type = block_material

    @synchronous()
    def pour(self, blocktype, where, srctype=None, maxdepth=20):
        """
        Flood fills an area of one block type to a different type.

        :param blocktype:
        :param where:
        :param srctype:
        :param maxdepth:
        """
        loc = self.location(where, looking=True)
        if srctype is None:
            srctype = self.world().getBlockAt(loc).type
        _fill(material(blocktype), loc, material(srctype), 0, maxdepth)

    def _fill(self, blocktype, loc, srctype, depth, maxdepth):
        if depth >= maxdepth:
            return
        block = self.world().getBlockAt(loc)
        if block.type != srctype:
            return
        block.type = blocktype
        self._fill([loc.x+1, loc.y, loc.z], blocktype, srctype, depth+1, maxdepth)
        self._fill([loc.x-1, loc.y, loc.z], blocktype, srctype, depth+1, maxdepth)
        self._fill([loc.x, loc.y, loc.z-1], blocktype, srctype, depth+1, maxdepth)
        self._fill([loc.x, loc.y, loc.z+1], blocktype, srctype, depth+1, maxdepth)
        self._fill([loc.x, loc.y-1, loc.z], blocktype, srctype, depth+1, maxdepth)

    @synchronous()
    def maze(self, blocktype=Material.STONE, xlen=31, zlen=31, height=3, where=None):
        """
        Creates a maze of the given type and specified dimensions, with an
        entrance at the given coordinates, and exit on the opposite diagonal.

        :param blocktype: The type of block the maze will be made of.
        :param xlen: The maze's length in X.
        :param zlen: The maze's length in Z.
        :param height: The maze's height (length in Y).
        :param where: The maze's entrance corner.
                      Default is one unit above lookingat().
        """
        block_material = material(blocktype)
        maze = Maze(int((xlen - 1) / 2), int((zlen - 1) / 2), 0, 0)
        maze.make_maze()
        if where is None:
            look = self.lookingat()
            px, py, pz = look.x, look.y + 1, look.z
        else:
            px = self.ix(where)
            py = self.iy(where)
            pz = self.iz(where)
        x, z = px, pz
        for row in str(maze).split('\n'):
            z += 1
            x = px
            for c in row:
                x += 1
                if c == ' ': continue
                for y in range(py, py + height):
                    self.world().getBlockAt(x, y, z).type = block_material

    @synchronous()
    def airrail(self, wherestart, whereend, blocktype):
        """
        Lays down rail from one location to another,
        as straightly as possible while following rail rules.

        :param wherestart: Starting position of the rail.
        :param whereend: Ending position of the rail.
        :param blocktype: The type of block under the rail.
        """
        world = self.world()
        x, y, z = self.ipos(wherestart)
        y = float(y)
        stop = self.ipos(whereend)
        block_material = material(blocktype)
        rail_material = Material.POWERED_RAIL

        xdiff = stop[0] - x
        ydiff = stop[1] - y
        zdiff = stop[2] - z
        xinc = sign(xdiff)
        zinc = sign(zdiff)
        xzdiff = abs(xdiff) - abs(zdiff)
        if xzdiff > 0:
            raildir = True # lay along X
            oomph = max(2, abs(xdiff) / max(1, abs(zdiff)))
        else:
            raildir = False # lay along Z
            oomph = max(2, abs(zdiff) / max(1, abs(xdiff)))

        step = 0
        maxsteps = abs(xdiff) + 2*abs(ydiff) + abs(zdiff) + 5
        while (x, int(y), z) != stop:
            step += 1
            if step > maxsteps:
                print('[ERROR] Rail path did not converge!')
                break
            if raildir:
                x += xinc
            else:
                z += zinc
            oomph -= 1
            turned_last_time = rail_material == Material.RAIL
            rail_material = Material.POWERED_RAIL

            # compute which direction to move up or down -- if feasible
            ydenom = abs(stop[0] - x) + abs(stop[2] - z)
            if ydenom == 0: ydenom = 1
            yinc = (stop[1] - y) / ydenom
            if yinc < -1: yinc = -1
            if yinc > 1: yinc = 1

            if oomph == 0:
                # turn
                raildir = not raildir
                rail_material = Material.RAIL
                xinc = 1 if x < stop[0] else -1
                zinc = 1 if z < stop[2] else -1
                xdiff = stop[0] - x
                zdiff = stop[2] - z
                if raildir:
                    oomph = max(2, abs(xdiff) / max(1, abs(zdiff)))
                else:
                    oomph = max(2, abs(zdiff) / max(1, abs(xdiff)))
                if yinc < 0:
                    # cannot go down while turning
                    yinc = 0
            elif int(y) != stop[1]:
                if turned_last_time and yinc > 0:
                    # cannot go up after turning
                    yinc = 0
            else:
                yinc = 0
            y += yinc

            blk = self.world().getBlockAt(int(x), int(y), int(z))
            if not airorwater(blk):
                print('[ERROR] Track ran into something!')
                return
            blk.type = block_material

            blk1 = self.world().getBlockAt(int(x), int(y+1), int(z))
            if not airorwater(blk1):
                print('[ERROR] Rail ran into something!')
                return
            blk1.type = rail_material

    @synchronous()
    def layrail(self, where=None, limit=100, powerstep=8):
        """
        Places powered rail along an existing track.

        :param where:
        :param limit: Default 100.
        :param powerstep: Default 8.
        """
        loc = self.location(where, looking=True)
        tracktype = loc.block.type
        for x in (-1, 0, 1):
            for z in (-1, 0, 1):
                if abs(x ^ z) != 1:
                    # only traverse n/s/w/e
                    continue
                for y in (-1, 0, 1):
                    nxt = self.location([loc.x+x, loc.y+y, loc.z+z])
                    above = self.location([nxt.x, nxt.y+1, nxt.z])
                    if nxt.block.type == tracktype and \
                            above.block.type != Material.RAIL and \
                            above.block.type != Material.POWERED_RAIL:
                        # rail needed in this direction
                        self._layrail(nxt, limit-1, tracktype, loc, powerstep)

    def _layrail(self, loc, limit, tracktype, previous, powerstep, powerleft=0):
        if limit < 0:
            return

        xdiff = loc.x - previous.x
        zdiff = loc.z - previous.z
        railtype = Material.RAIL
        nextloc = None

        # detect track in a straight line
        xnext = loc.x + xdiff
        znext = loc.z + zdiff
        for nxt in (self.location([xnext, loc.y+1, znext]), \
                    self.location([xnext, loc.y, znext]), \
                    self.location([xnext, loc.y-1, znext])):
            above = self.location([nxt.x, nxt.y+1, nxt.z])
            if nxt.block.type == tracktype or \
                    above.block.type == Material.POWERED_RAIL or \
                    above.block.type == Material.RAIL:
                railtype = Material.POWERED_RAIL
                nextloc = nxt
                break

        # detect track turning a corner
        if nextloc is None:
            if xdiff != 0:
                nexts = (
                    self.location([loc.x, loc.y, loc.z-1]),
                    self.location([loc.x, loc.y-1, loc.z-1]),
                    self.location([loc.x, loc.y, loc.z+1]),
                    self.location([loc.x, loc.y-1, loc.z+1])
                )
            elif zdiff != 0:
                nexts = (
                    self.location([loc.x-1, loc.y, loc.z]),
                    self.location([loc.x-1, loc.y-1, loc.z]),
                    self.location([loc.x+1, loc.y, loc.z]),
                    self.location([loc.x+1, loc.y-1, loc.z])
                )
            else:
                print('[ERROR] Assertion failed: loc=(%d, %d, %d), xdiff=%d, zdiff=%d' % (loc.x, loc.y, loc.z, xdiff, zdiff))
                return
            for nxt in nexts:
                above = self.location([nxt.x, nxt.y+1, nxt.z])
                if nxt.block.type == tracktype or \
                        above.block.type == Material.POWERED_RAIL or \
                        above.block.type == Material.RAIL:
                    nextloc = nxt
                    powerleft = 0
                    break

        if nextloc is None:
            print('[ERROR] Track ends at (%d, %d, %d)' % (loc.x, loc.y, loc.z))
            return

        # lay the rail
        u = self.location([loc.x, loc.y+1, loc.z])
        if u.block.type == Material.RAIL or \
           u.block.type == Material.POWERED_RAIL:
            # we already have rail on this block of track
            pass
        elif not airy(u.block):
            print('[WARNING] Track at (%d, %d, %d) is blocked!' % (loc.x, loc.y, loc.z))
        else:
            u.block.type = railtype

        # power the rail, if needed
        if u.block.type == Material.POWERED_RAIL:
            if powerleft > 0:
                powerleft -= 1
            else:
                # power the rail!
                if xdiff != 0:
                    sides = (
                        self.location([loc.x, loc.y, loc.z-1]),
                        self.location([loc.x, loc.y, loc.z+1])
                    )
                elif zdiff != 0:
                    sides = (
                        self.location([loc.x-1, loc.y, loc.z]),
                        self.location([loc.x+1, loc.y, loc.z])
                    )
                else:
                    print('[ERROR] Assertion failed: loc=(%d, %d, %d), xdiff=%d, zdiff=%d' % (loc.x, loc.y, loc.z, xdiff, zdiff))
                    return
                torched = False
                for side in sides:
                    torchspot = self.location([side.x, side.y+1, side.z]).block
                    if not airy(torchspot):
                        if torchspot.type == Material.REDSTONE_TORCH:
                            torched = True
                        continue
                    if airorwater(side.block):
                        side.block.type = tracktype
                    torchspot.type = Material.REDSTONE_TORCH
                    torched = True
                if not torched:
                    # no room for redstone torches; use a redstone block instead
                    loc.block.type = Material.REDSTONE_BLOCK
                powerleft = powerstep

        # keep going
        self._layrail(nextloc, limit-1, tracktype, loc, powerstep, powerleft)


    ################# SEARCHING ##################

    def diamonds(self, where=None, limit=100):
        """
        Searches around for nearby diamonds.
        """
        origin = self.location(where)
        origin.y = 11 # Diamond level!
        queue = LocationQueue(origin, limit)
        hits = []
        while queue:
            loc = self.location(queue.pop())
            if loc.block.type == Material.DIAMOND_ORE:
                print(loc)
                hits.append(loc)
            n = self.location([loc.x-1, loc.y, loc.z]).block
            s = self.location([loc.x+1, loc.y, loc.z]).block
            w = self.location([loc.x, loc.y, loc.z-1]).block
            e = self.location([loc.x, loc.y, loc.z+1]).block
            u = self.location([loc.x-1, loc.y, loc.z]).block
            d = self.location([loc.x+1, loc.y, loc.z]).block
            queue.push(n.x, n.y, n.z)
            queue.push(s.x, s.y, s.z)
            queue.push(w.x, w.y, w.z)
            queue.push(e.x, e.y, e.z)
            if u.y <= 13 and u.y >= 9:
                queue.push(u.x, u.y, u.z)
            if d.y <= 13 and d.y >= 9:
                queue.push(d.x, d.y, d.z)
        # TODO: Connected component analysis.
        return hits


    ############### MISCELLANEOUS ################

    def compasstarget(self, where):
        """
        Points the linked player's compass to the specified place.
        :param where: Place or player where linked player's compass will point.
        """
        who = self.player(where)
        if who:
            # Continuously update compass to point to that player.
            self._compass_updater = CompassUpdater(self.player(), who)
            self._compass_updater.runTaskTimer(PLUGIN, 0, 100);
        else:
            # Stop continuous update thread.
            if self._compass_updater:
                self._compass_updater.cancel()
                self._compass_updater = None
            self.player().setCompassTarget(self.location(where))

class CompassUpdater(BukkitRunnable):
    def __init__(self, player, target):
        self.player = player
        self.target = target
    def run(self):
        self.player.setCompassTarget(self.target.location)


################## PLAYERS ###################
# Specific to me -- if you want this generalized, file an issue
# and I'll turn it into a config file. Otherwise, YAGNI! ;-)

ted = pov('FlexibleKid7')
mn = pov('MilesintheNether')
rg = pov('restlessgamer7')


################### IDEAS ####################

# 3D Python turtle
# copy/paste blocks of reality
# generate mathematical structures
# generate structures matching images
# dropping items
# spawning creatures
