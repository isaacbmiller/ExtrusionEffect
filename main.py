from PIL import Image, ImageDraw
import os
from datetime import datetime

def create_white_lines_pattern(image_width, image_height, line_spacing, line_width, min_y, max_y, num_lines=17):
    # Create a new image with the same dimensions as the original
    pattern_image = Image.new('RGB', (image_width, image_height), color='black')

    # Initialize the drawing context with the pattern image
    draw = ImageDraw.Draw(pattern_image)

    # find max and min white pixels
    # divive the range by num_lines, accounting for line_width and line_spacing

    # max_y - min_y = 17 * (line_width*2 + line_spacing)

    line_spacing = int((max_y - min_y) / num_lines - line_width*2)
    current_y = min_y
    # line_widths = [12, 12, 12, 10, 10, 10, 10, 8, 8, 8, 8, 6, 6, 6, 4, 4, 4]

    # line_locations = []
    # for i in range(num_lines):
    #     line_locations.append(current_y)
    #     current_y += line_widths[i] + line_spacing
    # print(current_y, max_y)

    # Draw white horizontal lines across the pattern image with the specified spacing
    y = min_y
    while y < max_y:
        draw.line((0, y, image_width, y), fill='white', width=line_width)
        y += line_spacing + line_width*2
    # for i in range(num_lines):
    #     y = line_locations[i]
    #     draw.line((0, y, image_width, y), fill='white', width=line_widths[i])

    pattern_image.save("./images/results/white_lines_pattern.png")

    return pattern_image, line_spacing

def find_max_min_y(image):
    min_y = image.size[1]
    max_y = 0
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            if image.getpixel((x, y)) == (255, 255, 255, 255):
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
    return min_y, max_y

def draw_quadratic_curve(image, start_point, end_point, control_point):
    for t in range(101):  # Iterate over t from 0 to 1 in steps of 0.01
        t /= 100
        x = (1-t)**2 * start_point[0] + 2*(1-t)*t * control_point[0] + t**2 * end_point[0]
        y = (1-t)**2 * start_point[1] + 2*(1-t)*t * control_point[1] + t**2 * end_point[1]

        x, y = int(x), int(y)  # Converting to integer for pixel coordinates
        if y < image.size[1]:
            for y_offset in range(10): # TODO: Make this a variable - y_segment_width
                new_y = y + y_offset
                if new_y < image.size[1] and x < image.size[0] and x >= 0 and image.getpixel((x, new_y)) != (255, 255, 255, 255):
                    image.putpixel((x, new_y), (255, 255, 255, 123))

def mask_image(base_image, overlay_pattern, line_spacing):
    # Ensure both images have the same size
    overlay_pattern = overlay_pattern.resize(base_image.size)
    new_image = Image.new('RGBA', base_image.size)

    y_segment_width = 10
    x_segment_min_width = 10
    displacement = line_spacing
    # Overlay the pattern on the original image
    for y in range(0, base_image.size[1], y_segment_width):
        for x in range(0, base_image.size[0], x_segment_min_width):
            if overlay_pattern.getpixel((x, y)) == (255, 255, 255):
                if base_image.getpixel((x, y)) == (255, 255, 255, 255):
                    for x_offset in range(x_segment_min_width):
                        for y_offset in range(y_segment_width):
                            new_image.putpixel((x+x_offset, y + y_offset), (255, 255, 255, 255))

    new_image.save("./images/results/masked_image.png")

    # Gather the gray ranges in each row and draw the curves
    for y in range(0, base_image.size[1], y_segment_width):
        gray_ranges = []
        in_gray_range = False

        for x in range(0, base_image.size[0]):
            pixel = new_image.getpixel((x, y))

            # Check if the pixel is gray (R, G, and B are equal)
            if pixel != (255, 255, 255, 255):
                # print("Gray pixel found")
                if not in_gray_range:
                    # Start a new gray range
                    gray_ranges.append([x, None])
                    in_gray_range = True
            else:
                if in_gray_range:
                    # End the current gray range
                    gray_ranges[-1][1] = x
                    in_gray_range = False

        # Handle case where the last pixel in the row is gray
        if in_gray_range:
            gray_ranges[-1][1] = base_image.size[0]
                    

        # Draw the curves
        if len(gray_ranges) > 1:
            for idx, i in enumerate(gray_ranges):
                # Wait until we are at most 70 pixels from a white segment, or the midpoint of the range
                x_start = i[1] - 70
                scaled_displacement = displacement

                if i[1] - i[0] < 140:
                    scaled_displacement = displacement * (i[1] - i[0]) // 140
                    x_start = i[1] - (i[1] - i[0]) // 2
                elif idx == len(gray_ranges) - 1:
                    x_start = i[0] + 70

                curve_x_start, curve_y_start = i[0], y
                curve_x_end, curve_y_end = x_start, y + scaled_displacement

                need_flat = False
                if i[1] - i[0] > 140 and idx not in [0, len(gray_ranges) - 1]:
                    curve_x_end = i[0] + 70
                    need_flat = True

                slope = (curve_y_end - curve_y_start) / (curve_x_end - curve_x_start)


                if i == gray_ranges[0]:
                    for x in range(i[0], curve_x_end):
                        # Draw solid gray pixels
                        # extra_y_offset = int((x - curve_x_start) * slope)
                        if i == gray_ranges[0]:
                            extra_y_offset = scaled_displacement
                        for y_offset in range(y_segment_width):
                            new_y = y + y_offset + extra_y_offset
                            if new_y < base_image.size[1]  and new_image.getpixel((x, new_y)) != (255, 255, 255, 255):
                                new_image.putpixel((x,new_y), (255, 255, 255, 123))

                control_x = (curve_x_start + curve_x_end) // 2
                control_y = min(curve_y_start, curve_y_end) + (abs(curve_y_start - curve_y_end))

                draw_quadratic_curve(new_image, (curve_x_start, curve_y_start), (curve_x_end, curve_y_end), (control_x, control_y))
                
                
                if need_flat:
                    for x in range(curve_x_end, x_start):
                        for y_offset in range(y_segment_width):
                            new_y = y + y_offset + scaled_displacement
                            if new_y < base_image.size[1] and new_image.getpixel((x, new_y)) != (255, 255, 255, 255):
                                new_image.putpixel((x, new_y), (255, 255, 255, 123))
                
                curve_x_start, curve_y_start = x_start, y + scaled_displacement
                curve_x_end, curve_y_end = i[1], y

                slope = (curve_y_end - curve_y_start) / (curve_x_end - curve_x_start)

                if i == gray_ranges[-1]:
                    slope == 0
                # Draw quadratic curve
                # for x in range(curve_x_start, curve_x_end):
                #     extra_y_offset = int((x - curve_x_start) * slope)
                #     if i == gray_ranges[-1]:
                #         extra_y_offset = 0
                #     for y_offset in range(y_segment_width):
                #         new_y = y + y_offset + extra_y_offset + scaled_displacement
                #         if new_y < base_image.size[1] and new_image.getpixel((x, new_y)) != (255, 255, 255, 255):
                #             new_image.putpixel((x, new_y), (255, 255, 255, 123))
                # Define control point for the curve. Modify as needed.
                if i == gray_ranges[-1]:
                    for x in range(curve_x_start, curve_x_end):
                        for y_offset in range(y_segment_width):
                            new_y = y + y_offset + scaled_displacement
                            if new_y < base_image.size[1] and new_image.getpixel((x, new_y)) != (255, 255, 255, 255):
                                new_image.putpixel((x, new_y), (255, 255, 255, 123))
                else:
                    control_x = (curve_x_start + curve_x_end) // 2
                    control_y = min(curve_y_start, curve_y_end) + (abs(curve_y_start - curve_y_end))

                    draw_quadratic_curve(new_image, (curve_x_start, curve_y_start), (curve_x_end, curve_y_end), (control_x, control_y))

    return new_image


