# Credit: https://stackoverflow.com/a/5187612/1207769
def line(x0, y0, x1, y1):
    dx = abs(x1 - x0) # distance to travel in X
    dy = abs(y1 - y0) # distance to travel in Y

    ix = 1 if x0 < x1 else -1
    iy = 1 if y0 < y1 else -1
    e = 0 # Current error

    for i in range(dx + dy):
        yield x0, y0
        e1 = e + dy
        e2 = e - dx
        if abs(e1) < abs(e2):
            # Error will be smaller moving on X
            x0 += ix
            e = e1
        else:
            # Error will be smaller moving on Y
            y0 += iy
            e = e2
