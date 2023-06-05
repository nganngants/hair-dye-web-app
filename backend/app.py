from flask import Flask, request, send_file
from PIL import Image
import numpy as np
from io import BytesIO
from HairDye import HairDye

app = Flask(__name__)

@app.route('/dye', methods=['POST'])
def dye_hair():
    color = request.form.get('color')
    image = request.files['image']

    # Convert image to numpy array
    pil_image = Image.open(image)
    if pil_image.format=="PNG":
       pil_image = pil_image.convert("RGB")
    numpy_image = np.array(pil_image)

    # Pass the color and image to the HairDye model
    hair_dye = HairDye()
    result_image = hair_dye.predict(numpy_image, color)

    # Convert the result image back to PIL Image
    result_pil_image = Image.fromarray(result_image)

    # Create a BytesIO object to temporarily store the result image
    result_image_stream = BytesIO()
    result_pil_image.save(result_image_stream, format='JPEG')
    result_image_stream.seek(0)

    # Return the result image
    return send_file(result_image_stream, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run()
