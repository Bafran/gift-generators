"""
Generate the Spot It! "Layout" which defines which symbols go on which cards
"""
import os
import random
import json
import hashlib
import argparse

from spot_it_schematic import make_deck
from layout_scripts.layout_bounding_polygon import compute_polygon_parts
from layout_scripts.layout_pymunk_sim import SimulationInstance
from layout_scripts.layout_card_generator import generate_card_from_metadata
from layout_scripts.layout_tuning_gui import open_tuning_gui

IMAGE_DIR = "card_images"
CANDIDATES_DIR = "candidates"
OUTPUT_DIR = "output_cards"
POLYGON_CACHE_FILE = "polygon_parts_cache.json"


def compute_directory_md5(dir_path, suffix=".png"):
    """Compute a stable MD5 digest across file names and contents in a directory."""
    hasher = hashlib.md5()
    file_paths = []
    for name in os.listdir(dir_path):
        if name.endswith(suffix):
            file_paths.append(os.path.join(dir_path, name))

    for file_path in sorted(file_paths):
        rel_name = os.path.relpath(file_path, dir_path).replace("\\", "/")
        hasher.update(rel_name.encode("utf-8"))
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)
    return hasher.hexdigest()


def serialize_polygon_parts(polygon_parts):
    """Convert polygon tuples to JSON-safe nested lists."""
    return {
        image_name: [
            [[float(x), float(y)] for x, y in part]
            for part in parts
        ]
        for image_name, parts in polygon_parts.items()
    }


def deserialize_polygon_parts(serialized_parts):
    """Convert JSON-safe nested lists back to tuples for simulation use."""
    return {
        image_name: [
            [(float(x), float(y)) for x, y in part]
            for part in parts
        ]
        for image_name, parts in serialized_parts.items()
    }


def load_or_compute_polygon_parts(image_dir, image_names, cache_file):
    """Load precomputed polygon parts when inputs are unchanged, otherwise recompute and cache."""
    images_md5 = compute_directory_md5(image_dir)
    cache_exists = os.path.exists(cache_file)
    cached_data = None

    if cache_exists:
        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            cached_data = None

    if cached_data is not None:
        cached_md5 = cached_data.get("images_md5")
        cached_parts = cached_data.get("polygon_parts")
        if (
            cached_md5 == images_md5
            and isinstance(cached_parts, dict)
            and set(cached_parts.keys()) == set(image_names)
        ):
            print(f"Polygon cache hit ({cache_file}); loading precomputed parts.")
            return deserialize_polygon_parts(cached_parts)

    print("Polygon cache miss; recomputing all polygon parts.")
    polygon_parts = {}
    for image_name in image_names:
        polygon_parts[image_name] = compute_polygon_parts(os.path.join(image_dir, image_name))

    cache_payload = {
        "images_md5": images_md5,
        "polygon_parts": serialize_polygon_parts(polygon_parts),
    }
    with open(cache_file, "w") as f:
        json.dump(cache_payload, f, indent=2)
    print(f"Saved polygon cache to {cache_file}.")
    return polygon_parts


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


def offer_tuning(metadata_path, card_number):
    """Prompt user if they want to tune the selected card."""
    while True:
        response = input(f"\nWould you like to tune card {card_number:02d}? (y/n): ").strip().lower()
        if response == "y":
            open_tuning_gui(metadata_path, IMAGE_DIR, card_number)
            return True
        elif response == "n":
            return False
        else:
            print("Invalid choice. Enter 'y' or 'n'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Spot It card layouts and optionally start from a specific card number."
    )
    parser.add_argument(
        "--card",
        type=int,
        default=1,
        help="One-indexed card number to start from (default: 1).",
    )
    args = parser.parse_args()

    # Grab all symbols from IMAGE_DIR that end in .png
    image_names = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(".png")])

    # Create the deck
    n = 7
    deck = make_deck(n, image_names)

    if args.card < 1 or args.card > len(deck):
        parser.error(f"--card must be between 1 and {len(deck)} (got {args.card}).")

    image_polygon_parts = load_or_compute_polygon_parts(IMAGE_DIR, image_names, POLYGON_CACHE_FILE)

    # Create output directories if they don't exist.
    if not os.path.exists(CANDIDATES_DIR):
        os.makedirs(CANDIDATES_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Create the card for each image set in the deck
    for card_number, image_set in enumerate(deck[args.card - 1 :], start=args.card):

        candidate_paths = []
        metadata_paths = []

        append_candidates(card_number, image_set, image_polygon_parts, candidate_paths, metadata_paths, count=3)

        while True:
            selected_idx = choose_candidate(card_number, candidate_paths)
            if selected_idx is not None:
                break

            print(f"Generating 3 additional candidates for card {card_number:02d}...")
            append_candidates(card_number, image_set, image_polygon_parts, candidate_paths, metadata_paths, count=3)

        selected_metadata_path = metadata_paths[selected_idx]
        
        # Offer tuning option
        offer_tuning(selected_metadata_path, card_number)
        
        # Regenerate the final card image from the (possibly tuned) metadata
        generate_card_from_metadata(selected_metadata_path, IMAGE_DIR, f"{OUTPUT_DIR}/card_{card_number:02d}.png")

        final_card_path = f"{OUTPUT_DIR}/card_{card_number:02d}.png"
        print(f"Saved final card to {final_card_path}")
        
        # Clean up candidate files
        for idx, path in enumerate(candidate_paths):
            if os.path.exists(path):
                os.remove(path)

        for metadata_path in metadata_paths:
            if os.path.exists(metadata_path):
                os.remove(metadata_path)