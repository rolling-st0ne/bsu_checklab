import sys


def bubble_sort(lst):
    comparisons = 0
    swaps = 0

    for i in range(len(lst)):
        for j in range(len(lst) - i - 1):
            comparisons += 1
            if lst[j] > lst[j + 1]:
                lst[j], lst[j + 1] = lst[j + 1], lst[j]
                swaps += 1

    return [comparisons, swaps, lst]


def selection_sort(lst):
    comparisons = 0
    swaps = 0

    for i in range(len(lst) - 1):
        max_index = 0
        for j in range(1, len(lst) - i):
            comparisons += 1

            if lst[max_index] < lst[j]:
                max_index = j

        swaps += 1
        lst[max_index], lst[-i - 1] = lst[-i - 1], lst[max_index]

    return [comparisons, swaps, lst]


def insertion_sort(lst):
    comparisons = 0
    swaps = 0

    for i in range(1, len(lst)):
        number = lst[i]

        for j in range(i - 1, -1, -1):
            comparisons += 1

            if number < lst[j]:
                swaps += 1
                lst[j + 1], lst[j] = lst[j], lst[j + 1]
            else:
                break

    return [comparisons, swaps, lst]


path = sys.argv[1]
sort_type = sys.argv[2]

if len(sys.argv) == 4:
    k = int(sys.argv[3])
else:
    k = 20

with open(path, "r") as f:
    numbers = f.read().split()
    numbers = list(map(int, numbers))

    match sort_type:
        case "bubble":
            comparisons, swaps, lst = bubble_sort(numbers)

        case "selection":
            comparisons, swaps, lst = selection_sort(numbers)

        case "insertion":
            comparisons, swaps, lst = insertion_sort(numbers)

    result = comparisons, swaps, lst[:k]
    print(result)