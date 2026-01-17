
import matplotlib
matplotlib.use("Agg")  # Force headless

import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
sys.path.append(os.getcwd())

from core import pipeline, io_utils

def generate_screenshot():
    # 1. Run Pipeline
    image_path = "data/250525 154446 STEM 5.1Mx HAADF c.dm3"  # Use verified existing file
    print(f"Running pipeline on {image_path}...")
    
    if not Path(image_path).exists():
        print(f"Error: {image_path} not found.")
        return

    # Run with default params
    result = pipeline.run_pipeline(
        image_path,
        gaussian_sigma=1.0,
        refine_sigma=1.0,
        separation=None,  # Auto
        threshold=None,
        nm_per_pixel=None,
    )
    
    out_dir = result.output_dir
    print(f"Outputs generated in {out_dir}")
    
    # 2. Create Collage mimicking the GUI Overview tab
    files = [
        ("peaks_overlay.png", "A/B Sublattice Detection"),
        ("displacement_heatmap.png", "Displacement Heatmap"),
        ("displacement_arrows_angle.png", "Angle-Coded Vectors"),
        ("strain_combined.png", "Strain Analysis"),
    ]
    
    images = []
    titles = []
    
    target_size = (600, 600)  # Resize all to this roughly
    
    for fname, title in files:
        p = out_dir / fname
        if p.exists():
            img = Image.open(p)
            # Resize preserving aspect ratio to fit in target_size
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            images.append(img)
            titles.append(title)
        else:
            print(f"Warning: {fname} not found in {out_dir}")
            # Placeholder
            img = Image.new('RGB', target_size, color='gray')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), f"Missing: {fname}", fill="white")
            images.append(img)
            titles.append(title)

    # layout: 2x2
    margin = 40
    text_h = 40
    
    # Calculate cell size
    cell_w = max(im.width for im in images) + 2 * margin
    cell_h = max(im.height for im in images) + 2 * margin + text_h
    
    canvas_w = cell_w * 2
    canvas_h = cell_h * 2
    
    collage = Image.new('RGB', (canvas_w, canvas_h), color='#2b2b2b') # Dark theme bg
    draw = ImageDraw.Draw(collage)
    
    # Try to load a font
    try:
        font_path = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
        if not Path(font_path).exists():
             font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 24)
    except:
        font = ImageFont.load_default()

    positions = [(0, 0), (1, 0), (0, 1), (1, 1)]
    
    for idx, (img, title) in enumerate(zip(images, titles)):
        r, c = positions[idx]
        x = c * cell_w + margin
        y = r * cell_h + margin + text_h
        
        # Center image in cell
        img_x = x + (cell_w - 2 * margin - img.width) // 2
        img_y = y  # Top align
        
        collage.paste(img, (img_x, img_y))
        
        # Draw Title
        try:
            title_w = draw.textlength(title, font=font)
        except:
            title_w = draw.textsize(title, font=font)[0]
            
        text_x = c * cell_w + (cell_w - title_w) // 2
        text_y = r * cell_h + margin
        draw.text((text_x, text_y), title, fill="white", font=font)

    # Save
    out_path = Path("assets/screenshot.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    collage.save(out_path)
    print(f"Screenshot saved to {out_path}")

if __name__ == "__main__":
    generate_screenshot()
