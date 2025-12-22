import requests
import numpy as np
from PIL import Image
from collections import Counter
import matplotlib.pyplot as plt
from typing import Dict, Tuple, List
import json
import os
from pathlib import Path

# API Configuration
API_KEY = os.getenv('REBRICKABLE_API_KEY')
API_BASE_URL = 'https://rebrickable.com/api/v3/lego/elements/'
CACHE_FILE = 'color_cache.json'

# TODO: Update these element IDs to be the flat tiles instead of stubbed tiles
element_ids = {
  302421,
  6469084,
  6330584,
  6186012,
  6357797,
  4221744,
  6215606,
  4524929,
  6194729,
  6073040,
  4549436,
  4159553,
  6069887,
  302424,
  6058014,
  6058245,
  4621557,
  6566896,
  6401817,
  302428,
  6055169,
  6099189,
  6058016,
  6213778,
  6097493,
  6151664,
  302426,
  302423,
  6184484,
  4179826,
  6257079,
  4184108,
  6231376,
  4619521,
  6099363,
  6096942,
  6217797,
  4539114,
  6258091,
  302401,
  4211399,
  4210719
}


def load_color_cache() -> Dict:
    """Load cached color data from file if it exists."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                print(f"Loaded {len(cache)} colors from cache")
                return cache
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    return {}


def save_color_cache(color_data: Dict):
    """Save color data to cache file."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(color_data, f, indent=2)
        print(f"Saved {len(color_data)} colors to cache")
    except Exception as e:
        print(f"Error saving cache: {e}")


def fetch_element_color_data(element_id: int) -> Dict:
    """Fetch color data for a given element ID from Rebrickable API."""
    url = f"{API_BASE_URL}{element_id}/"
    headers = {'Authorization': f'key {API_KEY}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract the human-readable color name from LEGO external IDs
        color_info = data['color']
        lego_descrs = color_info.get('external_ids', {}).get('LEGO', {}).get('ext_descrs', [[]])
        human_name = lego_descrs[0][0] if lego_descrs and lego_descrs[0] else color_info['name']
        
        return {
            'element_id': element_id,
            'color_name': human_name,
            'rgb': color_info['rgb'],
            'rgb_tuple': hex_to_rgb(color_info['rgb'])
        }
    except Exception as e:
        print(f"Error fetching element {element_id}: {e}")
        return None


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color code to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def fetch_all_colors() -> List[Dict]:
    """Fetch color data for all available element IDs."""
    # Try to load from cache first
    cache = load_color_cache()
    
    # Convert cache dict to list of color data
    cached_colors = []
    colors_to_fetch = []
    
    for element_id in element_ids:
        element_key = str(element_id)
        if element_key in cache:
            cached_colors.append(cache[element_key])
        else:
            colors_to_fetch.append(element_id)
    
    if cached_colors:
        print(f"Using {len(cached_colors)} colors from cache")
    
    # Fetch any missing colors from API
    if colors_to_fetch:
        print(f"Fetching {len(colors_to_fetch)} new colors from Rebrickable API...")
        for element_id in colors_to_fetch:
            color_data = fetch_element_color_data(element_id)
            if color_data:
                cached_colors.append(color_data)
                cache[str(element_id)] = color_data
                print(f"  Loaded: {color_data['color_name']} (RGB: {color_data['rgb']})")
        
        # Save updated cache
        if colors_to_fetch:
            save_color_cache(cache)
    
    return cached_colors


def load_and_bin_image(image_path: str, bin_size: Tuple[int, int] = (32, 32)) -> np.ndarray:
    """Load an image and bin it to the specified size."""
    print(f"\nLoading image: {image_path}")
    img = Image.open(image_path).convert('RGB')
    print(f"Original size: {img.size}")
    
    # Resize to bin_size using high-quality resampling
    img_binned = img.resize(bin_size, Image.Resampling.LANCZOS)
    print(f"Binned to: {bin_size}")
    
    return np.array(img_binned)


def find_closest_color(pixel_rgb: Tuple[int, int, int], available_colors: List[Dict]) -> Dict:
    """Find the closest available LEGO color to a given RGB value."""
    min_distance = float('inf')
    closest_color = None
    
    for color in available_colors:
        # Calculate Euclidean distance in RGB space
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(pixel_rgb, color['rgb_tuple'])))
        
        if distance < min_distance:
            min_distance = distance
            closest_color = color
    
    return closest_color


def match_image_to_colors(binned_image: np.ndarray, available_colors: List[Dict]) -> Tuple[np.ndarray, Counter]:
    """Match each pixel in the binned image to the nearest available color."""
    print("\nMatching pixels to available LEGO colors...")
    height, width, _ = binned_image.shape
    matched_image = np.zeros_like(binned_image)
    color_counts = Counter()
    
    for y in range(height):
        for x in range(width):
            pixel_rgb = tuple(binned_image[y, x])
            closest = find_closest_color(pixel_rgb, available_colors)
            
            # Set the matched color
            matched_image[y, x] = closest['rgb_tuple']
            color_counts[closest['color_name']] += 1
    
    print(f"Matched {height * width} pixels to {len(color_counts)} unique colors")
    return matched_image, color_counts


def display_results(original_binned: np.ndarray, matched_image: np.ndarray, 
                   color_counts: Counter, output_path: str = 'output.png'):
    """Display the original binned image and matched image side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
    axes[0].imshow(original_binned)
    axes[0].set_title('Original Image (32x32)')
    axes[0].axis('off')
    
    axes[1].imshow(matched_image)
    axes[1].set_title('Matched to LEGO Colors')
    axes[1].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved comparison image to: {output_path}")
    plt.show()


def print_shopping_list(color_counts: Counter):
    """Print the shopping list of colors needed."""
    print("\n" + "="*60)
    print("LEGO BRICK SHOPPING LIST")
    print("="*60)
    print(f"{'Color':<30} {'Quantity':>10}")
    print("-"*60)
    
    total = 0
    for color_name, count in color_counts.most_common():
        print(f"{color_name:<30} {count:>10}")
        total += count
    
    print("-"*60)
    print(f"{'TOTAL':<30} {total:>10}")
    print("="*60)


def main(image_path: str):
    """Main function to process an image and generate shopping list."""
    # Step 1: Fetch all available colors
    available_colors = fetch_all_colors()
    
    if not available_colors:
        print("Error: No colors could be fetched from the API")
        return
    
    print(f"\nLoaded {len(available_colors)} unique colors")
    
    # Step 2: Load and bin the image
    binned_image = load_and_bin_image(image_path, bin_size=(32, 32))
    
    # Step 3: Match pixels to available colors
    matched_image, color_counts = match_image_to_colors(binned_image, available_colors)
    
    # Step 4: Display results
    print_shopping_list(color_counts)
    display_results(binned_image, matched_image, color_counts)


if __name__ == '__main__':
    # Example usage - replace with your image path
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("Usage: python pixel_binning.py <image_path>")
        print("\nExample: python pixel_binning.py my_image.jpg")
        sys.exit(1)
    
    main(image_path)

