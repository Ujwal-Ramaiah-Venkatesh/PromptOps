"""
Create Premium PromptOps Banner with Enhanced Visual Effects
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

# Banner dimensions
WIDTH = 1200
HEIGHT = 630

# Premium Color Palette
DARK_BG = (15, 23, 42)  # Dark slate
ACCENT_BLUE = (59, 130, 246)  # Bright blue
ACCENT_PURPLE = (139, 92, 246)  # Vibrant purple
ACCENT_CYAN = (6, 182, 212)  # Cyan
ACCENT_PINK = (236, 72, 153)  # Hot pink
GOLD = (251, 191, 36)  # Gold/amber
WHITE = (255, 255, 255)
LIGHT_GRAY = (148, 163, 184)
GREEN = (16, 185, 129)  # Emerald green

def create_premium_gradient(width, height):
    """Create a premium dark gradient with vibrant accents"""
    image = Image.new('RGB', (width, height), DARK_BG)
    draw = ImageDraw.Draw(image, 'RGBA')

    # Create radial gradient spots
    # Top left glow
    for i in range(300, 0, -5):
        alpha = int(15 * (i / 300))
        draw.ellipse([-100, -100, i*2, i*2],
                    fill=(*ACCENT_PURPLE, alpha))

    # Top right glow
    for i in range(250, 0, -5):
        alpha = int(12 * (i / 250))
        draw.ellipse([width-300, -100, width+100, i*2],
                    fill=(*ACCENT_CYAN, alpha))

    # Bottom right glow
    for i in range(300, 0, -5):
        alpha = int(10 * (i / 300))
        draw.ellipse([width-200, height-200, width+100, height+100],
                    fill=(*ACCENT_PINK, alpha))

    return image

def add_grid_lines(image):
    """Add premium grid lines"""
    draw = ImageDraw.Draw(image, 'RGBA')
    grid_size = 40

    # Vertical lines
    for x in range(0, WIDTH, grid_size):
        opacity = 8 if x % (grid_size * 2) == 0 else 4
        draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, opacity), width=1)

    # Horizontal lines
    for y in range(0, HEIGHT, grid_size):
        opacity = 8 if y % (grid_size * 2) == 0 else 4
        draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, opacity), width=1)

    return image

def add_floating_elements(image):
    """Add modern floating elements"""
    draw = ImageDraw.Draw(image, 'RGBA')

    # Floating particles with glow
    particles = [
        (200, 150, ACCENT_CYAN),
        (950, 200, ACCENT_PURPLE),
        (400, 450, ACCENT_PINK),
        (1050, 500, ACCENT_BLUE),
        (150, 550, GOLD),
        (700, 180, ACCENT_CYAN),
    ]

    for x, y, color in particles:
        # Outer glow
        for r in range(15, 0, -2):
            alpha = int(30 * (r / 15))
            draw.ellipse([x-r, y-r, x+r, y+r], fill=(*color, alpha))
        # Core
        draw.ellipse([x-4, y-4, x+4, y+4], fill=(*color, 200))

    # Add some geometric shapes
    # Hexagons in corners
    hex_coords = [
        (100, 100), (1100, 100), (100, 530), (1100, 530)
    ]

    for hx, hy in hex_coords:
        # Draw subtle hexagon
        size = 30
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            px = hx + size * math.cos(angle)
            py = hy + size * math.sin(angle)
            points.append((px, py))
        draw.polygon(points, outline=(*ACCENT_PURPLE, 30), width=2)

    return image

def create_premium_logo(draw, x, y, size):
    """Create a premium logo with effects"""
    # Outer glow
    for i in range(20, 0, -2):
        alpha = int(40 * (i / 20))
        draw.rounded_rectangle([x-i, y-i, x+size+i, y+size+i],
                             radius=20, fill=(*ACCENT_BLUE, alpha))

    # Main logo background with gradient effect
    draw.rounded_rectangle([x, y, x+size, y+size],
                          radius=18, fill=(255, 255, 255))

    # Inner gradient overlay
    draw.rounded_rectangle([x+2, y+2, x+size-2, y+size-2],
                          radius=16, fill=(240, 245, 255))

    # Circle accent with glow
    circle_x = x + size - 12
    circle_y = y - 8
    circle_size = 28

    # Circle glow
    for r in range(circle_size, 0, -2):
        alpha = int(80 * (r / circle_size))
        draw.ellipse([circle_x-r//2, circle_y-r//2,
                     circle_x+r//2+circle_size, circle_y+r//2+circle_size],
                    fill=(*ACCENT_PURPLE, alpha))

    draw.ellipse([circle_x, circle_y, circle_x+circle_size, circle_y+circle_size],
                fill=ACCENT_PURPLE)

def draw_text_with_shadow(draw, pos, text, font, fill_color, shadow_offset=3):
    """Draw text with shadow for depth"""
    x, y = pos
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text,
             fill=(0, 0, 0, 100), font=font)
    # Main text
    draw.text((x, y), text, fill=fill_color, font=font)

def create_feature_badge(draw, x, y, text, icon, color, font):
    """Create a premium feature badge"""
    # Calculate dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    badge_width = text_width + 70
    badge_height = 50

    # Glow effect
    for i in range(10, 0, -1):
        alpha = int(20 * (i / 10))
        draw.rounded_rectangle([x-i, y-i, x+badge_width+i, y+badge_height+i],
                              radius=25, fill=(*color, alpha))

    # Badge background
    draw.rounded_rectangle([x, y, x+badge_width, y+badge_height],
                          radius=25, fill=(*color, 25))

    # Badge border
    draw.rounded_rectangle([x, y, x+badge_width, y+badge_height],
                          radius=25, outline=(*color, 80), width=2)

    # Icon circle
    icon_x = x + 15
    icon_y = y + 15
    draw.ellipse([icon_x, icon_y, icon_x+20, icon_y+20],
                fill=(*color, 150))

    # Icon text
    icon_font_size = 14
    try:
        icon_font = ImageFont.truetype("arial.ttf", icon_font_size)
    except:
        icon_font = font

    draw.text((icon_x + 5, icon_y + 2), icon, fill=WHITE, font=icon_font)

    # Badge text
    draw.text((x + 45, y + 14), text, fill=WHITE, font=font)

    return badge_width

def main():
    """Create premium banner"""
    print("Creating premium PromptOps banner...")

    # Create base with premium gradient
    image = create_premium_gradient(WIDTH, HEIGHT)

    # Add grid
    image = add_grid_lines(image)

    # Add floating elements
    image = add_floating_elements(image)

    # Create drawing context
    draw = ImageDraw.Draw(image, 'RGBA')

    # Load fonts
    try:
        logo_font = ImageFont.truetype("arialbd.ttf", 52)
        title_font = ImageFont.truetype("arialbd.ttf", 38)
        subtitle_font = ImageFont.truetype("arialbd.ttf", 22)
        small_font = ImageFont.truetype("arial.ttf", 18)
        badge_font = ImageFont.truetype("arialbd.ttf", 16)
        tiny_font = ImageFont.truetype("arial.ttf", 15)
    except:
        print("Warning: Arial font not found, using default")
        logo_font = ImageFont.load_default()
        title_font = logo_font
        subtitle_font = logo_font
        small_font = logo_font
        badge_font = logo_font
        tiny_font = logo_font

    # Draw premium logo
    create_premium_logo(draw, 70, 50, 90)

    # Draw "P" in logo
    try:
        p_font = ImageFont.truetype("arialbd.ttf", 56)
    except:
        p_font = logo_font

    draw.text((100, 62), "P", fill=ACCENT_BLUE, font=p_font)

    # Draw "PromptOps" with glow
    logo_text_x = 180
    logo_text_y = 65

    # Glow
    for offset in range(8, 0, -1):
        alpha = int(60 * (offset / 8))
        draw.text((logo_text_x, logo_text_y), "PromptOps",
                 fill=(*ACCENT_CYAN, alpha), font=logo_font)

    # Main text
    draw.text((logo_text_x, logo_text_y), "PromptOps", fill=WHITE, font=logo_font)

    # Main tagline with better spacing
    tagline_y = 170
    tagline_lines = [
        "Empowering DevOps, Security, Infrastructure, Monitoring,",
        "Cloud Engineering, and Site Reliability Engineering",
        "in a single AI-powered cloud operations control tower."
    ]

    for line in tagline_lines:
        # Subtle shadow
        draw.text((72, tagline_y + 2), line, fill=(0, 0, 0, 80), font=title_font)
        # Main text
        draw.text((70, tagline_y), line, fill=WHITE, font=title_font)
        tagline_y += 45

    # AI prediction tagline with gradient effect
    ai_text = "AI predicts and prevents failures before they happen"
    ai_y = tagline_y + 15

    # Gradient text effect (cyan to purple)
    draw.text((70, ai_y), ai_text, fill=ACCENT_CYAN, font=subtitle_font)

    # Feature badges with icons
    badges_y = 400
    badges_x = 70

    badges_data = [
        ("DevOps", "⚙", ACCENT_BLUE),
        ("Security", "🛡", ACCENT_PURPLE),
        ("Infrastructure", "🏗", ACCENT_CYAN),
        ("Monitoring", "📊", ACCENT_PINK),
        ("Cloud", "☁", ACCENT_BLUE),
        ("SRE", "✓", GREEN),
    ]

    for text, icon, color in badges_data:
        width = create_feature_badge(draw, badges_x, badges_y, text, icon, color, badge_font)
        badges_x += width + 15

        if badges_x > 900:
            badges_x = 70
            badges_y += 60

    # Premium AI badge with strong glow
    ai_badge_x = 70
    ai_badge_y = 540
    ai_badge_w = 280
    ai_badge_h = 55

    # Strong glow
    for i in range(20, 0, -1):
        alpha = int(50 * (i / 20))
        draw.rounded_rectangle([ai_badge_x-i, ai_badge_y-i,
                               ai_badge_x+ai_badge_w+i, ai_badge_y+ai_badge_h+i],
                              radius=28, fill=(*GOLD, alpha))

    # Badge
    draw.rounded_rectangle([ai_badge_x, ai_badge_y,
                           ai_badge_x+ai_badge_w, ai_badge_y+ai_badge_h],
                          radius=28, fill=GOLD)

    # Badge text with shadow
    try:
        ai_badge_font = ImageFont.truetype("arialbd.ttf", 20)
    except:
        ai_badge_font = badge_font

    draw.text((ai_badge_x + 18, ai_badge_y + 16), "⚡ AI-Powered Automation",
             fill=DARK_BG, font=ai_badge_font)

    # Production ready status with pulse effect
    status_x = 980
    status_y = 555

    # Pulse glow
    for r in range(15, 0, -2):
        alpha = int(100 * (r / 15))
        draw.ellipse([status_x-r, status_y-r, status_x+12+r, status_y+12+r],
                    fill=(*GREEN, alpha))

    # Status dot
    draw.ellipse([status_x, status_y, status_x+12, status_y+12], fill=GREEN)

    # Status text
    draw.text((status_x + 22, status_y - 2), "Production Ready",
             fill=WHITE, font=tiny_font)

    # Apply subtle overall sharpness
    # image = image.filter(ImageFilter.SHARPEN)

    # Save
    output_path = "promptops-premium-banner.png"
    image.save(output_path, quality=98, optimize=True)

    print(f"Premium banner saved to: {output_path}")
    print(f"Dimensions: {WIDTH}x{HEIGHT}px")
    print(f"Full path: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    import os
    main()
