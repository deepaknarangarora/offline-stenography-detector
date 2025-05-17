from flask import Flask, render_template, request, redirect, url_for, flash
import os
import numpy as np
from PIL import Image
import wave
import re
import time

# Initialize Flask application
app = Flask(__name__)

# Folder to store uploaded files
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Secret key for Flask flash messages
app.secret_key = 'supersecretkey'

# Valid file extensions
VALID_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'bmp']
VALID_AUDIO_EXTENSIONS = ['wav']
VALID_TEXT_EXTENSIONS = ['txt']

# Extract hidden message from image using LSB
def extract_lsb_message(image_path):
    image = Image.open(image_path).convert('RGB')
    pixels = np.array(image).flatten()
    bits = [str(pixel & 1) for pixel in pixels]
    chars = []
    for b in range(0, len(bits), 8):
        byte = bits[b:b+8]
        if len(byte) < 8:
            break
        char = chr(int(''.join(byte), 2))
        if char == '\0':  # Null terminator
            break
        chars.append(char)
    message = ''.join(chars)
    return message if message else "No readable hidden message found."

# Audio Steganography Detection (basic average magnitude test)
def extract_audio_samples(audio_path):
    with wave.open(audio_path, 'rb') as audio_file:
        num_frames = audio_file.getnframes()
        frames = audio_file.readframes(num_frames)
        samples = np.frombuffer(frames, dtype=np.int16)
    return samples

def detect_audio_steganography(audio_path):
    samples = extract_audio_samples(audio_path)
    mean_value = np.mean(np.abs(samples))
    if mean_value < 50:
        return "Possible hidden data detected in audio file!"
    else:
        return "No hidden data detected in audio file."

# Text Steganography Detection

def detect_text_steganography(text):
    invisible_characters = re.findall(r'[\u200B-\u200D\uFEFF]', text)
    if invisible_characters:
        return f"Possible hidden data detected in text! Found {len(invisible_characters)} invisible characters."
    else:
        return "No hidden data detected in text."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    file_type = file.filename.split('.')[-1].lower()
    if file_type not in VALID_IMAGE_EXTENSIONS + VALID_AUDIO_EXTENSIONS + VALID_TEXT_EXTENSIONS:
        flash("Unsupported file format. Only image, audio, or text files are allowed.")
        return redirect(request.url)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    time.sleep(2)

    try:
        if file_type in VALID_IMAGE_EXTENSIONS:
            result = extract_lsb_message(file_path)
        elif file_type in VALID_AUDIO_EXTENSIONS:
            result = detect_audio_steganography(file_path)
        elif file_type in VALID_TEXT_EXTENSIONS:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            result = detect_text_steganography(text_content)
    except Exception as e:
        flash(f"Error occurred while processing the file: {str(e)}")
        return redirect(request.url)

    return render_template('result.html', result=result, file_name=file.filename)

if __name__ == '__main__':
    app.run(debug=True)
