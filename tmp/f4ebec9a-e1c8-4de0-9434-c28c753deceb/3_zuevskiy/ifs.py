import random
import sys
import matplotlib.pyplot as plt

file_name = sys.argv[2]
weights = list()
coef1 = list()

with open(sys.argv[1], "r") as f:
    weights = f.readline()
    f.readline()

    k_x, k_y = f.read().split("\n\n")
    k_x = k_x.split("\n")
    k_y = k_y.split("\n")

    print(k_x)
    print()
    print(k_y)




cx = [0.0, 1.0, 0.5]
cy = [0.0, 0.0, 0.866]

n = 50_000

x, y = [0.0], [0.0]
for _ in range(n):
    r = random.randrange(3)
    x.append((x[-1] + cx[r]) / 2.0)
    y.append((y[-1] + cy[r]) / 2.0)

fig, ax = plt.subplots()
fig.suptitle("Ковер Серпинского")
ax.set_xlim(-0.2, 1.2)
ax.set_ylim(-0.2, 1)
ax.set_aspect("equal", adjustable="box")

ax.plot(x, y, "b.", markersize=1)
plt.show()
