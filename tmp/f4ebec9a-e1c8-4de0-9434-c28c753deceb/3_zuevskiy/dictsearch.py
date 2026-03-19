import sys

word = sys.argv[2]
path = sys.argv[1]

result = list()

with open(path, "r") as f:
    f = list(f)
    start, end = 0, len(f) - 1

    while end - start > 1:
        mid = (end - (end - start) // 2)

        if f[mid].startswith(word):
            break

        if word < f[mid]:
            end = mid

        elif word > f[mid]:
            start = mid

    else:
        print([])
        exit()

    i = mid

    while f[i].startswith(word):
        i -= 1
    else:
        i += 1

    while f[i].startswith(word):
        result.append(f[i].rstrip('\n'))
        i += 1

    print(result)