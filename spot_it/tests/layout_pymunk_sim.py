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

from layout_bounding_polygon import compute_polygon_parts

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

        self.sim_bodies = []

    def create_polygon(self, vertices, position, scale_factor=1.0, rotation=0.0):
        # Single polygon
        scaled_vertices = [(x * scale_factor, y * scale_factor) for x, y in vertices]
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
        scaled_parts = [[(x * scale_factor, y * scale_factor) for x, y in part] for part in vertices]
        # Calculate total moment as sum of all parts
        total_moment = sum(pymunk.moment_for_poly(scale_factor / len(scaled_parts), verts) for verts in scaled_parts)
        body = pymunk.Body(scale_factor, total_moment)
        body.position = position
        body.angle = rotation
        shapes = []
        for part_vertices in scaled_parts:
            shape = pymunk.Poly(body, part_vertices)
            shape.friction = 0.5
            shapes.append(shape)
        self.space.add(body, *shapes)
        self.sim_bodies.append((body, shapes[0]))

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

    def apply_radial_gravity(self):
        """Apply gravitational attraction towards the center for all bodies"""
        for body, shape in self.sim_bodies:
            dx = self.center[0] - body.position.x
            dy = self.center[1] - body.position.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                direction_x = dx / distance
                direction_y = dy / distance
                force = self.gravity_strength * distance
                body.apply_force_at_world_point((direction_x * force, direction_y * force), body.position)

    def apply_repulsion_force(self):
        """Apply a repulsion force to each body from every other body"""
        for i, (body_a, shape_a) in enumerate(self.sim_bodies):
            for j, (body_b, shape_b) in enumerate(self.sim_bodies):
                if i != j:
                    dx = body_b.position.x - body_a.position.x
                    dy = body_b.position.y - body_a.position.y
                    distance = math.sqrt(dx**2 + dy**2)
                    mass_factor = ((body_a.mass + body_b.mass) ** 1.25) / 4.0
                    
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

    def run_simulation(self, verticies_list, output_file="card_metadata.json"):
        # Create all bodies in the simulation
        self.create_all_bodies(verticies_list)
        
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
        masses.append(random.uniform(0.5, 1.5))

    total_mass = sum(masses)
    masses = [m * (8.0 / total_mass) for m in masses]

    verticies_list = [
        (compute_polygon_parts(image_path + "/batteries.png", resolution=2.0), masses[0], "batteries"),
        (compute_polygon_parts(image_path + "/clock.png", resolution=2.0), masses[1], "clock"),
        (compute_polygon_parts(image_path + "/computer.png", resolution=2.0), masses[2], "computer"),
        (compute_polygon_parts(image_path + "/cutter.png", resolution=2.0), masses[3], "cutter"),
        (compute_polygon_parts(image_path + "/lamp.png", resolution=2.0), masses[4], "lamp"),
        (compute_polygon_parts(image_path + "/push-pin.png", resolution=2.0), masses[5], "push-pin"),
        (compute_polygon_parts(image_path + "/ruler.png", resolution=2.0), masses[6], "ruler"),
        (compute_polygon_parts(image_path + "/stapler-remover.png", resolution=2.0), masses[7], "stapler-remover"),
    ]

    sim = SimulationInstance(headless=False)
    sim.run_simulation(verticies_list)