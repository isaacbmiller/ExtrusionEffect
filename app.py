from flask import Flask, render_template, request
from main import generate_design
from PIL import Image

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    if request.method == 'POST':
        file = request.files['image']
        # Process the image file using your script

        image = Image.open(file)

        line_spacing = 60
        line_width = 10
        background_color = (0, 0, 0)

        processed_image = generate_design(image, line_spacing, line_width, background_color)
        # processed_image.save('static/processed_image.png')
        # Save or display the processed image as needed
        return render_template('result.html', image=processed_image)

if __name__ == '__main__':
    app.run(debug=True)