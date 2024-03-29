from PIL import Image, ImageDraw
import os
from os.path import join
from datetime import datetime
import numpy as np

def create_white_lines_pattern(image_width, image_height, line_spacing, line_width, min_y, max_y, num_lines=17):
    # Create a new image with the same dimensions as the original
    pattern_image = Image.new('RGB', (image_width, image_height), color='black')

    # Initialize the drawing context with the pattern image
    draw = ImageDraw.Draw(pattern_image)

    # find max and min white pixels
    # max_y - min_y = 17 * (line_width*2 + line_spacing)

    line_spacing = int((max_y - min_y) / num_lines - line_width*2)

    # Draw white horizontal lines across the pattern image with the specified spacing
    y = min_y
    while y < max_y:
        draw.line((0, y, image_width, y), fill='white', width=line_width)
        y += line_spacing + line_width*2

    print(f"Line spacing: {line_spacing}")
    

    # pattern_image.save("./api/static/white_lines_pattern.png")

    return pattern_image, line_spacing

def find_max_min_y(image):
    # Convert PIL image to Numpy array
    np_image = np.array(image)

    # Find rows containing the target color
    rows_with_white = np.any(np.all(np_image == [255, 255, 255, 255], axis=2), axis=1)

    # Get min and max y indices
    y_indices = np.where(rows_with_white)[0]
    min_y = y_indices.min() if y_indices.size > 0 else 0
    max_y = y_indices.max() if y_indices.size > 0 else image.size[1]

    return min_y, max_y

def find_max_min_x(image):
    # Convert PIL image to Numpy array
    np_image = np.array(image)

    # Find columns containing the target color
    cols_with_white = np.any(np.all(np_image == [255, 255, 255, 255], axis=2), axis=0)

    # Get min and max x indices
    x_indices = np.where(cols_with_white)[0]
    min_x = x_indices.min() if x_indices.size > 0 else 0
    max_x = x_indices.max() if x_indices.size > 0 else image.size[0]

    return min_x, max_x

def draw_quadratic_curve(image, start_point, end_point, control_point):
    for t in range(101):  # Iterate over t from 0 to 1 in steps of 0.01
        t /= 100
        x = (1-t)**2 * start_point[0] + 2*(1-t)*t * control_point[0] + t**2 * end_point[0]
        y = (1-t)**2 * start_point[1] + 2*(1-t)*t * control_point[1] + t**2 * end_point[1]

        x, y = int(x), int(y)  # Converting to integer for pixel coordinates

        y_opacity_min = 150
        y_opacity_max = 255

        def opacity(y):
            if end_point[1] - start_point[1] == 0:
                return 0
            if end_point[1] < start_point[1]:
                return int(y_opacity_min + (y_opacity_max - y_opacity_min) * (y - start_point[1]) / (end_point[1] - start_point[1])) - 1
            return int(y_opacity_min + (y_opacity_max - y_opacity_min) * (end_point[1] - y) / (end_point[1] - start_point[1])) - 1

        if y < image.size[1]:
            for y_offset in range(10): # TODO: Make this a variable - y_segment_width
                new_y = y + y_offset
                if new_y < image.size[1] and x < image.size[0] and x >= 0 and image.getpixel((x, new_y)) != (255, 255, 255, 255):
                    image.putpixel((x, new_y), (255, 255, 255, opacity(y)))

def mask_image(base_image, overlay_pattern, line_spacing):
    # Ensure both images have the same size
    overlay_pattern = overlay_pattern.resize(base_image.size)
    new_image = Image.new('RGBA', base_image.size)

    y_segment_width = 10
    x_segment_min_width = 10
    displacement = line_spacing
    # Overlay the pattern on the original image
    start_time = datetime.now()
    previous_time = start_time
    print("delta time in mask: ", datetime.now() - previous_time)
    for y in range(0, base_image.size[1], y_segment_width):
        for x in range(0, base_image.size[0], x_segment_min_width):
            if overlay_pattern.getpixel((x, y)) == (255, 255, 255) and base_image.getpixel((x, y)) == (255, 255, 255, 255):
                for x_offset in range(x_segment_min_width):
                    for y_offset in range(y_segment_width):
                        if y + y_offset < base_image.size[1] and x + x_offset < base_image.size[0]:
                            new_image.putpixel((x+x_offset, y + y_offset), (255, 255, 255, 255))

    # new_image.save(join('data', 'masked_image.png'))
    print(f"Masked image")
    print("Current time after mask: ", datetime.now() - start_time)

    min_x, max_x = find_max_min_x(new_image)
    min_x_offset, max_x_offset = min_x - 150, max_x + 150
    # Gather the gray ranges in each row and draw the curves
    for y in range(0, base_image.size[1], y_segment_width):
        # print(f"Drawing curves for row {y}")
        # print("Current delta: ", datetime.now() - start_time)
        previous_time = datetime.now()

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
                
                if i == gray_ranges[0]:
                    def opacity(x):
                        if x <= min_x_offset:
                            # between curve_x_start and min_x_offset, opacity scales linearly from 0 to 30
                            return int(30 * (x - curve_x_start) / (min_x_offset - curve_x_start))
                        # between min_x_offset and i[1], opacity scales linearly from 30 to 150

                        return int(30 + 120 * (x - min_x_offset) / (curve_x_end - min_x_offset))
                    for x in range(i[0], curve_x_end):
                        # Draw solid gray pixels
                        if y + scaled_displacement + y_segment_width < base_image.size[1]:
                            new_y = y + scaled_displacement
                            for y_offset in range(y_segment_width):
                                new_image.putpixel((x,new_y), (255, 255, 255, opacity(x)))
                                new_y += 1
                else:
                    control_x = (curve_x_start + curve_x_end) // 2
                    control_y = min(curve_y_start, curve_y_end) + (abs(curve_y_start - curve_y_end))

                    draw_quadratic_curve(new_image, (curve_x_start, curve_y_start), (curve_x_end, curve_y_end), (control_x, control_y))
                
                if need_flat:
                    for x in range(curve_x_end, x_start):
                        for y_offset in range(y_segment_width):
                            new_y = y + y_offset + scaled_displacement
                            if new_y < base_image.size[1]:
                            # and new_image.getpixel((x, new_y)) != (255, 255, 255, 255):
                                new_image.putpixel((x, new_y), (255, 255, 255, 150))
                
                curve_x_start, curve_y_start = x_start, y + scaled_displacement
                curve_x_end, curve_y_end = i[1], y

                # Define control point for the curve. Modify as needed.
                if i == gray_ranges[-1]:
                    def opacity(x):
                        if x >= max_x_offset:
                            return int(30 - 30 * (x - max_x_offset) / (curve_x_end - max_x_offset))
                        return int(30 + 120 * (max_x_offset - x) / (max_x_offset - curve_x_start))
                    for x in range(curve_x_start, curve_x_end):
                        if y + scaled_displacement + y_segment_width < base_image.size[1]:
                            new_y = y + scaled_displacement
                            for _ in range(y_segment_width):
                                new_image.putpixel((x, new_y), (255, 255, 255, opacity(x)))
                                new_y += 1
                                # if new_y < base_image.size[1]:
                                # and new_image.getpixel((x, new_y)) != (255, 255, 255, 255):
                else:
                    control_x = (curve_x_start + curve_x_end) // 2
                    control_y = min(curve_y_start, curve_y_end) + (abs(curve_y_start - curve_y_end))

                    draw_quadratic_curve(new_image, (curve_x_start, curve_y_start), (curve_x_end, curve_y_end), (control_x, control_y))
                    
    print(f"Curves drawn")
    print(f"total_time: {datetime.now() - start_time}")
    return new_image


