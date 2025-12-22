"""
Generate the card image by reading in the image files and mapping according to card_metadata.json
"""

import json
from PIL import Image, ImageDraw

def read_card_metadata(file_path):
    with open(file_path, "r") as f:
        card_data = json.load(f)
    return card_data

def generate_card_image(card_data, image_folder, output_path):
    # Create a blank white card
    card_size = (600, 600)
    card_image = Image.new("RGBA", card_size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(card_image)

    center = (card_size[0] // 2, card_size[1] // 2)

    for item in card_data:
        print("Processing item:", item)

        image_id = item["id"]
        position = item["position"]
        angle = item["angle"]
        mass = item["mass"]

        # Load the image
        img_path = f"{image_folder}/{image_id}.png"
        print(f"Loading image from: {img_path}")
        img = Image.open(img_path).convert("RGBA")
        print(f"Image loaded, size: {img.size}")

        scale_factor = 0.1 * mass
        print(f"Scale factor: {scale_factor}, new size: ({int(img.width * scale_factor)}, {int(img.height * scale_factor)})")
        img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)))
        print("Image resized")

        # Rotate the image
        print(f"Rotating by angle: {angle}")
        img = img.rotate(angle * (180.0 / 3.14159265), expand=True)
        print("Image rotated")

        # Calculate position on the card
        pos_x = int(center[0] + position[0] - img.width // 2)
        pos_y = int(center[1] + position[1] - img.height // 2)
        print(f"Pasting at position: ({pos_x}, {pos_y})")

        # Paste the image onto the card
        card_image.paste(img, (pos_x, pos_y), img)
        print("Image pasted")

    # Save the final card image
    card_image.save(output_path)

if __name__ == "__main__":
    card_metadata_path = "card_metadata.json"
    image_folder = "icon_files"
    output_card_path = "generated_card.png"

    card_data = read_card_metadata(card_metadata_path)
    generate_card_image(card_data, image_folder, output_card_path)