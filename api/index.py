from flask import Flask, render_template, request
from api.main import generate_design
from PIL import Image
from os.path import join
import base64
from io import BytesIO

app = Flask(__name__)

def get_image_data(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue())
    return image_base64.decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    if request.method == 'POST':
        file = request.files['image']
        background_color = request.form['background-color']
        # convert the background color from hex to rgb
        background_color = background_color.lstrip('#')
        background_color = tuple(int(background_color[i:i+2], 16) for i in (0, 2, 4))

        image = Image.open(file)

        line_spacing = 60
        line_width = 10

        processed_image = generate_design(image, line_spacing, line_width, background_color)
        processed_image_base64 = get_image_data(processed_image)
        return render_template('result.html', image_data=processed_image_base64)

if __name__ == '__main__':
    app.run(debug=True)