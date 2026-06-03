"""
Create Balanced PromptOps Banner - Eye-catching but Clean
"""
from PIL import Image, ImageDraw, ImageFont
import math

# Banner dimensions
WIDTH = 1200
HEIGHT = 630

# Balanced Color Palette
BG_START = (30, 41, 59)  # Slate 800
BG_END = (88, 28, 135)   # Purple 900
ACCENT_BLUE = (96, 165, 250)  # Blue 400
ACCENT_PURPLE = (167, 139, 250)  # Purple 400
ACCENT_CYAN = (34, 211, 238)  # Cyan 400
ACCENT_PINK = (244, 114, 182)  # Pink 400
ACCENT_ORANGE = (251, 146, 60)  # Orange 400
GOLD = (250, 204, 21)  # Yellow 400
WHITE = (255, 255, 255)
LIGHT_BLUE = (224, 242, 254)
GREEN = (52, 211, 153)  # Emerald 400

def create_smooth_gradient(width, height):
    """Create a smooth diagonal gradient"""
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    for y in range(height):
        # Diagonal gradient
        for x in range(width):
            progress = (x + y) / (width + height)

            # Smooth transition from slate to purple
            r = int(BG_START[0] + (BG_END[0] - BG_START[0]) * progress)
            g = int(BG_START[1] + (BG_END[1] - BG_START[1]) * progress)
            b = int(BG_START[2] + (BG_END[2] - BG_START[2]) * progress)

            draw.point((x, y), fill=(r, g, b))

    return image

def add_simple_grid(image):
    """Add a subtle grid pattern"""
    draw = ImageDraw.Draw(image, 'RGBA')
    grid_size = 50

    # Vertical and horizontal lines
    for x in range(0, WIDTH, grid_size):
        draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 8), width=1)

    for y in range(0, HEIGHT, grid_size):
        draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 8), width=1)

    return image

def add_corner_accents(image):
    """Add subtle corner accents for visual interest"""
    draw = ImageDraw.Draw(image, 'RGBA')

    # Top right corner accent lines
    for i in range(3):
        y = 60 + i * 30
        x_start = WIDTH - 200 + i * 40
        draw.line([(x_start, y), (WIDTH, y)], fill=(255, 255, 255, 15), width=2)

    # Bottom left corner accent lines
    for i in range(3):
        y = HEIGHT - 80 + i * 20
        x_end = 180 - i * 40
        draw.line([(0, y), (x_end, y)], fill=(255, 255, 255, 15), width=2)

    return image

