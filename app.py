import os
import replicate
import requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import json
import logging
import base64

# Initialize the Flask app
app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/outputs'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure Replicate API token is set
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN is not set in the environment.")

replicate.Client(api_token=REPLICATE_API_TOKEN)  # Initialize Replicate client with API token

# Logging configuration
logging.basicConfig(level=logging.DEBUG)
logging.debug(f"Using Replicate API token: {REPLICATE_API_TOKEN}")

def allowed_file(filename):
    """Check if the file is allowed based on the extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def upload_image():
    """Render the upload page."""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'image' not in request.files:
        return redirect(request.url)
    file = request.files['image']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('edit_image', image_filename=filename))
    return redirect(request.url)

@app.route('/edit/<image_filename>')
def edit_image(image_filename):
    """Render the image editing page."""
    return render_template('edit_image.html', image_filename=image_filename)

@app.route('/process_image', methods=['POST'])
def process_image():
    """Process the image and send it for inpainting using Replicate API."""
    try:
        image_filename = request.form['image_filename']
        mask_data = request.form['mask_data']  # This is the mask data in JSON format
        prompt = request.form['prompt']

        # Parse the mask data (left, top, width, height)
        mask = json.loads(mask_data)

        # Load the original image
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        original_image = Image.open(image_path).convert("RGB")

        # Create a mask image with a fully white background (255 = unchanged areas)
        mask_image = Image.new("L", original_image.size, 255)

        # Draw a black polygon (0 = selected area to edit) over the selected area
        draw = ImageDraw.Draw(mask_image)
        draw.polygon(
            [
                (mask['left'], mask['top']),
                (mask['left'] + mask['width'], mask['top']),
                (mask['left'] + mask['width'], mask['top'] + mask['height']),
                (mask['left'], mask['top'] + mask['height'])
            ],
            fill=0
        )

        # Save the original and mask images temporarily for API request
        init_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'init_' + image_filename)
        mask_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'mask_' + image_filename)
        original_image.save(init_image_path, format="PNG")
        mask_image.save(mask_image_path, format="PNG")

        # Use replicate.run to process the image using the correct model
        output = replicate.run(
            "ideogram-ai/ideogram-v2-turbo",
            input={
                "prompt": prompt,
                "image": open(init_image_path, "rb"),
                "mask": open(mask_image_path, "rb"),
                "resolution": "None",
                "style_type": "None",
                "aspect_ratio": "1:1",
                "magic_prompt_option": "Auto"
            }
        )

        # Decode the output and save it to the output folder
        if isinstance(output, replicate.helpers.FileOutput):
            # Read the file content as bytes
            file_data = output.read()
            
            # Save the binary data to an image file
            output_image_path = os.path.join(app.config['OUTPUT_FOLDER'], 'generated_image.png')
            with open(output_image_path, 'wb') as file:
                file.write(file_data)

            # Render the result page with the image URL
            return render_template('result.html', output_image='generated_image.png')
        else:
            logging.error(f"Error: No output returned from model.")
            return jsonify({'error': 'No output generated from the model.'}), 500

    except Exception as e:
        # Log the exact error
        error_message = f"Internal Server Error: {str(e)}"
        logging.exception(error_message)  # This logs the full stack trace

        # Return the error message as part of the response for easier debugging
        return jsonify({'error': error_message}), 500


@app.route('/static/outputs/<filename>')
def output_image(filename):
    """Serve the output image."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """Serve the uploaded file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Ensure the directories exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.makedirs(app.config['OUTPUT_FOLDER'])

    # Run the Flask app in debug mode
    app.run(debug=True)
