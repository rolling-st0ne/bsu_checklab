import sys
import csv
import matplotlib.pyplot as plt
import math


path = sys.argv[1]
# path = "lab3_files/minsk2025.csv"

dir_count = {0:0, 45:0, 90:0, 135:0, 180:0, 225:0, 270:0, 315:0}


with open(path, "r") as f:
    csv_dict = csv.DictReader(f)

    wdir = [row["wdir"] for row in csv_dict]
    wdir.sort()

    for direct in wdir:
        i = (((float(direct) + 22.5) // 45) % 8) * 45
        dir_count[i] += 1

# print(dir_count)

x, y = [], []

for angle, count in dir_count.items():
    x.append(count * math.sin(math.radians(angle)))
    y.append(count * math.cos(math.radians(angle)))

x.append(x[0])
y.append(y[0])


dir_names = ("N", "NE","E","SE","S","SW","W","NW")
plt.axis("equal")
plt.grid(True)
plt.title("Роза ветров Минска")
plt.xlim(-1500, 1500)
plt.ylim(-1500, 1500)

plt.plot(x, y)

for i in range(8):
    plt.arrow(0, 0, x[i], y[i])
    plt.text(x[i], y[i], dir_names[i])

# plt.show()
plt.savefig(sys.argv[2], dpi=300, bbox_inches='tight')