def generate_design(input_image, line_spacing, line_width, background_color):
    # Load the original image

    # Add the background color to the original image
    start_time = datetime.now()
    print("starting to generate design, time: ", datetime.now())

    # Convert to RGBA if necessary
    if input_image.mode != 'RGBA':
        input_image = input_image.convert('RGBA')
        print("converted to RGBA, time: ", datetime.now(), "delta time: ", datetime.now() - start_time)

    # Resize the image to have max width/heigth of 1500
    max_width, max_height = 1500, 1500
    min_width, min_height = 1000, 1000

    if input_image.width > max_width or input_image.height > max_height:
        if input_image.width > input_image.height:
            input_image = input_image.resize((max_width, int(max_width * input_image.height / input_image.width)))
        else:
            input_image = input_image.resize((int(max_height * input_image.width / input_image.height), max_height))
        print("resized image, time: ", datetime.now(), "delta time: ", datetime.now() - start_time)

    elif input_image.width < min_width or input_image.height < min_height:
        if input_image.width < input_image.height:
            input_image = input_image.resize((min_width, int(min_width * input_image.height / input_image.width)))
        else:
            input_image = input_image.resize((int(min_height * input_image.width / input_image.height), min_height))
        print("resized image, time: ", datetime.now(), "delta time: ", datetime.now() - start_time)

    min_y, max_y = find_max_min_y(input_image)
    print("min_y, max_y found, time: ", datetime.now(), "delta time: ", datetime.now() - start_time)
    # Create the white lines pattern
    white_lines_pattern, line_spacing = create_white_lines_pattern(input_image.width, input_image.height, line_spacing, line_width, min_y, max_y)
    print("white lines pattern created, time: ", datetime.now(), "delta time: ", datetime.now() - start_time)
    # Overlay the pattern onto the original image
    final_image = mask_image(input_image, white_lines_pattern, line_spacing)
    print("final image created, time: ", datetime.now(), "delta time: ", datetime.now() - start_time)

    background_image = Image.new('RGBA', input_image.size, background_color)
    print("background image created, time: ", datetime.now() - start_time)
    # Paste the original image onto the background image
    background_image.paste(final_image, (0, 0), final_image)
    print("final image pasted onto background image, time: ", datetime.now() - start_time)
    # background_image.save(join('data', 'final_image.png'))
    print("total time: ", datetime.now() - start_time)

    return background_image

def generate_local_design(input_path, output_path, line_spacing, line_width, background_color=(0, 0, 0)):
    # Load the original image
    image = Image.open(input_path)

    image = generate_design(image, line_spacing, line_width, background_color)

    # Save the styled image
    image.save(output_path)

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
        # look for only PNG
        if ".png" not in filename:
            continue


        
        background_color = (255, 255, 255)
        if "pen" in filename:
            background_color = (61, 122, 86, 255)
        elif "bolt" in filename:
            background_color = (103, 83, 145, 255)
        elif "sketch" in filename:
            background_color = (188, 91, 42, 255)

        input_filename = f"./images/test_cases/{filename}"
        output_filename = f"./images/results/{''.join(filename.split('.')[:-1])}_current.png"
        desired_filename = f"./images/test_cases/{''.join(filename.split('.')[:-1])}_desired.png"
        grid_files.append([output_filename, desired_filename])
        generate_local_design(input_filename, output_filename, line_spacing, line_width, background_color=background_color)

    # Create an archive in /tests/{timestamp}
    os.mkdir(f"./logs/{timestamp}")

    
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