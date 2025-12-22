"""
A Pymunk simulation that creates various polygon shapes arranged in a disk,
applies radial gravitational attraction towards the center, and repulsion forces
between the polygons to help them settle into a steady state without overlapping.
"""

import pygame
import pymunk
import pymunk.pygame_util
import math
import json

from bounding_polygon_test import compute_polygon_parts

# Initialize pygame
pygame.init()
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pymunk Polygons in Disk Simulation")
clock = pygame.time.Clock()

# Initialize pymunk space
space = pymunk.Space() # No gravity in space, defaults to (0, 0)
space.damping = 0.7  # Add damping to help system reach steady state (1.0 = no damping, 0.0 = full damping)

# Drawing options
draw_options = pymunk.pygame_util.DrawOptions(screen)

# Center of the disk
center = (WIDTH // 2, HEIGHT // 2)
disk_radius = 300

def create_polygon(vertices, position, mass=1.0):
    """Create a polygon body and shape"""
    # Calculate moment of inertia for the polygon
    moment = pymunk.moment_for_poly(mass, vertices)
    body = pymunk.Body(mass, moment)
    body.position = position
    
    shape = pymunk.Poly(body, vertices)
    shape.friction = 0.5
    
    space.add(body, shape)
    return body, shape

def create_compound_polygon(polygon_parts, position, mass=1.0):
    """Create a single body with multiple polygon shapes (for compound objects like decomposed concave shapes)"""
    # Calculate total moment as sum of all parts
    total_moment = sum(pymunk.moment_for_poly(mass / len(polygon_parts), verts) for verts in polygon_parts)
    
    body = pymunk.Body(mass, total_moment)
    body.position = position
    
    shapes = []
    for vertices in polygon_parts:
        shape = pymunk.Poly(body, vertices)
        shape.friction = 0.5
        shapes.append(shape)
    
    space.add(body, *shapes)
    return body, shapes

# Create 8 different polygons
bodies = []

image_path = "/home/achinoy/code/gift_generators/spot_it/tests/icon_files"

verticies_list = [
    # ([(-20, -15), (20, -15), (0, 20)], 5.0),  # Triangle
    # ([(-20, -20), (20, -20), (20, 20), (-20, 20)], 1.0),  # Square
    # ([(25 * math.cos(i * 2 * math.pi / 5), 25 * math.sin(i * 2 * math.pi / 5)) for i in range(5)], 1.0),  # Pentagon
    # ([(20 * math.cos(i * 2 * math.pi / 6), 20 * math.sin(i * 2 * math.pi / 6)) for i in range(6)], 1.0),  # Hexagon
    # ([(-30, -15), (30, -15), (30, 15), (-30, 15)], 1.0),  # Rectangle (horizontal)
    # ([(-15, -30), (15, -30), (15, 30), (-15, 30)], 1.0),  # Rectangle (vertical)
    # ([(-25, -15), (25, -15), (15, 15), (-15, 15)], 1.0),  # Trapezoid
    # ([(0, -25), (20, 0), (0, 25), (-20, 0)], 1.0),  # Diamond
    # (compute_polygon_parts(image_path, resolution=2.0), 1.0) # Horse
    (compute_polygon_parts(image_path + "/batteries.png", resolution=2.0), 1.0, "batteries"),
    (compute_polygon_parts(image_path + "/clock.png", resolution=2.0), 3.0, "clock"),
    (compute_polygon_parts(image_path + "/computer.png", resolution=2.0), 1.0, "computer"),
    (compute_polygon_parts(image_path + "/cutter.png", resolution=2.0), 1.0, "cutter"),
    (compute_polygon_parts(image_path + "/lamp.png", resolution=2.0), 1.0, "lamp"),
    (compute_polygon_parts(image_path + "/push-pin.png", resolution=2.0), 1.0, "push-pin"),
    (compute_polygon_parts(image_path + "/ruler.png", resolution=2.0), 1.0, "ruler"),
    (compute_polygon_parts(image_path + "/stapler-remover.png", resolution=2.0), 1.0, "stapler-remover"),
]

for i, (vertices, scale_factor, image_name) in enumerate(verticies_list):
    angle = i * (2 * math.pi / len(verticies_list))

    # Our disk is of radius 300, so we'll make our polygons with a radius of 150 from the center
    radius = 150
    position = (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))

    # Check if vertices is a list of polygon parts (compound shape) or a single polygon
    if isinstance(vertices[0][0], (list, tuple)):
        # Compound shape - multiple polygon parts
        scaled_parts = [[(x * scale_factor, y * scale_factor) for x, y in part] for part in vertices]
        body, shapes = create_compound_polygon(scaled_parts, position, mass=scale_factor)
        # Store the body with the first shape for compatibility
        bodies.append((body, shapes[0]))
    else:
        # Single polygon
        scaled_vertices = [(x * scale_factor, y * scale_factor) for x, y in vertices]
        poly = create_polygon(scaled_vertices, position, mass=scale_factor)
        bodies.append(poly)

