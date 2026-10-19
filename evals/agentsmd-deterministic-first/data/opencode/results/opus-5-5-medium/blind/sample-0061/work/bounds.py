def clamp(value, low, high):
    if low > high:
        raise ValueError(f"low ({low!r}) must not be greater than high ({high!r})")
    return max(low, min(high, value))
