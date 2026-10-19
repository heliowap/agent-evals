def sum_range(a, b):
    """Sum integers from a to b inclusive."""
    total = 0
    for i in range(a, b):
        total += i
    return total


def avg(xs):
    return sum(xs) / len(xs)