def generate_design(input_path, output_path, line_spacing, line_width, background_color=(255, 0, 0)):
    # Load the original image
    original_image = Image.open(input_path)

    # Add the background color to the original image
    # original_image = original_image.convert('RGBA') 

    

    # original_image = background_image
    # original_image = Image.alpha_composite(Image.new('RGBA', original_image.size, background_color), original_image)
    
    min_y, max_y = find_max_min_y(original_image)
    # Create the white lines pattern
    white_lines_pattern, line_spacing = create_white_lines_pattern(original_image.width, original_image.height, line_spacing, line_width, min_y, max_y)
    
    # Overlay the pattern onto the original image
    final_image = mask_image(original_image, white_lines_pattern, line_spacing)

    # Example usage:
    forward_search_range = 20  # Horizontal distance to search forward

    background_image = Image.new('RGBA', original_image.size, (36,105,126))

    # Paste the original image onto the background image
    # Since the original image is 'RGBA', the alpha channel will be used to blend it onto the background
    background_image.paste(final_image, (0, 0), final_image)

    # background_image.save("./images/results/background_image.png")

    # Save the styled image
    background_image.save(output_path)

# TODO: Automatically determine based off of number of lines desired and image size
    
# num lines = 17
line_spacing = 60  # Spacing between lines, adjust as needed
line_width = 10  # Width of the lines

# Call the main function
def test_harness():
    # Goal: Greate a 3xN grid of images for all images in ./images
    # 1. Original image - /images/test_cases/{filename}.png
    # 2. Current output - /images/results/{filename}_current.png
    # 3. Desired output - /images/test_cases/{filename}_desired.png


    grid_files = []
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for filename in os.listdir("./images/test_cases"):
        if "desired" in filename:
            continue
        input_filename = f"./images/test_cases/{filename}"
        output_filename = f"./images/results/{''.join(filename.split('.')[:-1])}_current.png"
        desired_filename = f"./images/test_cases/{''.join(filename.split('.')[:-1])}_desired.png"
        grid_files.append([output_filename, desired_filename])
        generate_design(input_filename, output_filename, line_spacing, line_width)

    # Create an archive in /tests/{timestamp}
    os.mkdir(f"./tests/{timestamp}")

    # Save the combined image to /tests/{timestamp}/combined.png
    combined_image = Image.new('RGBA', (1000, len(grid_files) * 300))
    for i in range(len(grid_files)):
        for j in range(len(grid_files[i])):
            # Open the image and paste it into the combined image and fit each image to 500x500 but keep aspect ratio
            image = Image.open(grid_files[i][j])
            image.thumbnail((500, 300))
            combined_image.paste(image, (j * 500, i * 300))
    # Save the archive of the created images to /tests/{timestamp}/archive.zip
    combined_image.save(f"./tests/{timestamp}/combined.png")
    combined_image.save(f"./images/results/combined.png")
    

if __name__ == "__main__":
    test_harness()