def apply_radial_gravity():
    """Apply gravitational attraction towards the center for all bodies"""
    gravity_strength = 1  # Adjust this to change attraction strength
    for body, shape in bodies:
        # Calculate vector from body to center
        dx = center[0] - body.position.x
        dy = center[1] - body.position.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:  # Avoid division by zero
            # Normalize the direction vector
            direction_x = dx / distance
            direction_y = dy / distance
            
            # Apply force towards center (proportional to distance)
            force = gravity_strength * distance
            body.apply_force_at_world_point((direction_x * force, direction_y * force), body.position)

def apply_repulsion_force():
    """Apply a repulsion force to each body from every other body to reach a steady state with some gap between bodies"""
    repulsion_strength = 100000
    for i, (body_a, shape_a) in enumerate(bodies):
        for j, (body_b, shape_b) in enumerate(bodies):
            if i != j:
                # Calculate vector from body_a to body_b
                dx = body_b.position.x - body_a.position.x
                dy = body_b.position.y - body_a.position.y
                distance = math.sqrt(dx**2 + dy**2)

                # Calculate a mass factor to increase repulsion for larger masses
                mass_factor = ((body_a.mass + body_b.mass) ** 2) / 4.0  # Average mass squared
                
                if distance > 0:  # Avoid division by zero
                    # Normalize the direction vector
                    direction_x = dx / distance
                    direction_y = dy / distance
                    
                    # Apply repulsion force away from each other (inversely proportional to distance)
                    # Also, create a stronger repulsion force for objects with large mass
                    force = (repulsion_strength / (distance ** 2)) * mass_factor
                    body_a.apply_force_at_world_point((-direction_x * force, -direction_y * force), body_a.position)

def check_steady_state():
    """Check if all bodies are below a certain velocity threshold"""
    velocity_threshold = 1.5
    for body, _ in bodies:
        if body.velocity.length > velocity_threshold:
            return False
    return True

FPS = 60

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Apply radial gravity to all bodies
    # This is the attraction force towards the center of the disk
    apply_radial_gravity()

    # Apply repulsion forces between bodies
    apply_repulsion_force()

    # Step the physics simulation
    dt = 1.0 / FPS
    space.step(dt)
    
    # Clear screen
    screen.fill((255, 255, 255))
    
    # Draw the disk boundary
    pygame.draw.circle(screen, (200, 200, 200), center, disk_radius, 2)
    
    # Draw pymunk objects
    space.debug_draw(draw_options)

    # Print out if we've reached steady state
    if check_steady_state():
        print("Steady state reached.")
        running = False
        # Save the card metadata to a JSON file
        # We want to know the positions, scales, and rotations of each polygon
        # Construct JSON data
        card_data = []
        for i, (body, shape) in enumerate(bodies):
            card_data.append({
                "id": verticies_list[i][2],  # Use image name as ID # TODO: Fix this hack
                "position": [body.position.x - center[0], body.position.y - center[1]],  # Center relative position
                "angle": body.angle,
                "mass": body.mass
            })
        with open("card_metadata.json", "w") as f:
            json.dump(card_data, f, indent=4)
    
    # Update display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
