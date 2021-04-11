"""
A ridiculously abstracted version of Conway's Game of Life.

It would be nice to use the ABC mechanism fleshed out in Python 3.
But this code is intended for use with Jython, and therefore needs
to run with Python 2.7. So we'll settle for "abstract" methods
that raise an exception, rather than disallowing instantiation.
"""

import itertools, random
import collections
try:
    Iterator = collections.abc.Iterator
except AttributeError:
    # NB: For Python 2 / Jython.
    Iterator = collections.Iterator


class Game(object):
    """
    A game is a function:
        state sub t -> state sub t+1
    where t is a non-negative integer representing the game's current time or step.
    This function updates the game state; i.e.:
    when the function is iterated, the game progresses.
    """

    def start(self, state):
        """
        Given a starting state, returns an iterator for advancing that state
        by repeated application of nextgamestate.
        """
        class GameState(Iterator):
            def __init__(self, game, state):
                self.game = game
                self.state = state 

            def __next__(self):
                self.state = self.game.nextgamestate(self.state)

            # NB: For Python 2 / Jython.
            def next(self):
                return self.__next__()

        return GameState(self, state)

    def nextgamestate(self, state): # Abstract!
        """
        Abstract method for advancing a game by one step.
        """
        raise Exception("Unimplemented")


class BoardGame(Game):
    """
    A board game is a game whose state is a dict-like board of cells (keys)
    mapped to cell states (values).
    """

    def nextgamestate(self, state): # Implemented!
        """
        Advances the board a step by invoking nextcellstate on each cell.
        """
        next_state = state.copy()
        for cell in state:
            next_state[cell] = self.nextcellstate(state, cell)
        return next_state

    def nextcellstate(self, board, cell): # Abstract!
        """
        Abstract method defining the next cell state for a given board + cell.
        """
        raise Exception("Unimplemented")


class NeighborhoodBoardGame(BoardGame):
    """
    A *neighborhood* board game is a board game with additional structure:
    for a given board + cell, we recognize that not all other cells may be
    relevant for discerning that cell's next state. We define a cell's
    *neighbors* to be the set of board cells which could affect that cell's
    next state. These neighbors are fed to the nextcellstate method as a *board
    subset*, so that it considers only those neighbor cells when calculating.
    """

    def nextgamestate(self, board): # Overridden!
        """
        Advances the game state a step by invoking nextcellstate on each cell,
        considering only each cell's neighbors, rather than the entire board.
        """
        next_board = board.copy()
        for cell in board:
            next_board[cell] = self.nextcellstate(self.neighbors(board, cell), cell)
        return next_board

    def neighbors(self, board, cell): # Default behavior!
        """
        Obtains, for a given board + cell, its neighbor cells.
        By default, all cells of the board are considered neighbors.
        At minimum, the cell itself must be included in the neighbors set.
        """
        return board


class StableBoardGame(NeighborhoodBoardGame):
    """
    A *stable* board game adds a restriction to the neighborhood board game:
    each cell's neighbors are guaranteed to be independent of the board state.
    That is: we can discern whether two cells are neighbors based only on those
    cells themselves, not their states, nor the existence of or state of any
    other cells of the board.
    """

    def neighbors(self, board, cell): # Overridden!
        """
        Obtains, for a given board + cell, its neighbor cells.
        The isneighbor method is used to filter the board.
        """
        return {c: self.board[c] for c in self.board if self.isneighbor(cell, c)}

    def isneighbor(self, cell1, cell2): # Abstract!
        """
        Gets whether two cells are neighbors.
        """
        raise Exception("Unimplemented")


class LifeGame(NeighborhoodBoardGame):
    """
    A *life* game is a neighborhood board game where the cells have two states,
    live (True) and dead (False). For each cell, its next state is dictated by
    the following rules:

    - Isolation:    Each live cell whose live neighbors number <= the
                    isolation threshold will die in the next generation.

    - Overcrowding: Each live cell whose live neighbors number >= the
                    overcrowding threshold will die in the next generation.

    - Survival:     Each live cell whose live neighbors number > the isolation
                    threshold, but < the overcrowding threshold, will remain
                    alive for the next generation.

    - Birth:        Each dead cell whose live neighbors number >= birth_min
                    and <= birth_max will become live in the next generation.
    """

    def __init__(self, isolation_threshold, birth_min, birth_max, overcrowding_threshold):
        self.isolation_threshold = isolation_threshold
        self.birth_min = birth_min
        self.birth_max = birth_max
        self.overcrowding_threshold = overcrowding_threshold
        assert isolation_threshold < overcrowding_threshold
        assert birth_min <= birth_max

    def nextcellstate(self, board, cell): # Implemented!
        """
        Defines the next cell state for a given board + cell.
        """
        c = list(board.values()).count(True) # number of live neighbors
        live = board[cell] # assumes the cell is a neighbor of itself
        return c > self.isolation_threshold and c < self.overcrowding_threshold if live else \
               c >= self.birth_min and c <= self.birth_max


