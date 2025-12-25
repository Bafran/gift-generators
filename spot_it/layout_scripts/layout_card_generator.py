"""
Generate the card image by reading in the image files and mapping according to card_metadata.json
"""

import json
from PIL import Image, ImageDraw

CARD_SIZE = 1024

def read_card_metadata(file_path):
    with open(file_path, "r") as f:
        card_data = json.load(f)
    return card_data

def generate_card_image(card_data, image_folder, output_path):
    # Create a blank white card
    card_size = (CARD_SIZE, CARD_SIZE)
    card_image = Image.new("RGBA", card_size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(card_image)

    center = (card_size[0] // 2, card_size[1] // 2)

    for item in card_data:
        image_id = item["id"]
        position = item["position"]
        angle = item["angle"]
        mass = item["mass"]

        # Load the image
        img_path = f"{image_folder}/{image_id}.png"
        img = Image.open(img_path).convert("RGBA")

        # Scale the image to have it be nominally 256 x 256 pixels, adjusted by mass
        scale_factor = (256.0 / max(img.width, img.height) * mass) * 1.0
        img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)))

        # Rotate the image
        img = img.rotate(angle * (180.0 / 3.14159265), expand=True)

        # Calculate position on the card
        pos_x = int(center[0] + position[0] - img.width // 2)
        pos_y = int(center[1] + position[1] - img.height // 2)

        # Flip the image vertically to match coordinate system
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        # Paste the image onto the card
        card_image.paste(img, (pos_x, pos_y), img)

    # Draw a disk surrounding the images
    disk_radius = CARD_SIZE // 2
    draw.ellipse(
        [center[0] - disk_radius, center[1] - disk_radius,
         center[0] + disk_radius, center[1] + disk_radius],
        outline=(0, 0, 0), width=5
    )

    # Save the final card image
    card_image.save(output_path)

def generate_card_from_metadata(card_metadata_path, image_folder, output_card_path):
    card_data = read_card_metadata(card_metadata_path)
    generate_card_image(card_data, image_folder, output_card_path)

if __name__ == "__main__":
    card_metadata_path = "card_metadata.json"
    image_folder = "icon_files"
    output_card_path = "generated_card.png"

    generate_card_from_metadata(card_metadata_path, image_folder, output_card_path)