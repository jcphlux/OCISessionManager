import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont
import threading
import time


# Function to create an icon image with a number badge
def create_icon_with_badge(number):
    # Create an image with transparent background
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a circle (or any shape) for the icon's background
    draw.ellipse((0, 0, width, height), fill=(0, 128, 255))

    # Draw a small circle in the bottom-left corner for the badge
    badge_radius = 20
    badge_x, badge_y = width - badge_radius, height - badge_radius
    draw.ellipse(
        (
            badge_x - badge_radius,
            badge_y - badge_radius,
            badge_x + badge_radius,
            badge_y + badge_radius,
        ),
        fill=(255, 0, 0),
    )  # Red badge

    # Draw the number on the badge
    try:
        # Load a default font (if system has it)
        font = ImageFont.truetype("arialbd.ttf", 46)  # Use Arial Bold for better visibility
    except IOError:
        # Fallback to a default font if arial.ttf is not available
        font = ImageFont.load_default()

    # Position the text in the center of the badge
    text = str(number)
    pos= draw.textlength(text, font=font)

    text_x = badge_x - pos // 2
    text_y = badge_y - 10 - pos // 2

    draw.text((text_x, text_y), text, font=font, fill="white")

    return image


# Function to update the icon periodically (simulating some dynamic change)
def update_icon(icon):
    number = 0
    while True:
        # Create a new icon with the updated number
        icon.icon = create_icon_with_badge(number)
        number += 1  # Update number (this could be any dynamic value)
        time.sleep(5)  # Update every second


# Function to stop the icon
def on_quit(icon, item):
    icon.stop()


# Create a pystray icon and set up the menu
icon = pystray.Icon(
    "test_icon", create_icon_with_badge(0), menu=(item("Quit", on_quit),)
)

# Run the update in a separate thread
thread = threading.Thread(target=update_icon, args=(icon,))
thread.daemon = True
thread.start()

# Run the icon in the system tray
icon.run()
