"""
A test script that takes in a png image and computes a bounding polygon around the
non-transparent pixels using skimage.
"""

import numpy as np
from PIL import Image
from skimage import measure
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.ops import triangulate

def compute_bounding_polygon(image_path, threshold=0, resolution=1.0):
    # Load image and convert to RGBA
    img = Image.open(image_path).convert("RGBA")
    img_data = np.array(img)

    # Add transparant padding around the image
    padding = 50
    padded_img_data = np.zeros((img_data.shape[0] + 2 * padding,
                                img_data.shape[1] + 2 * padding,
                                4), dtype=img_data.dtype)
    padded_img_data[padding:-padding, padding:-padding, :] = img_data
    img_data = padded_img_data

    # Create a binary mask where non-transparent pixels are 1
    alpha_channel = img_data[:, :, 3]
    binary_mask = (alpha_channel > threshold).astype(np.uint8)

    # Use marching squares to find contours
    contours = measure.find_contours(binary_mask, 0.5)

    # Find the largest contour
    largest_contour = max(contours, key=len)

    # Simplify the contour
    simplified_contour = measure.approximate_polygon(largest_contour, tolerance=resolution)

    # Convert contour coordinates to (x, y) tuples
    bounding_polygon = [(x, y) for y, x in simplified_contour]

    # Recenter the polygon to the origin by subtracting the centroid
    centroid_x = np.mean([x for x, y in bounding_polygon])
    centroid_y = np.mean([y for x, y in bounding_polygon])
    bounding_polygon = [(x - centroid_x, y - centroid_y) for x, y in bounding_polygon]

    # Normalize the polygon to fit within a 50x50 box
    max_extent = max(max(abs(x) for x, y in bounding_polygon), max(abs(y) for x, y in bounding_polygon))
    scale_factor = 128.0 / max_extent
    bounding_polygon = [(x * scale_factor, y * scale_factor) for x, y in bounding_polygon]

    # Don't return the last point
    return bounding_polygon[:-1]

def break_polygon_into_convex_parts(bounding_polygon):
    """Break a possibly concave polygon into convex parts using ear clipping."""
    poly = Polygon(bounding_polygon)
    triangles = triangulate(poly, tolerance=1)

    convex_parts = []
    for triangle in triangles:
        # Only keep triangles that are inside the original polygon
        # Check if the centroid is inside the polygon
        if poly.contains(triangle.centroid) or poly.intersects(triangle):
            # Also verify the triangle is mostly inside (at least 80% area overlap)
            intersection = poly.intersection(triangle)
            if intersection.area > 0.8 * triangle.area:
                coords = list(triangle.exterior.coords)[:-1]  # Exclude the repeated last point
                convex_parts.append(coords)

    return convex_parts

def plot(bounding_polygon, convex_parts):
    # Plot the bounding polygon and its convex parts
    plt.figure()
    if convex_parts is not None:
        for part in convex_parts:
            xs, ys = zip(*part)
            plt.fill(xs, ys, alpha=0.5)
    plt.axis('equal')

    # Draw bounding polygon outline
    xs, ys = zip(*bounding_polygon)
    plt.plot(xs + (xs[0],), ys + (ys[0],), color='black', linewidth=2)

    # Save image instead of showing it
    plt.savefig("bounding_polygon_output.png", bbox_inches='tight', pad_inches=0)

def compute_polygon_parts(image_path, resolution=1.0):
    bounding_polygon = compute_bounding_polygon(image_path, resolution)
    convex_parts = break_polygon_into_convex_parts(bounding_polygon)
    return convex_parts

if __name__ == "__main__":
    # image_path = "/home/achinoy/code/gift_generators/spot_it/testhorse.png"
    image_path = "/home/achinoy/code/gift_generators/spot_it/tests/icon_files/push-pin.png"
    bounding_polygon = compute_bounding_polygon(image_path, resolution=2.0)
    convex_parts = break_polygon_into_convex_parts(bounding_polygon)
    plot(bounding_polygon, convex_parts)