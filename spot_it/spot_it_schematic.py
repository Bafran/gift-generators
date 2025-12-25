# Generate the Spot It! "Schematic" which defines which symbols go on which cards

def ordinary_points(n):
    """Number of ordinary points in a projective plane of order n."""
    return [(x, y)
            for x in range(n)
            for y in range(n)]

def points_at_infinity(n):
    """infinite points are just the numbers 0 to n - 1
    (corresponding to the infinity where lines with that slope meet)
    and infinity infinity (where vertical lines meet)"""
    return list(range(n)) + ["infinity"]

def ordinary_line(m, b, n):
    """returns the ordinary line through (0, b) with slope m
    in the finite projective plan of degree n
    includes 'infinity m'"""
    return [(x, (m * x + b) % n) for x in range(n)] + [m]

def vertical_line(x, n):
    """returns the vertical line with the specified x-coordinate
    in the finite projective plane of degree n
    includes 'infinity infinity'"""
    return [(x, y) for y in range(n)] + ["∞"]

def line_at_infinity(n):
    """the line at infinity just contains the points at infinity"""
    return points_at_infinity(n)

def all_points(n):
    return ordinary_points(n) + points_at_infinity(n)

def all_lines(n):
    return ([ordinary_line(m, b, n) for m in range(n) for b in range(n)] +
            [vertical_line(x, n) for x in range(n)] +
            [line_at_infinity(n)])

def make_deck(n, pics):
    if len(pics) != n * n + n + 1:
        raise ValueError(f"Expected {n * n + n + 1} pics for order {n}, got {len(pics)}")

    points = all_points(n)

    # create a mapping from point to pic
    mapping = { point : pic
                for point, pic in zip(points, pics) }

    # and return the remapped cards
    return [list(map(mapping.get, line)) for line in all_lines(n)]


if __name__ == "__main__":
    # Generate a Spot It! deck for n=7 (standard size)
    n = 7
    
    # Total symbols needed: n² + n + 1 = 57 for n=7
    num_symbols = n * n + n + 1
    
    # Create symbol names
    symbols = [f"symbol_{i}" for i in range(num_symbols)]
    
    # Generate the deck
    deck = make_deck(n, symbols)
    
    # Print each card
    print(f"Generated {len(deck)} cards with {len(deck[0])} symbols each:\n")
    for i, card in enumerate(deck, 1):
        print(f"Card {i}: {card}")
