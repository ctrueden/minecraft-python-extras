from java.net import URL, URLClassLoader

# TODO: Generalize path.
url = URL('file:///home/curtis/minecraft/python/mcx/mcx.jar')
cl = URLClassLoader([url])
gol3d = cl.loadClass('GameOfLife3D')
golFactory = gol3d.getConstructors()[0]

def golfast(world, xMin, xMax, yMin, yMax, zMin, zMax,
            max_adjacent_dims=3, birth_min=6, birth_max=6,
            starvation_max=3, suffocation_min=8):

    return golFactory.newInstance(world, xMin, xMax, yMin, yMax, zMin, zMax,
                                  max_adjacent_dims, birth_min, birth_max,
                                  starvation_max, suffocation_min)
