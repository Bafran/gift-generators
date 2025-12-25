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

def compute_bounding_polygon(image_path, threshold=0, tolerance=1.0):
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
    simplified_contour = measure.approximate_polygon(largest_contour, tolerance=tolerance)

    # Convert contour coordinates to (x, y) tuples
    bounding_polygon = [(x, y) for y, x in simplified_contour]

    # Flip over the y-axis to match image coordinates
    bounding_polygon = [(x, img_data.shape[0] - y) for x, y in bounding_polygon]

    # Recenter the polygon to the origin by subtracting 1/2 of the x and 1/2 of the y of the original image size
    center_x = img_data.shape[1] / 2.0
    center_y = img_data.shape[0] / 2.0
    bounding_polygon = [(x - center_x, y - center_y) for x, y in bounding_polygon]

    # Normalize the polygon to fit within a box
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

def plot(bounding_polygon, convex_parts, image_path):
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

    # Overlay the original image and scale it the same way card gen does
    img = Image.open(image_path).convert("RGBA")
    mass = 1.0  # Assuming mass is defined somewhere; replace with actual value if needed
    # Scale the image to have it be nominally 256 x 256 pixels, adjusted by mass
    scale_factor = (256.0 / max(img.width, img.height) * mass) * 1.0
    img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)))
    img_data = np.array(img)
    padding = 50
    padded_img_data = np.zeros((img_data.shape[0] + 2 * padding,
                                img_data.shape[1] + 2 * padding,
                                4), dtype=img_data.dtype)
    padded_img_data[padding:-padding, padding:-padding, :] = img_data
    img_data = padded_img_data
    extent = [-img_data.shape[1]//2, img_data.shape[1]//2, -img_data.shape[0]//2, img_data.shape[0]//2]
    plt.imshow(img_data, extent=extent)

    # Save image instead of showing it
    plt.savefig("bounding_polygon_output.png", bbox_inches='tight', pad_inches=0)

def compute_polygon_parts(image_path, tolerance=0.5):
    bounding_polygon = compute_bounding_polygon(image_path, tolerance=tolerance)
    convex_parts = break_polygon_into_convex_parts(bounding_polygon)
    return convex_parts

if __name__ == "__main__":
    image_path = "/home/achinoy/code/gift_generators/spot_it/tests/icon_files/cutter.png"
    bounding_polygon = compute_bounding_polygon(image_path, tolerance=1.0)
    convex_parts = break_polygon_into_convex_parts(bounding_polygon)
    plot(bounding_polygon, convex_parts, image_path)