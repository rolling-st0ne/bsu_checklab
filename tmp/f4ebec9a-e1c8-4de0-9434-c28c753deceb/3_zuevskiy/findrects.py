import sys


def getRectsIndexes(str):
    rects_indexes = set()

    for i in range(len(str) - 1):
            if (str[i] == "0" and str[i + 1] == "1") or (i == 0 and str[0] == "1"):
                rects_indexes.add(i)

    return rects_indexes


def getEndedRects(set1, set2):
    diffSet = set1 - set2

    return len(diffSet)


rects_count = 0

with open(sys.argv[1], "r") as f:
    current_line = getRectsIndexes(f.readline().rstrip('\n'))
    line_before = set()

    for line in f:
        line_before = current_line
        current_line = getRectsIndexes(line.rstrip('\n'))
        rects_count += getEndedRects(line_before, current_line)

    rects_count += len(current_line)

print(rects_count)