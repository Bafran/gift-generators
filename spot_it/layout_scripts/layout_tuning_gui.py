"""
Simple GUI for tuning card layouts by adjusting metadata parameters.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from .layout_card_generator import generate_card_from_metadata


class CardTuningGUI:
    def __init__(self, metadata_path, image_dir, card_number):
        self.metadata_path = metadata_path
        self.image_dir = image_dir
        self.card_number = card_number
        self.window = None
        self.original_metadata = None
        self.current_metadata = None
        self.preview_label = None
        self.image_id_var = None
        self.fields = {}
        
    def load_metadata(self):
        """Load the metadata from file."""
        with open(self.metadata_path, "r") as f:
            self.original_metadata = json.load(f)
        self.current_metadata = json.loads(json.dumps(self.original_metadata))
    
    def save_metadata(self):
        """Save current metadata to file."""
        with open(self.metadata_path, "w") as f:
            json.dump(self.current_metadata, f, indent=2)
    
    def get_current_item(self):
        """Get the currently selected item from metadata."""
        selected_id = self.image_id_var.get()
        for item in self.current_metadata:
            if item["id"] == selected_id:
                return item
        return None
    
    def on_image_selected(self, *args):
        """Update fields when a different image is selected."""
        self.update_fields()
    
    def update_fields(self):
        """Update the input fields based on selected image."""
        item = self.get_current_item()
        if item is None:
            return
        
        self.fields["pos_x"].delete(0, tk.END)
        self.fields["pos_x"].insert(0, f"{item['position'][0]:.2f}")
        
        self.fields["pos_y"].delete(0, tk.END)
        self.fields["pos_y"].insert(0, f"{item['position'][1]:.2f}")
        
        self.fields["angle"].delete(0, tk.END)
        self.fields["angle"].insert(0, f"{item['angle']:.4f}")
        
        self.fields["mass"].delete(0, tk.END)
        self.fields["mass"].insert(0, f"{item['mass']:.4f}")
    
    def apply_changes(self):
        """Apply field changes to the current item."""
        item = self.get_current_item()
        if item is None:
            return False
        
        try:
            item["position"][0] = float(self.fields["pos_x"].get())
            item["position"][1] = float(self.fields["pos_y"].get())
            item["angle"] = float(self.fields["angle"].get())
            item["mass"] = float(self.fields["mass"].get())
            return True
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")
            return False
    
    def regenerate_card(self):
        """Regenerate the card preview with current metadata."""
        if not self.apply_changes():
            return
        
        try:
            self.save_metadata()
            # Generate a temporary preview
            generate_card_from_metadata(self.metadata_path, self.image_dir, "/tmp/card_preview.png")
            self.update_preview()
            messagebox.showinfo("Success", "Card regenerated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to regenerate card: {str(e)}")
    
    def update_preview(self):
        """Update the preview image in the GUI."""
        try:
            img = Image.open("/tmp/card_preview.png")
            # Scale for preview (256x256)
            img.thumbnail((256, 256), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preview: {str(e)}")
    
    def reset_to_original(self):
        """Reset all changes to original metadata."""
        if messagebox.askyesno("Reset", "Reset all changes to original?"):
            self.current_metadata = json.loads(json.dumps(self.original_metadata))
            self.update_fields()
    
    def run(self):
        """Launch the GUI window."""
        self.load_metadata()
        
        self.window = tk.Tk()
        self.window.title(f"Tune Card {self.card_number:02d}")
        self.window.geometry("600x700")
        
        # Top frame: Image selector
        selector_frame = ttk.Frame(self.window)
        selector_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(selector_frame, text="Select Image:").pack(side=tk.LEFT)
        
        image_ids = [item["id"] for item in self.current_metadata]
        self.image_id_var = tk.StringVar(value=image_ids[0])
        self.image_id_var.trace("w", self.on_image_selected)
        
        dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.image_id_var,
            values=image_ids,
            state="readonly",
            width=30
        )
        dropdown.pack(side=tk.LEFT, padx=5)
        
        # Main frame: Fields and preview
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side: Input fields
        fields_frame = ttk.LabelFrame(main_frame, text="Parameters", padding=10)
        fields_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        field_names = [
            ("Position X:", "pos_x"),
            ("Position Y:", "pos_y"),
            ("Angle (radians):", "angle"),
            ("Mass:", "mass"),
        ]
        
        for label_text, field_key in field_names:
            frame = ttk.Frame(fields_frame)
            frame.pack(fill=tk.X, pady=5)
            ttk.Label(frame, text=label_text, width=15).pack(side=tk.LEFT)
            entry = ttk.Entry(frame, width=20)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.fields[field_key] = entry
        
        # Right side: Preview
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=10)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.preview_label = tk.Label(preview_frame, bg="white", width=256, height=256)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Initialize fields and preview
        self.update_fields()
        self.regenerate_card()
        
        # Bottom frame: Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Regenerate Card",
            command=self.regenerate_card
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Reset to Original",
            command=self.reset_to_original
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Done",
            command=self.window.quit
        ).pack(side=tk.RIGHT, padx=5)
        
        self.window.mainloop()


def open_tuning_gui(metadata_path, image_dir, card_number):
    """Open the card tuning GUI."""
    gui = CardTuningGUI(metadata_path, image_dir, card_number)
    gui.run()
