from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import bcrypt
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
# Add this import for the specific config class mentioned in the error
from TTS.tts.configs.xtts_config import XttsConfig

from pydub.utils import which
AudioSegment.converter = which("ffmpeg")


# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Voice cloning configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg', 'm4a'}
MAX_FILE_SIZE_MB = 100

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024

db = SQLAlchemy(app)

# --- Model Initialization (Lazy Loading) ---
tts_model_instance = None
model_init_error = None

def get_tts_model():
    """Loads the XTTS v2 model."""
    global tts_model_instance, model_init_error
    if tts_model_instance is None and model_init_error is None:
        try:
            # --- FIX: Add the necessary classes to safe globals ---
            logger.info("Adding XTTS config classes to PyTorch safe globals (for PyTorch >= 2.6 compatibility)")
            # Import the additional required class
            from TTS.tts.models.xtts import XttsAudioConfig
            # Allowlist all specific config classes mentioned in the error
            torch.serialization.add_safe_globals([XttsConfig, XttsAudioConfig])
            
            # Alternative approach using weights_only=False if allowlisting fails
            # Modify the TTS library's torch.load calls
            original_torch_load = torch.load
            def patched_torch_load(*args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return original_torch_load(*args, **kwargs)
            
            # Temporarily patch torch.load
            torch.load = patched_torch_load
            # --- End of FIX ---

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Initializing XTTS v2 model on {device}...")
            # Use XTTS v2 - generally better for multilingual cloning
            tts_model_instance = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                                     progress_bar=True).to(device) # Enable progress bar for download
            logger.info("XTTS v2 model loaded successfully.")
            
            # Restore original torch.load function
            torch.load = original_torch_load
        except Exception as e:
            logger.error(f"FATAL: Failed to initialize TTS model: {e}", exc_info=True)
            # Check if it's the weights_only error specifically for a clearer message
            if "Weights only load failed" in str(e):
                 model_init_error = f"Could not load TTS model due to PyTorch compatibility issue. Attempted fix failed or requires further action. Original error: {e}"
            else:
                 model_init_error = f"Could not load the TTS voice cloning model: {e}. Check logs."
            tts_model_instance = None # Ensure it stays None
    return tts_model_instance

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
# Create the database tables
with app.app_context():
    db.create_all()


# Simple in-memory user store for demo purposes
users = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_wav(input_file_path):
    _, file_ext = os.path.splitext(input_file_path)
    file_ext = file_ext.lower()

    if file_ext == '.wav':
        return input_file_path, None

    try:
        temp_wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wav_path = temp_wav_file.name
        temp_wav_file.close()

        audio = AudioSegment.from_file(input_file_path)
        audio.export(wav_path, format="wav")
        return wav_path, wav_path
    except Exception as e:
        raise ValueError(f"Failed to convert audio file to WAV: {e}") from e

def split_hindi_text(text, max_chars=200):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 <= max_chars:
            current_chunk.append(word)
            current_length += len(word) + 1
        else:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def combine_audio_files(audio_paths, output_path):
    combined = AudioSegment.empty()
    for path in audio_paths:
        audio = AudioSegment.from_file(path)
        combined += audio
    combined.export(output_path, format="wav")
    return output_path

def get_supported_languages():
    return {
        'en': 'English',
        'hi': 'Hindi (Devanagari Script)',
        'hinglish': 'Hinglish (Roman Script)'
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/voice_clone')
def voice_clone_page():
    get_tts_model()  # Initialize model if not already loaded
    if model_init_error:
        flash(f"Voice Cloning System Error: {model_init_error}", "error")
    return render_template('voice_clone.html', languages=get_supported_languages())

@app.route('/clone_voice', methods=['POST'])
def clone_voice():
    model = get_tts_model()
    if model is None or model_init_error:
        return jsonify({'success': False, 'message': f"TTS Model Error: {model_init_error or 'Not available'}"}), 503

    if 'text' not in request.form or not request.form['text'].strip():
        return jsonify({'success': False, 'message': 'Text input is required.'}), 400
    text = request.form['text'].strip()

    if 'voice_sample' not in request.files:
        return jsonify({'success': False, 'message': 'Voice sample file is required.'}), 400

    file = request.files['voice_sample']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No voice sample file selected.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': f'File type not allowed. Use: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    selected_language_option = request.form.get('language', 'en')

    temp_input_filename = f"input_{uuid.uuid4()}{os.path.splitext(secure_filename(file.filename))[1]}"
    original_input_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_input_filename)
    file.save(original_input_path)

    converted_wav_path = None
    temp_wav_path_info = None

    try:
        converted_wav_path, temp_wav_path_info = convert_to_wav(original_input_path)

        if selected_language_option == 'hinglish':
            lang_code = 'en'
        elif selected_language_option == 'hi':
            lang_code = 'hi'
        else:
            lang_code = selected_language_option

        output_filename = f"output_{uuid.uuid4()}.wav"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        if selected_language_option == 'hi' and len(text) > 200:
            text_chunks = split_hindi_text(text)
            temp_audio_files = []
            
            try:
                for i, chunk in enumerate(text_chunks):
                    temp_output = os.path.join(app.config['OUTPUT_FOLDER'], f"temp_chunk_{uuid.uuid4()}.wav")
                    model.tts_to_file(
                        text=chunk,
                        file_path=temp_output,
                        speaker_wav=converted_wav_path,
                        language=lang_code
                    )
                    temp_audio_files.append(temp_output)
                
                combine_audio_files(temp_audio_files, output_path)
            finally:
                for temp_file in temp_audio_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"Could not delete temporary chunk file {temp_file}: {e}")
        else:
            model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=converted_wav_path,
                language=lang_code
            )

        return jsonify({
            'success': True,
            'message': 'Speech generated successfully.',
            'audio_url': url_for('download_file', filename=output_filename),
            'download_name': f"cloned_{selected_language_option}_{datetime.now():%Y%m%d_%H%M}.wav"
        })

    except Exception as e:
        logger.error(f"Error during TTS generation: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

    finally:
        if os.path.exists(original_input_path):
            try:
                os.remove(original_input_path)
            except OSError as e:
                logger.warning(f"Could not delete temp input file {original_input_path}: {e}")

        if temp_wav_path_info is not None and os.path.exists(temp_wav_path_info):
            try:
                os.remove(temp_wav_path_info)
            except OSError as e:
                logger.warning(f"Could not delete temp converted WAV file {temp_wav_path_info}: {e}")

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.normpath(file_path).startswith(os.path.normpath(app.config['OUTPUT_FOLDER'])):
        return "Forbidden", 403
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(
        file_path,
        mimetype="audio/wav",
        as_attachment=True,
        download_name=filename
    )

# Existing routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user'] = user.name
            return redirect(url_for('index'))
        
        # In a real app, you would flash a message here
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation checks
        error = None
        if not all([name, email, password, confirm_password]):
            error = 'All fields are required'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long'
        elif not any(char.isdigit() for char in password):
            error = 'Password must contain at least one digit'
        elif not any(char.isalpha() for char in password):
            error = 'Password must contain at least one letter'
        elif not any(char in '!@#$%^&*()_+' for char in password):
            error = 'Password must contain at least one special character'
        elif not any(char.isupper() for char in password):
            error = 'Password must contain at least one uppercase letter'
        elif User.query.filter_by(email=email).first():
            error = 'Email already registered'

        if error:
            flash(error, 'error')
            return redirect(url_for('register'))

        # If validation passes, create new user
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("--- Starting VoxLite Voice Cloning Service ---")
    get_tts_model()  # Initialize model at startup
    app.run(debug=False)