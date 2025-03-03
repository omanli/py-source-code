# utility function
def swap_elements(L, p, q):
    x = L[p]
    L[p] = L[q]
    L[q] = x


# initialization
L = [83, 19, 78, 65, 91, 75]
n = len(L)

print(L, "", sep="\n")

# Selection Sort Algorithm
for i in range(n - 1):
    selected = i
    for j in range(i, n):
        if L[j] < L[selected]:
            selected = j
    swap_elements(L, i, selected)

print(L, "", sep="\n")
