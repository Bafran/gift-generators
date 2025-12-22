Approach:

- Generate N random points on the unit circle.
- Each point then gets randomly assigned with a size S, up to some maximum size.
- In descending order of the point size, transform the point into a circle with size S. Each time the transformation is applied, check if you are already within another point's radius. If yes, move out of the radius in the radial direction of the unit circle until the point is out of the other point's radius, then try to apply the transform again.
- In the case where applying the transform now puts the point outside of the unit circle entirely, then move in the direction of greatest whitespace until you are no longer colliding with any other circle or the unit circle's edge.

The point with the greatest whitespace is some arbitrary point on the unit circle that has the largest free radius, defined as the distance from the point to the next boundary. We can compute this by discretizing the unit circle and performing a BFS from every point.