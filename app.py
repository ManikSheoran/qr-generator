from flask import Flask, render_template, request, send_file
import qrcode
from PIL import Image
import requests
from io import BytesIO
import os
from waitress import serve

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/qr_codes'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form['data']
        brand_image_url = request.form['brand_image_url']
        qr_color = request.form.get('qr_color', '#A294F9')
        qr_path = create_colorful_qr_with_url_image(data, brand_image_url, qr_color)
        
        return send_file(qr_path, mimetype='image/png', as_attachment=True, download_name='qr_code.png')
    return render_template('index.html')

def create_colorful_qr_with_url_image(data, brand_image_url, qr_color):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Use the user-provided color and set background transparent
    qr_img = qr.make_image(fill_color=qr_color, back_color=None).convert("RGBA")
    
    width, height = qr_img.size
    gradient = Image.new("RGBA", (width, height), color=(0, 0, 0))  # Transparent background

    qr_pixels = qr_img.load()
    for x in range(width):
        for y in range(height):
            if qr_pixels[x, y][3] != 0:  # Copy only non-transparent pixels
                gradient.putpixel((x, y), qr_pixels[x, y])

    qr_img = gradient

    if brand_image_url:
        response = requests.get(brand_image_url)
        if response.status_code == 200:
            brand_img = Image.open(BytesIO(response.content)).convert("RGBA")
            box_size = min(width, height) // 4
            brand_img = brand_img.resize((box_size, box_size), Image.Resampling.LANCZOS)

            x_offset = (width - box_size) // 2
            y_offset = (height - box_size) // 2
            qr_img.paste(brand_img, (x_offset, y_offset), mask=brand_img)

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'qr_code.png')
    qr_img.save(output_path)
    return output_path

if __name__ == '__main__':
    # app.run(debug=True)
    serve(app, host='0.0.0.0', port=8080)
