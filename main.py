from PIL import Image, ImageDraw

def create_white_lines_pattern(image_width, image_height, line_spacing, line_width=20):
    # Create a new image with the same dimensions as the original
    pattern_image = Image.new('RGB', (image_width, image_height), color='black')

    # Initialize the drawing context with the pattern image
    draw = ImageDraw.Draw(pattern_image)

    # Draw white horizontal lines across the pattern image with the specified spacing
    y = 0
    while y < image_height:
        draw.line((0, y, image_width, y), fill='white', width=line_width)
        y += line_spacing + line_width

    return pattern_image

def overlay_images(base_image, overlay_pattern):
    # Ensure both images have the same size
    overlay_pattern = overlay_pattern.resize(base_image.size)
    new_image = Image.new('RGB', base_image.size)

    # Overlay the pattern on the original image
    for y in range(base_image.size[1]):
        for x in range(base_image.size[0]):
            if overlay_pattern.getpixel((x, y)) == (255, 255, 255) and base_image.getpixel((x, y)) == (255, 255, 255, 255):
                new_image.putpixel((x, y), (255, 255, 255))

    return new_image

def main(image_path, line_spacing):
    # Load the original image
    original_image = Image.open(image_path)
    
    # Create the white lines pattern
    white_lines_pattern = create_white_lines_pattern(original_image.width, original_image.height, line_spacing)
    
    # Overlay the pattern onto the original image
    final_image = overlay_images(original_image, white_lines_pattern)
    
    # Save the styled image
    final_image.save(f"styled_{image_path}")

# Path to the original image
image_path = "sketch_logo.png"  # Assuming the image is saved at this path
line_spacing = 50  # Spacing between lines, adjust as needed

# Call the main function

if __name__ == "__main__":
    main(image_path, line_spacing)