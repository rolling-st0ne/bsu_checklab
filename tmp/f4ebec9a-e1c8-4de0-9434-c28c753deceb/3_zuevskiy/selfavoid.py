import matplotlib.pyplot as plt
import sys
import random

if len(sys.argv) != 3:
    exit()

size, file_name = int(sys.argv[1]), sys.argv[2]
# size, file_name = 15, "out.png"

matrix = [[False for _ in range(size + 1)] for _ in range(size + 1)]

x = (size + 1) // 2
y = (size + 1) // 2

matrix[x][y] = True


def step(x, y, matrix):
    free_spots = list()

    if x - 1 >= 1 and not matrix[x - 1][y]:
        free_spots.append((x - 1, y))
    
    if x + 1 <= size and not matrix[x + 1][y]:
        free_spots.append((x + 1, y))

    if y - 1 >= 1  and not matrix[x][y - 1]:
        free_spots.append((x, y - 1))

    if y + 1 <= size and not matrix[x][y + 1]:
        free_spots.append((x, y + 1))

    if len(free_spots) > 0:
        x, y = random.choice(free_spots)
        matrix[x][y] = True
        return x, y, matrix

    else:
        return -1, -1, matrix

steps_x = list()
steps_y = list()

while (x, y) != (-1, -1):
    steps_x.append(x)
    steps_y.append(y)

    x, y, matrix = step(x, y, matrix)

plt.grid()
plt.plot(steps_x, steps_y, linewidth=3)
plt.plot([steps_x[0]], [steps_y[0]], 'ro')
plt.plot([steps_x[-1]], [steps_y[-1]], 'bo')
plt.xlim(1, size)
plt.ylim(1, size)
ticks = [x for x in range(1, size+1)]
plt.xticks(ticks)
plt.yticks(ticks)
# plt.show()
plt.savefig(sys.argv[2], dpi=300, bbox_inches='tight')

# print(steps_x, steps_y)