class ZnBoardGame(StableBoardGame):
    """
    A *Z^n* board game is a board game played on cells in N-dimensional integer
    space.
    """

    def __init__(self, max_adjacent_dims):
        self.max_adjacent_dims = max_adjacent_dims

    def neighbors(self, board, cell): # Overridden for performance!
        """
        Obtains, for a given board + cell, its neighbor cells.
        """
        dim = len(cell)

        # Iteration of all [-1/0/1, -1/0/1, ...] tuples, dim dimensions long.
        # E.g. in 2D, this will be:
        # [
        #   (-1, -1), (-1, 0), (-1, 1),
        #    (0, -1),  (0, 0),  (0, 1), 
        #    (1, -1),  (1, 0),  (1, 1)
        # ]
        offsets = itertools.product([-1, 0, 1], repeat=dim)

        # List of coordinates corresponding to the current cell adjusted by each offset.
        #
        #   candidates = [cell ++ offset for offset in offsets]
        #
        # Where "++" is element-wise addition over equal-length lists/tuples.
        # But sadly, Python does not have an operator like that (+ on lists
        # concatenates them), so we have this tricky construction instead:
        candidates = [tuple(sum(pair) for pair in zip(cell, offset)) for offset in offsets]

        return {p: board[p] for p in candidates if p in board and self.isneighbor(cell, p)}

    def isneighbor(self, cell1, cell2): # Implemented!
        """
        Gets whether two cells are neighbors: adjacent or equal along each
        dimensional axis. The number of axes that are allowed to be adjacent
        rather than equal is defined by the max_adjacent_dims parameter.

        Examples:
        * Squares in 2D space, 4-connected (across edges only): max_adjacent_dims = 1
          - Either X or Y, but not both, is adjacent. The other coordinate is equal.
        * Squares in 2D space, 8-connected (across edges or corners): max_adjacent_dims = 2
          - X, Y, or both may be adjacent. Neither coordinate must be equal.
        * Cubes in 3D space, 6-connected (across faces only): max_adjacent_dims = 1
          - Either X, Y, or Z, but only one of them at most, is adjacent. The other two must be equal.
        * Cubes in 3D space, 18-connected (across faces or edges): max_adjacent_dims = 2
          - Up to two of X, Y, and Z is adjacent. The remaining dimension must be equal.
        * Cubes in 3D space, 26-connected (across faces, edges, or corners): max_adjacent_dims = 3
          - Any of X, Y, and Z may be adjacent. None of the coordinates must be equal.
        """
        def adist(v1, v2):
            """
            Adjacency distance:
            * 0 if v1=v2
            * 1 if v1=v2+1 or v1=v2-1
            * infinity for all larger differences
            """
            d = abs(v1 - v2)
            return d if d <= 1 else float('inf')

        return sum(adist(pair[0], pair[1]) for pair in zip(cell1, cell2)) <= self.max_adjacent_dims


class GameOfLife(ZnBoardGame, LifeGame):

    def __init__(self, max_adjacent_dims=2, isolation_threshold=2, birth_min=3, birth_max=3, overcrowding_threshold=5):
        ZnBoardGame.__init__(self, max_adjacent_dims)
        LifeGame.__init__(self, isolation_threshold, birth_min, birth_max, overcrowding_threshold)


def random_board(extents, saturation=0.1, live=True, dead=False, seed=None, rng=None):
    """
    :param saturation: Probability of a cell having the live state (default 0.1, min 0.0, max 1.0).
    :param live: The value to use for live state (default True).
    :param dead: The value to use for dead state (default False).
    :param seed: The random seed, in case the standard Python RNG is used (default None).
    :param rng: An object whose random() function generates floats between
                0.0 and 1.0. The default is a fresh random.Random object using
                the specified seed, whose aim is a uniform distribution.
    """
    board = {}
    if rng is None: rng = random.Random(seed)
    for cell in itertools.product(*[range(extent) for extent in extents]):
        board[cell] = live if rng.random() < saturation else dead
    return board
