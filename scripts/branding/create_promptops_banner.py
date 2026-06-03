"""
Create PromptOps banner image using PIL/Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import math

# Banner dimensions (standard social media size)
WIDTH = 1200
HEIGHT = 630

# Colors
GRADIENT_START = (102, 126, 234)  # #667eea
GRADIENT_END = (240, 147, 251)    # #f093fb
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GREEN = (74, 222, 128)
PURPLE = (118, 75, 162)

def create_gradient_background(width, height):
    """Create a diagonal gradient background"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    for y in range(height):
        for x in range(width):
            # Diagonal gradient calculation
            progress = (x + y) / (width + height)

            r = int(GRADIENT_START[0] + (GRADIENT_END[0] - GRADIENT_START[0]) * progress)
            g = int(GRADIENT_START[1] + (GRADIENT_END[1] - GRADIENT_START[1]) * progress)
            b = int(GRADIENT_START[2] + (GRADIENT_END[2] - GRADIENT_START[2]) * progress)

            draw.point((x, y), fill=(r, g, b))

    return image

def add_grid_overlay(image):
    """Add a grid pattern overlay"""
    draw = ImageDraw.Draw(image, 'RGBA')
    grid_size = 50

    # Draw vertical lines
    for x in range(0, WIDTH, grid_size):
        draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 13), width=1)

    # Draw horizontal lines
    for y in range(0, HEIGHT, grid_size):
        draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 13), width=1)

    return image

def add_particles(image):
    """Add floating particles"""
    draw = ImageDraw.Draw(image, 'RGBA')
    particles = [
        (120, 126), (360, 252), (600, 378),
        (840, 189), (1020, 441), (240, 504)
    ]

    for x, y in particles:
        draw.ellipse([x-3, y-3, x+3, y+3], fill=(255, 255, 255, 150))

    return image

def create_logo(draw, x, y, size):
    """Create the PromptOps logo"""
    # Main square background
    logo_rect = [x, y, x + size, y + size]
    draw.rounded_rectangle(logo_rect, radius=16, fill=(240, 240, 255))

    # Small circle accent
    circle_x = x + size - 15
    circle_y = y - 5
    draw.ellipse([circle_x, circle_y, circle_x + 30, circle_y + 30], fill=PURPLE)

    # Draw "P" letter
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()

    # Center the P
    bbox = draw.textbbox((0, 0), "P", font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = x + (size - text_width) // 2
    text_y = y + (size - text_height) // 2 - 5

    draw.text((text_x, text_y), "P", fill=GRADIENT_START, font=font)

def main():
    """Create the banner image"""
    print("Creating PromptOps banner...")

    # Create gradient background
    image = create_gradient_background(WIDTH, HEIGHT)

    # Add grid overlay
    image = add_grid_overlay(image)

    # Add particles
    image = add_particles(image)

    # Create drawing context
    draw = ImageDraw.Draw(image, 'RGBA')

    # Draw logo
    create_logo(draw, 80, 60, 80)

    # Load fonts
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 48)
        logo_font = ImageFont.truetype("arialbd.ttf", 44)
        tagline_font = ImageFont.truetype("arialbd.ttf", 32)
        feature_font = ImageFont.truetype("arialbd.ttf", 16)
        badge_font = ImageFont.truetype("arialbd.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        print("Warning: Arial font not found, using default font")
        title_font = ImageFont.load_default()
        logo_font = title_font
        tagline_font = title_font
        feature_font = title_font
        badge_font = title_font
        small_font = title_font

    # Draw "PromptOps" text
    draw.text((180, 75), "PromptOps", fill=WHITE, font=logo_font)

    # Draw main tagline (multi-line)
    tagline_lines = [
        "Empowering DevOps, Security, Infrastructure, Monitoring,",
        "Cloud Engineering, and Site Reliability Engineering",
        "in a single AI-powered cloud operations control tower."
    ]

    y_offset = 180
    for line in tagline_lines:
        draw.text((80, y_offset), line, fill=WHITE, font=tagline_font)
        y_offset += 42

    # Add predictive AI subtitle
    y_offset += 10
    try:
        subtitle_font = ImageFont.truetype("arial.ttf", 20)
    except:
        subtitle_font = small_font
    draw.text((80, y_offset), "AI predicts and prevents failures before they happen",
              fill=(255, 255, 255, 220), font=subtitle_font)

    # Draw feature badges
    features = ["DevOps", "Security", "Infrastructure", "Monitoring", "Cloud", "SRE"]
    x_offset = 80
    y_badge = 410

    for feature in features:
        # Badge background
        bbox = draw.textbbox((0, 0), feature, font=feature_font)
        badge_width = bbox[2] - bbox[0] + 40
        badge_height = 40

        # Draw rounded rectangle for badge
        badge_rect = [x_offset, y_badge, x_offset + badge_width, y_badge + badge_height]
        draw.rounded_rectangle(badge_rect, radius=20, fill=(255, 255, 255, 38))

        # Draw text
        text_x = x_offset + 20
        text_y = y_badge + 10
        draw.text((text_x, text_y), feature, fill=WHITE, font=feature_font)

        x_offset += badge_width + 20

    # Draw AI-Powered badge
    ai_badge_text = "⚡ AI-Powered Automation"
    ai_badge_rect = [80, 550, 320, 590]
    draw.rounded_rectangle(ai_badge_rect, radius=20, fill=GOLD)
    draw.text((100, 558), ai_badge_text, fill=(26, 26, 46), font=badge_font)

    # Draw production ready status
    status_x = 950
    status_y = 562

    # Green status dot
    draw.ellipse([status_x, status_y, status_x + 10, status_y + 10], fill=GREEN)

    # Status text
    draw.text((status_x + 18, status_y - 3), "Production Ready", fill=WHITE, font=small_font)

    # Save image
    output_path = "promptops-banner.png"
    image.save(output_path, quality=95)
    print(f"Banner saved to: {output_path}")
    print(f"Dimensions: {WIDTH}x{HEIGHT}px")
    print(f"Full path: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    import os
    main()