def create_logo(draw, x, y, size):
    """Create attractive logo with gradient P"""
    # Logo background with subtle shadow
    shadow_offset = 4
    draw.rounded_rectangle([x+shadow_offset, y+shadow_offset,
                           x+size+shadow_offset, y+size+shadow_offset],
                          radius=16, fill=(0, 0, 0, 60))

    # Gradient background for logo box (light blue to white)
    for i in range(size):
        progress = i / size
        r = int(240 + (255 - 240) * progress)
        g = int(245 + (255 - 245) * progress)
        b = int(255)
        draw.rectangle([x, y+i, x+size, y+i+1], fill=(r, g, b))

    # Add rounded corners back
    draw.rounded_rectangle([x, y, x+size, y+size],
                          radius=16, outline=None, width=0)

    # Inner border glow
    draw.rounded_rectangle([x+2, y+2, x+size-2, y+size-2],
                          radius=14, outline=(*ACCENT_CYAN, 40), width=2)

    # Accent circle with gradient effect
    circle_x = x + size - 10
    circle_y = y - 8
    circle_size = 26

    # Circle glow
    for r in range(circle_size + 8, circle_size, -1):
        alpha = int(60 * ((r - circle_size) / 8))
        draw.ellipse([circle_x-(r-circle_size), circle_y-(r-circle_size),
                     circle_x+r, circle_y+r],
                    fill=(*ACCENT_PURPLE, alpha))

    # Main circle
    draw.ellipse([circle_x, circle_y, circle_x+circle_size, circle_y+circle_size],
                fill=ACCENT_PURPLE)

    # Highlight on circle
    highlight_size = 8
    draw.ellipse([circle_x+6, circle_y+4, circle_x+6+highlight_size, circle_y+4+highlight_size],
                fill=(255, 255, 255, 100))

    # Draw "P" with gradient effect
    try:
        p_font = ImageFont.truetype("arialbd.ttf", 58)
    except:
        p_font = ImageFont.load_default()

    p_x = x + 20
    p_y = y + 14

    # P shadow
    draw.text((p_x + 3, p_y + 3), "P", fill=(ACCENT_BLUE[0]//3, ACCENT_BLUE[1]//3, ACCENT_BLUE[2]//3, 60), font=p_font)

    # Main P with gradient (simulate with multiple colors)
    # Top part - lighter blue
    draw.text((p_x, p_y), "P", fill=ACCENT_CYAN, font=p_font)

    # Create highlight effect on P
    try:
        p_font_small = ImageFont.truetype("arialbd.ttf", 56)
    except:
        p_font_small = p_font
    draw.text((p_x, p_y), "P", fill=ACCENT_BLUE, font=p_font)

def create_badge(draw, x, y, text, icon, color, font):
    """Create a clean feature badge"""
    # Calculate size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    badge_width = text_width + 60
    badge_height = 46

    # Shadow
    draw.rounded_rectangle([x+2, y+2, x+badge_width+2, y+badge_height+2],
                          radius=23, fill=(0, 0, 0, 50))

    # Badge background
    draw.rounded_rectangle([x, y, x+badge_width, y+badge_height],
                          radius=23, fill=(*color, 30))

    # Border
    draw.rounded_rectangle([x, y, x+badge_width, y+badge_height],
                          radius=23, outline=color, width=2)

    # Icon circle
    icon_size = 26
    icon_x = x + 12
    icon_y = y + 10
    draw.ellipse([icon_x, icon_y, icon_x+icon_size, icon_y+icon_size],
                fill=color)

    # Icon
    try:
        icon_font = ImageFont.truetype("arialbd.ttf", 14)
    except:
        icon_font = font

    draw.text((icon_x + 7, icon_y + 5), icon, fill=WHITE, font=icon_font)

    # Text
    draw.text((x + 48, y + 13), text, fill=WHITE, font=font)

    return badge_width

def main():
    """Create balanced banner"""
    print("Creating balanced PromptOps banner...")

    # Create gradient background
    image = create_smooth_gradient(WIDTH, HEIGHT)

    # Add subtle grid
    image = add_simple_grid(image)

    # Add corner accents
    image = add_corner_accents(image)

    # Drawing context
    draw = ImageDraw.Draw(image, 'RGBA')

    # Load fonts
    try:
        logo_font = ImageFont.truetype("arialbd.ttf", 50)
        title_font = ImageFont.truetype("arialbd.ttf", 36)
        subtitle_font = ImageFont.truetype("arialbd.ttf", 20)
        badge_font = ImageFont.truetype("arialbd.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 15)
    except:
        print("Warning: Arial font not found, using default")
        logo_font = ImageFont.load_default()
        title_font = logo_font
        subtitle_font = logo_font
        badge_font = logo_font
        small_font = logo_font

    # Draw logo
    create_logo(draw, 70, 55, 85)

    # Draw "PromptOps" text with subtle shadow
    text_x = 175
    text_y = 70
    draw.text((text_x + 2, text_y + 2), "PromptOps", fill=(0, 0, 0, 100), font=logo_font)
    draw.text((text_x, text_y), "PromptOps", fill=WHITE, font=logo_font)

    # Main tagline
    tagline_y = 175
    taglines = [
        "Empowering DevOps, Security, Infrastructure, Monitoring,",
        "Cloud Engineering, and Site Reliability Engineering",
        "in a single AI-powered cloud operations control tower."
    ]

    for line in taglines:
        # Shadow
        draw.text((72, tagline_y + 2), line, fill=(0, 0, 0, 80), font=title_font)
        # Text
        draw.text((70, tagline_y), line, fill=WHITE, font=title_font)
        tagline_y += 44

    # AI prediction subtitle with highlight
    ai_y = tagline_y + 12
    ai_text = "AI predicts and prevents failures before they happen"

    # Subtle background highlight
    ai_bbox = draw.textbbox((70, ai_y), ai_text, font=subtitle_font)
    highlight_padding = 8
    draw.rounded_rectangle([ai_bbox[0]-highlight_padding, ai_bbox[1]-highlight_padding,
                           ai_bbox[2]+highlight_padding, ai_bbox[3]+highlight_padding],
                          radius=8, fill=(6, 182, 212, 40))

    draw.text((70, ai_y), ai_text, fill=ACCENT_CYAN, font=subtitle_font)

    # Feature badges - Row 1: Core Disciplines
    badges_y = 380
    badges_x = 70

    row1_badges = [
        ("DevOps", "⚙", ACCENT_BLUE),
        ("Security", "🛡", ACCENT_PURPLE),
        ("Infrastructure", "🏗", ACCENT_CYAN),
        ("Monitoring", "📊", ACCENT_PINK),
        ("Cloud", "☁", ACCENT_BLUE),
        ("SRE", "✓", GREEN),
    ]

    for text, icon, color in row1_badges:
        width = create_badge(draw, badges_x, badges_y, text, icon, color, badge_font)
        badges_x += width + 12

    # Feature badges - Row 2: Key Features
    badges_y = 442
    badges_x = 70

    row2_badges = [
        ("Auto-Scaling", "↕", ACCENT_CYAN),
        ("Risk-Free", "✓", GREEN),
        ("Auto-Remediation", "🔧", ACCENT_ORANGE),
        ("Cost-Optimization", "$", GOLD),
        ("Multi-Cloud", "☁", ACCENT_PURPLE),
        ("Real-Time", "⚡", ACCENT_PINK),
    ]

    for text, icon, color in row2_badges:
        width = create_badge(draw, badges_x, badges_y, text, icon, color, badge_font)
        badges_x += width + 12

    # AI-Powered badge
    ai_badge_x = 70
    ai_badge_y = 525
    ai_badge_w = 270
    ai_badge_h = 50

    # Shadow
    draw.rounded_rectangle([ai_badge_x+3, ai_badge_y+3,
                           ai_badge_x+ai_badge_w+3, ai_badge_y+ai_badge_h+3],
                          radius=25, fill=(0, 0, 0, 70))

    # Badge
    draw.rounded_rectangle([ai_badge_x, ai_badge_y,
                           ai_badge_x+ai_badge_w, ai_badge_y+ai_badge_h],
                          radius=25, fill=GOLD)

    # Text
    try:
        ai_font = ImageFont.truetype("arialbd.ttf", 19)
    except:
        ai_font = badge_font

    draw.text((ai_badge_x + 16, ai_badge_y + 14), "⚡ AI-Powered Automation",
             fill=(30, 41, 59), font=ai_font)

    # Production ready status
    status_x = 970
    status_y = 540

    # Status dot with small glow
    for r in range(10, 6, -1):
        alpha = int(80 * ((r - 6) / 4))
        draw.ellipse([status_x-r, status_y-r, status_x+r+12, status_y+r+12],
                    fill=(*GREEN, alpha))

    draw.ellipse([status_x, status_y, status_x+12, status_y+12], fill=GREEN)

    # Status text
    draw.text((status_x + 20, status_y - 1), "Production Ready",
             fill=WHITE, font=small_font)

    # Save
    output_path = "promptops-balanced-banner.png"
    image.save(output_path, quality=95, optimize=True)

    print(f"Balanced banner saved to: {output_path}")
    print(f"Dimensions: {WIDTH}x{HEIGHT}px")
    print(f"Full path: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    import os
    main()
