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
CANDIDATES_DIR = "candidates"
OUTPUT_DIR = "output_cards"


def choose_candidate(card_index, candidate_paths):
    """Prompt user to choose a candidate or request more candidates."""
    print(f"\nCard {card_index:02d} candidates:")
    for idx, path in enumerate(candidate_paths, start=1):
        print(f"  {idx}. {path}")

    while True:
        raw_choice = input(
            f"Choose the best layout [1-{len(candidate_paths)}] or 'x' for 3 more: "
        ).strip().lower()

        if raw_choice == "x":
            return None

        try:
            choice = int(raw_choice)
            if 1 <= choice <= len(candidate_paths):
                return choice - 1
        except ValueError:
            pass
        print("Invalid choice. Enter a candidate number or 'x'.")


def append_candidates(card_number, image_set, image_polygon_parts, candidate_paths, metadata_paths, count=3):
    """Generate and append candidate images and metadata for one card."""
    start_idx = len(candidate_paths) + 1

    for candidate_idx in range(start_idx, start_idx + count):
        # Randomize masses per candidate so each option explores a distinct layout.
        masses = []
        for _ in range(8):
            masses.append(random.normalvariate(1.0, 0.3))
        total_mass = sum(masses)
        masses = [(m * (8.0 / total_mass)) for m in masses]

        verticies_list = []
        for j, image_name in enumerate(image_set):
            verticies_list.append(
                (image_polygon_parts[image_name], masses[j], image_name)
            )

        metadata_path = f"{CANDIDATES_DIR}/card_{card_number:02d}_metadata_{candidate_idx}.json"
        candidate_path = f"{CANDIDATES_DIR}/card_{card_number:02d}_candidate_{candidate_idx}.png"

        sim = SimulationInstance(headless=True)
        sim.run_simulation(verticies_list, output_file=metadata_path)
        generate_card_from_metadata(metadata_path, IMAGE_DIR, candidate_path)

        metadata_paths.append(metadata_path)
        candidate_paths.append(candidate_path)

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

    # Create output directories if they don't exist.
    if not os.path.exists(CANDIDATES_DIR):
        os.makedirs(CANDIDATES_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Create the card for each image set in the deck
    for i, image_set in enumerate(deck):
        card_number = i + 1

        candidate_paths = []
        metadata_paths = []

        append_candidates(card_number, image_set, image_polygon_parts, candidate_paths, metadata_paths, count=3)

        while True:
            selected_idx = choose_candidate(card_number, candidate_paths)
            if selected_idx is not None:
                break

            print(f"Generating 3 additional candidates for card {card_number:02d}...")
            append_candidates(card_number, image_set, image_polygon_parts, candidate_paths, metadata_paths, count=3)

        final_card_path = f"{OUTPUT_DIR}/card_{card_number:02d}.png"
        os.replace(candidate_paths[selected_idx], final_card_path)

        for idx, path in enumerate(candidate_paths):
            if idx != selected_idx and os.path.exists(path):
                os.remove(path)

        for metadata_path in metadata_paths:
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

        print(f"Saved selected card to {final_card_path}")