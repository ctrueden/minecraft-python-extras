import gol

def board2str(board, w, h):
    s = ''
    for y in range(h):
        for x in range(w):
            s += 'X' if board[(x, y)] else '.'
        s += '\n'
    return s

# Test 2D
gol2d = gol.GameOfLife()
w = 7; h = 5
board = gol.random_board([w, h], seed=12345)
game = gol2d.start(board)

boards2d = [
"""
...X...
X......
.......
....XXX
.......
""",
"""
.......
.......
.....X.
.....X.
.....X.
""",
"""
.......
.......
.......
....XXX
.......
"""
]

for board in boards2d:
    assert board.lstrip() == board2str(game.state, w, h)
    game.next()

# Test 3D
gol3d = gol.GameOfLife(max_adjacent_dims=3, isolation_threshold=5, birth_min=6, birth_max=7, overcrowding_threshold=9)
w = 2; h = 3; d = 4
game = gol3d.start(gol.random_board([w, h, d], seed=0xdeadbeef))
game.next()
# TODO: Assert game states match expected.
