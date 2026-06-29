# app.py
from flask import Flask, request, render_template, send_file, jsonify
import requests
import os
from PIL import Image
import io
import base64

app = Flask(__name__)

PIXAZO_API_URL = "https://api.pixazo.ai/v1/inpaint"  # يجب التأكد من صحة الرابط من وثائقهم
# احصل على مفتاح API مجاني من موقع Pixazo
API_KEY = "50eb5e66145c4635b2b8882640d9dea3" 

def inpaint_image(image_path, mask_path, prompt):
    with open(image_path, 'rb') as img_file, open(mask_path, 'rb') as mask_file:
        files = {
            'image': img_file,
            'mask': mask_file,
        }
        data = {
            'prompt': prompt,
        }
        headers = {
            'Authorization': f'Bearer {API_KEY}'
        }
        response = requests.post(PIXAZO_API_URL, files=files, data=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")

@app.route('/', methods=['GET'])
def index():
    return '''
    <form method="post" enctype="multipart/form-data" action="/process">
        <input type="file" name="image" accept="image/*"><br>
        <input type="file" name="mask" accept="image/*"><br>
        <input type="text" name="prompt" placeholder="Prompt (e.g., nude body)"><br>
        <input type="submit" value="تنفيذ">
    </form>
    '''

@app.route('/process', methods=['POST'])
def process():
    try:
        image_file = request.files['image']
        mask_file = request.files['mask']
        prompt = request.form['prompt']

        if not image_file or not mask_file:
            return jsonify({'error': 'Missing image or mask'}), 400

        # حفظ الملفات مؤقتاً
        img_path = "temp_img.png"
        mask_path = "temp_mask.png"
        image_file.save(img_path)
        mask_file.save(mask_path)

        result_image_bytes = inpaint_image(img_path, mask_path, prompt)

        # تنظيف
        os.remove(img_path)
        os.remove(mask_path)

        return send_file(
            io.BytesIO(result_image_bytes),
            mimetype='image/png',
            as_attachment=True,
            download_name='result.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
