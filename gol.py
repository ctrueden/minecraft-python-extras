"""
A ridiculously abstracted version of Conway's Game of Life.
"""

import random

class Game(collections.abc.Iterable):
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
        class GameState(collections.abc.Iterator):
            def __init__(self, game, state):
                self.game = game
                self.state = state 

            def __next__(self):
                self.state = self.game.nextgamestate(self.state)

        return GameState(self, state)

    def nextgamestate(self, state): # Abstract!
        """
        Abstract method for advancing a game by one step.
        """
        raise "Implement me"


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
        for cell in self.cells(state):
            next_state[cell] = self.nextcellstate(state, cell)
        return next_state

    def nextcellstate(self, board, cell): # Abstract!
        """
        Abstract method defining the next cell state for a given board + cell.
        """
        raise "Implement me"

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
        for cell in self.cells(board):
            next_board[cell] = self.nextcellstate(self.neighbors(board, cell), cell)
        return next_board

    def neighbors(self, board, cell): # Default behavior!
        """
        Obtains, for a given board + cell, its neighbor cells.
        By default, all cells of the board are considered neighbors.
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
        return {c, self.board[c] for c in self.board if self.isneighbor(cell, c)}

    def isneighbor(self, cell1, cell2): # Abstract!
        """
        Gets whether two cells are neighbors.
        """
        raise "Implement me"

class LifeGame(NeighborhoodBoardGame):
    """
    A *life* game is a neighborhood board game where the cells have two states:
    live (True) and dead (False).

    For each cell, its next state is dictated by the following rules:
    - Isolation:    Each live cell whose live neighbors number <= the
                    isolation threshold will die in the next generation.
    - Overcrowding: Each live cell whose live neighbors number >= the
                    overcrowding threshold will die in the next generation.
    - Survival:     Each live cell whose live neighbors number strictly more
                    than the isolation threshold, but strictly less than the
                    overcrowding threshold, will remain alive for the next
                    generation.
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
        livecount = board.values().count(True)
        live = board[cell]
        return livecount > self.isolation_threshold and livecount < self.overcrowding_threshold if live else \
               livecount >= self.birth_min and livecount <= self.birth_max

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
        offsets = itertools.product([-1, 0, 1], repeat=dim)
        candidates = [sum(t) for offset in offsets for t in zip(cell, offset)]
        return [p for p in candidates if p in board and self.isneighbor(cell, p)

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
            * 0 if v1 == v2
            * 1 if v1 == v2 + 1 or v1 == v2 - 1
            * +infinity for all larger differences
            """
            d = abs(v1 - v2)
            return d if d <= 1 else float('inf')

        return sum(adist(pair[0], pair[1]) for pair in zip(cell1, cell2)) <= max_adjacent_dims


class GameOfLife(ZnBoardGame, LifeGame):

    def __init__(self, max_adjacent_dims=2, isolation_threshold=2, birth_min=3, birth_max=3, overcrowding_threshold=5):
        super.ZnBoardGame.__init__(max_adjacent_dims)
        super.LifeGame.__init__(isolation_threshold, birth_min, birth_max, overcrowding_threshold)


def randomize(saturation, extents, live=True, dead=False):
    """
    :param saturation: Probability of a cell having the live state. Min 0.0, max 1.0.
    """
    board = {}
    for cell in itertools.product(*[range(extent) for extent in extents]):
        board[cell] = live if random.random() < saturation else dead
    return board


gol3d = GameOfLife(max_adjacent_dims=3, isolation_threshold=5, birth_min=6, birth_max=7, overcrowding_threshold=9)
board = randomize(0.1, [10, 12, 7])
it = gol3d.start(board)
