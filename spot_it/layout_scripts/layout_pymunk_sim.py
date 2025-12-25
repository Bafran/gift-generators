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
import random

from layout_scripts.layout_bounding_polygon import compute_polygon_parts

def is_valid_polygon(vertices, min_area=1.0):
    """Check if a polygon has sufficient area to be valid for physics simulation."""
    if len(vertices) < 3:
        return False
    # Calculate area using shoelace formula
    area = 0.0
    for i in range(len(vertices)):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % len(vertices)]
        area += x1 * y2 - x2 * y1
    area = abs(area) / 2.0
    return area >= min_area

class SimulationInstance:
    def __init__(self, headless=True, width=1024, height=1024):
        self.headless = headless
        self.width = width
        self.height = height
        self.disk_radius = min(self.width, self.height) // 2
        self.center = (self.width // 2, self.height // 2)

        # Initialize pygame
        pygame.init()
        if not self.headless:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Pymunk Polygons in Disk Simulation")
        else:
            self.screen = pygame.Surface((self.width, self.height))
        self.clock = pygame.time.Clock()

        # Initialize pymunk space
        self.space = pymunk.Space() # No gravity in space, defaults to (0, 0)
        self.space.damping = 0.7  # Add damping to help system reach steady state (1.0 = no damping, 0.0 = full damping)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)

        # Simulation parameters
        self.gravity_strength = 1
        self.repulsion_strength = 1E7
        self.velocity_threshold = 1.5 # steady state threshold
        self.fps = 60
        self.gravity_bias_index = None

        self.sim_bodies = []
        self.static_points = []  # List of (position, mass) tuples for static repulsion points

    def create_polygon(self, vertices, position, scale_factor=1.0, rotation=0.0):
        # Single polygon
        padding_factor = 1.05
        scaled_vertices = [(x * scale_factor * padding_factor, y * scale_factor * padding_factor) for x, y in vertices]
        moment = pymunk.moment_for_poly(scale_factor, scaled_vertices)
        body = pymunk.Body(scale_factor, moment)
        body.position = position
        body.angle = rotation
        shape = pymunk.Poly(body, scaled_vertices)
        shape.friction = 0.5
        self.space.add(body, shape)
        self.sim_bodies.append((body, shape))

    def create_compound_polygon(self, vertices, position, scale_factor=1.0, rotation=0.0):
        # Compound shape - multiple polygon parts
        padding_factor = 1.05
        scaled_parts = [[(x * scale_factor * padding_factor, y * scale_factor * padding_factor) for x, y in part] for part in vertices]
        
        # Filter out degenerate polygons (too small area)
        valid_parts = [part for part in scaled_parts if is_valid_polygon(part, min_area=1.0)]
        
        if not valid_parts:
            exit()("Error: No valid polygon parts found for compound shape.")
        
        # Calculate total moment as sum of all parts
        mass_per_part = scale_factor / len(valid_parts)
        total_moment = sum(pymunk.moment_for_poly(mass_per_part, verts) for verts in valid_parts)
        body = pymunk.Body(scale_factor, total_moment)
        body.position = position
        body.angle = rotation
        shapes = []
        for part_vertices in valid_parts:
            shape = pymunk.Poly(body, part_vertices)
            shape.friction = 0.5
            shapes.append(shape)
        self.space.add(body, *shapes)
        self.sim_bodies.append((body, shapes[0]))

    def create_static_repulsion_points(self, num_points=5, mass_range=(0.1, 0.3)):
        """Create random static points that provide additional repulsion forces."""
        for _ in range(num_points):
            # Random position within the disk
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(0, self.disk_radius * 0.8)  # Keep within 80% of disk radius
            position = (self.center[0] + radius * math.cos(angle), 
                       self.center[1] + radius * math.sin(angle))
            mass = random.uniform(*mass_range)
            self.static_points.append((position, mass))
        print(f"Created {num_points} static repulsion points")

    def create_all_bodies(self, verticies_list):
        for i, (vertices, scale_factor, image_name) in enumerate(verticies_list):
            angle = i * (2 * math.pi / len(verticies_list))
            radius = self.disk_radius / 2  # Place polygons at half the disk radius
            position = (self.center[0] + radius * math.cos(angle), self.center[1] + radius * math.sin(angle))

            # Apply a random rotation
            rotation = random.uniform(0, 2 * math.pi)

            # Check if vertices is a list of polygon parts (compound shape) or a single polygon
            if isinstance(vertices[0][0], (list, tuple)):
                self.create_compound_polygon(vertices, position, scale_factor, rotation)
            else:
                self.create_polygon(vertices, position, scale_factor, rotation)

        # Assign a random gravity bias index
        self.gravity_bias_index = random.randint(0, len(verticies_list) - 1)
        print(f"Gravity bias applied to object index: {self.gravity_bias_index}")

    def apply_radial_gravity(self):
        """Apply gravitational attraction towards the center for all bodies"""
        for i, (body, shape) in enumerate(self.sim_bodies):
            dx = self.center[0] - body.position.x
            dy = self.center[1] - body.position.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                direction_x = dx / distance
                direction_y = dy / distance
                force = self.gravity_strength * distance

                if self.gravity_bias_index is not None and i == self.gravity_bias_index:
                    force *= 2.0  # Apply a stronger force for the biased object

                body.apply_force_at_world_point((direction_x * force, direction_y * force), body.position)

    def apply_repulsion_force(self):
        """Apply a repulsion force to each body from every other body and static points"""
        for i, (body_a, shape_a) in enumerate(self.sim_bodies):
            # Repulsion from other bodies
            for j, (body_b, shape_b) in enumerate(self.sim_bodies):
                if i != j:
                    dx = body_b.position.x - body_a.position.x
                    dy = body_b.position.y - body_a.position.y
                    distance = math.sqrt(dx**2 + dy**2)
                    mass_factor = ((body_a.mass + body_b.mass) ** 1.5) / 4.0
                    
                    if distance > 0:
                        direction_x = dx / distance
                        direction_y = dy / distance
                        force = (self.repulsion_strength / (distance ** 2)) * mass_factor
                        body_a.apply_force_at_world_point((-direction_x * force, -direction_y * force), body_a.position)
            
            # Repulsion from static points
            for static_pos, static_mass in self.static_points:
                dx = static_pos[0] - body_a.position.x
                dy = static_pos[1] - body_a.position.y
                distance = math.sqrt(dx**2 + dy**2)
                mass_factor = ((body_a.mass + static_mass) ** 1.5) / 4.0
                
                if distance > 0:
                    direction_x = dx / distance
                    direction_y = dy / distance
                    force = (self.repulsion_strength / (distance ** 2)) * mass_factor
                    body_a.apply_force_at_world_point((-direction_x * force, -direction_y * force), body_a.position)

    def check_steady_state(self):
        """Check if all bodies are below a certain velocity threshold"""
        for body, _ in self.sim_bodies:
            if body.velocity.length > self.velocity_threshold:
                return False
        return True

    def run_simulation(self, verticies_list, output_file="card_metadata.json", num_static_points=3):
        # Create static repulsion points for more organic layouts
        self.create_static_repulsion_points(num_static_points)
        
        # Create all bodies in the simulation (pictures)
        self.create_all_bodies(verticies_list)

        # Create a wall around the disk to contain the polygons
        static_body = self.space.static_body
        num_segments = 100
        for i in range(num_segments):
            angle1 = (2 * math.pi / num_segments) * i
            angle2 = (2 * math.pi / num_segments) * (i + 1)
            p1 = (self.center[0] + self.disk_radius * math.cos(angle1),
                  self.center[1] + self.disk_radius * math.sin(angle1))
            p2 = (self.center[0] + self.disk_radius * math.cos(angle2),
                  self.center[1] + self.disk_radius * math.sin(angle2))
            segment = pymunk.Segment(static_body, p1, p2, 1.0)
            segment.friction = 1.0
            self.space.add(segment)
        
        dt = 1.0 / self.fps

        iteration = 0
        while True:
            if not self.headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return None
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return None
                            
                # Clear screen and draw
                self.screen.fill((255, 255, 255))
                pygame.draw.circle(self.screen, (200, 200, 200), self.center, self.disk_radius, 2)
                
                # Draw static repulsion points
                for static_pos, static_mass in self.static_points:
                    radius = max(3, int(static_mass * 10))  # Scale radius by mass
                    pygame.draw.circle(self.screen, (255, 100, 100), (int(static_pos[0]), int(static_pos[1])), radius)
                
                self.space.debug_draw(self.draw_options)

                pygame.display.flip()
                self.clock.tick(self.fps)

            self.apply_radial_gravity()
            self.apply_repulsion_force()
            self.space.step(dt)
            
            if self.check_steady_state():
                print(f"Steady state reached after {iteration} iterations.")
                break
            
            iteration += 1
            
            # Safety limit to prevent infinite loops
            if iteration > 100000:
                print(f"Maximum iterations reached without steady state.")
                break
        
        # Build metadata
        card_data = []
        for i, (body, shape) in enumerate(self.sim_bodies):
            card_data.append({
                "id": verticies_list[i][2],
                "position": [body.position.x - self.center[0], body.position.y - self.center[1]],
                "angle": body.angle,
                "mass": body.mass
            })
        
        # Save to file
        with open(output_file, "w") as f:
            json.dump(card_data, f, indent=4)

        return card_data
    
def run_pymunk_simulation(verticies_list):
    sim = SimulationInstance(headless=True)
    return sim.run_simulation(verticies_list)

if __name__ == "__main__":
    image_path = "/home/achinoy/code/gift_generators/spot_it/tests/icon_files"

    # Come up with the masses of each object randomly for variety
    # Normalize them so that they still add up to the same total mass (8 for 8 cards)
    masses = []

    for i in range(8):
        masses.append(random.normalvariate(1.0, 0.3))

    total_mass = sum(masses)
    masses = [(m * (8.0 / total_mass)) for m in masses]

    verticies_list = [
        (compute_polygon_parts(image_path + "/batteries.png"), masses[0], "batteries"),
        (compute_polygon_parts(image_path + "/clock.png"), masses[1], "clock"),
        (compute_polygon_parts(image_path + "/computer.png"), masses[2], "computer"),
        (compute_polygon_parts(image_path + "/cutter.png"), masses[3], "cutter"),
        (compute_polygon_parts(image_path + "/lamp.png", tolerance=0.1), masses[4], "lamp"),
        (compute_polygon_parts(image_path + "/push-pin.png"), masses[5], "push-pin"),
        (compute_polygon_parts(image_path + "/ruler.png"), masses[6], "ruler"),
        (compute_polygon_parts(image_path + "/stapler-remover.png"), masses[7], "stapler-remover"),
    ]

    sim = SimulationInstance(headless=True)
    sim.run_simulation(verticies_list)