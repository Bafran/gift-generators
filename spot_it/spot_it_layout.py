"""
Generate the Spot It! "Layout" which defines which symbols go on which cards
"""
import os
import random

from spot_it_schematic import make_deck
from layout_scripts.layout_bounding_polygon import compute_polygon_parts
from layout_scripts.layout_pymunk_sim import SimulationInstance
from layout_scripts.layout_card_generator import generate_card_from_metadata

IMAGE_DIR = "card_images"

if __name__ == "__main__":
    # Grab all symbols from IMAGE_DIR that end in .png
    image_names = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")])

    # Create the deck
    n = 7
    deck = make_deck(n, image_names)

    # Pre-compute the polygon parts for each image
    image_polygon_parts = {}
    for i, image_name in enumerate(image_names):
        image_polygon_parts[image_name] = compute_polygon_parts(os.path.join(IMAGE_DIR, image_name))

    # Create the card for each image set in the deck
    for i, image_set in enumerate(deck):
        # Randomize the masses for this card
        masses = []
        for j in range(8):
            masses.append(random.normalvariate(1.0, 0.3))
        total_mass = sum(masses)
        masses = [(m * (8.0 / total_mass)) for m in masses]

        # Create the vericies list for this card
        verticies_list = []
        for j, image_name in enumerate(image_set):
            verticies_list.append(
                (image_polygon_parts[image_name], masses[j], image_name)
            )

        # Run the simulation for this card
        sim = SimulationInstance(headless=True)
        sim.run_simulation(verticies_list, output_file=f"card_metadata.json")

        # Create the output directory if it doesn't exist
        if not os.path.exists("output_cards"):
            os.makedirs("output_cards")

        # Generate the card based on the output metadata
        generate_card_from_metadata(
            f"card_metadata.json",
            IMAGE_DIR,
            f"output_cards/card_{i+1:02d}.png"
        )