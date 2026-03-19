import sys

# file_input = list(map(int, open(input(), "r")))
# S = int(input())

with open(sys.argv[1], "r") as file_input:
    S = int(sys.argv[2])

# with open(input(), "r") as file_input:
#     S = int(input())

    file_input = list(map(int, file_input))

    length = len(file_input)

    sum = 0
    i = 0
    count = 0
    again = False

    while i < length:
        if sum > S:
            sum -= file_input[i - count]
            count -= 1

        elif sum < S:
            sum += file_input[i]
            count += 1
            i += 1

        if sum == S:
            print(file_input[i - count:i] if ((file_input[i - count:i] != []) and count >= 2) else "No answer")
            exit()


    else:
        print("No answer")


