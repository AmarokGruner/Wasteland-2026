def generate_province_grid(size=15):
    cx = cy = size // 2  # center at (7,7) for size=15
    grid = [['x' for _ in range(size)] for _ in range(size)]

    def set_cell(i, j, val):
        if 0 <= i < size and 0 <= j < size:
            grid[i][j] = str(val)

    # Camp cross (5 fields, level 1)
    cross = [(cx, cy), (cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]
    for (i, j) in cross:
        set_cell(i, j, 1)

    # Diagonals around center (level 2)
    diags = [(cx-1, cy-1), (cx-1, cy+1), (cx+1, cy-1), (cx+1, cy+1)]
    for (i, j) in diags:
        set_cell(i, j, 2)

    # Ring distance 2 -> level 3
    for i in range(size):
        for j in range(size):
            if max(abs(i-cx), abs(j-cy)) == 2:
                if grid[i][j] == 'x':
                    set_cell(i, j, 3)

    # Ring distance 3 -> level 4
    for i in range(size):
        for j in range(size):
            if max(abs(i-cx), abs(j-cy)) == 3:
                if grid[i][j] == 'x':
                    set_cell(i, j, 4)

    # Ring distance 4 -> level 5 (26-32 cells). We will distribute 6 cells per quadrant (total 24) to keep symmetry.
    ring4 = []
    for i in range(size):
        for j in range(size):
            if max(abs(i-cx), abs(j-cy)) == 4:
                if i == cx or j == cy:
                    continue
                ring4.append((i, j))
    # Partition into four quadrants around center
    def quad(p):
        i, j = p
        if i < cx and j < cy: return 1
        if i < cx and j > cy: return 2
        if i > cx and j < cy: return 3
        if i > cx and j > cy: return 4
        return 0
    groups = {1: [], 2: [], 3: [], 4: []}
    for coord in ring4:
        groups[quad(coord)].append(coord)
    for q in range(1,5):
        groups[q].sort()
        for idx, coord in enumerate(groups[q]):
            if idx < 6:
                i, j = coord
                grid[i][j] = '5'

    return grid

def print_grid(grid):
    for row in grid:
        print(' '.join(row))

if __name__ == '__main__':
    g = generate_province_grid(15)
    print_grid(g)
