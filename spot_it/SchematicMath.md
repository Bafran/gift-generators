# Math behind Spot It! game
https://joelgrus.com/2015/06/12/on-the-mathematics-of-spot-it/

# Rules
Each pair of cards has exactly one symbol in common.

# Math Explanation
## Finite Projective Planes

Let's start with a regular grid. For example, take a 7×7 grid of points, totalling 49 points. We can treat this as a regular x-y coordinate plane, where each point represents a symbol that could appear on our cards.

### Core Concept: Lines as Cards

To construct our Spot It! deck, we use a fundamental geometry concept: **any two non-parallel lines on a 2D plane will intersect at exactly one point**. This perfectly matches our goal where each pair of cards needs to have exactly one symbol in common.

We devise a system where:
- **Points = Symbols** (images on the cards)
- **Lines = Cards** (collections of symbols)

Each point that a line passes through represents a symbol that appears on that card.

### Constructing Lines on the Grid

How do we generate all possible lines through our grid? Since this is a finite grid with natural number coordinates, we can enumerate all possible line functions.

For our 7×7 case, consider the standard line equation `y = mx + b`:
- Slope `m` has 7 possibilities: {0, 1, 2, 3, 4, 5, 6}
- Y-intercept `b` has 7 possibilities: {0, 1, 2, 3, 4, 5, 6}
- This gives us 7 × 7 = 49 different lines

**Important**: All arithmetic is done modulo 7 (mod 7). This means:
- When calculating `y = mx + b`, we take the result mod 7
- For example: if `m = 3, x = 5, b = 4`, then `y = (3×5 + 4) mod 7 = 19 mod 7 = 5`

### Handling Parallel Lines: A Crucial Property of the Projective Plane

The problem with our current setup is that parallel lines never intersect, which would violate the case we made earlier for every line interesecting another exactly once.

This brings us to a crucial concept of the **finite projective plane**: we add "points at infinity."

In a projective plane:
- All lines with the same slope are considered to intersect at a "point at infinity"
- We create one point at infinity for each possible slope value
- We also add a special "line at infinity" that contains all these points at infinity

For our 7×7 grid:
- We have 7 points at infinity (one for each slope: 0, 1, 2, 3, 4, 5, 6)
- We add 1 line at infinity that contains all 7 points at infinity
- We also need vertical lines (infinite slope)

### Complete Card Construction

Here's how we build the complete deck:

**1. Regular sloped lines** (49 cards):
- For each combination of `m in {0,1,2,3,4,5,6}` and `b in {0,1,2,3,4,5,6}`
- Create a line with equation `y = mx + b (mod 7)`
- Each line passes through 7 grid points
- Add the "point at infinity for slope m" to each card
- **Result**: 49 cards, each with 8 symbols (7 grid points + 1 point at infinity)

**2. Vertical lines** (7 cards):
- For each `x in {0,1,2,3,4,5,6}`
- Create a vertical line at that x-coordinate
- Each line contains the 7 points: `(x,0), (x,1), ..., (x,6)`
- Add the "point at infinity for vertical lines"
- **Result**: 7 cards, each with 8 symbols

**3. The line at infinity** (1 card):
- Contains all 8 points at infinity (7 for slopes 0-6, plus 1 for vertical lines)
- **Result**: 1 card with 8 symbols

### Final Deck

- **Total cards**: 49 + 7 + 1 = **57 cards**
- **Symbols per card**: **8 symbols**
- **Total unique symbols**: 49 grid points + 8 points at infinity = **57 symbols**