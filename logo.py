from PIL import Image, ImageDraw, ImageFont

# Very large image canvas
width, height = 1600, 400
bg_color = (0, 0, 0, 0)  # Fully transparent background

# Create transparent image
image = Image.new("RGBA", (width, height), bg_color)
draw = ImageDraw.Draw(image)

# Load big font
try:
    font = ImageFont.truetype("arial.ttf", 300)  # Huge font size
except:
    font = ImageFont.load_default()

# Text and color
text = "NKTECH"
text_color = (255, 255, 255, 255)  # Pure white

# Center the text
text_width, text_height = draw.textsize(text, font=font)
x = (width - text_width) // 2
y = (height - text_height) // 2

# Draw the text
draw.text((x, y), text, font=font, fill=text_color)

# Save as watermark PNG
image.save("nktech.png")
print("✅ Huge watermark 'nktech.png' created.")
