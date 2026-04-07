# 🚀 Build VoxLite from Scratch: Complete Step-by-Step Guide

This guide will help you build the **entire** `app.py` file from scratch. Each step adds more logic until you have the full, production-ready backend.

---

## 🛠 Step 1: Imports and Initial Setup
First, we import all necessary libraries for web handling, database, security, and AI. We also set up logging and folder paths.

**Code (Start your app.py with this):**
```python
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
import uuid
import torch
import logging
from werkzeug.utils import secure_filename
from TTS.api import TTS
from pydub import AudioSegment
import tempfile
from datetime import datetime
from pydub.utils import which
import torch.serialization
from TTS.tts.configs.xtts_config import XttsConfig

# Setup FFmpeg for audio processing
AudioSegment.converter = which("ffmpeg")

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Voice cloning configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a'}
MAX_FILE_SIZE_MB = 100

# Create folders automatically
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024
```

---

## 🔐 Step 2: Database and User Security
Now, we configure the SQLite database and create the User model with password encryption.

**Add this to your app.py:**
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    
# Create tables automatically
with app.app_context():
    db.create_all()
```

---

## 🔑 Step 3: Authentication Routes (Register & Login)
In this step, we add the logic for creating accounts and logging users in.

**Add this to your app.py:**
```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Simple validation
        error = None
        if not all([name, email, password, confirm_password]):
            error = 'All fields are required'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered'

        if error:
            flash(error, 'error')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')
```

---

## 🧠 Step 4: AI Model and Voice Cloning (Processing Audio)
This is the final part where we load the AI and create the cloning magic.

**Add this to your app.py:**
```python
tts_model_instance = None
model_init_error = None

def get_tts_model():
    global tts_model_instance, model_init_error
    if tts_model_instance is None and model_init_error is None:
        try:
            from TTS.tts.models.xtts import XttsAudioConfig
            torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
            device = "cuda" if torch.cuda.is_available() else "cpu"
            tts_model_instance = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        except Exception as e:
            model_init_error = str(e)
    return tts_model_instance

def convert_to_wav(input_file_path):
    audio = AudioSegment.from_file(input_file_path)
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    audio.export(temp_wav.name, format="wav")
    return temp_wav.name, temp_wav.name

@app.route('/clone_voice', methods=['POST'])
def clone_voice():
    model = get_tts_model()
    text = request.form.get('text')
    file = request.files.get('voice_sample')
    
    # Process and Clone
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(original_path)
    
    try:
        wav_path, _ = convert_to_wav(original_path)
        output_name = f"output_{uuid.uuid4()}.wav"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_name)
        
        # This creates the cloned voice!
        model.tts_to_file(text=text, file_path=output_path, speaker_wav=wav_path, language=request.form.get('language', 'en'))

        return jsonify({'success': True, 'audio_url': url_for('download_file', filename=output_name)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename))

@app.route('/')
def index(): return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False)
```

---
**Done!** You now have the full `app.py` matching the original project.
