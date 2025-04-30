import os
import uuid
import torch
import logging
from flask import Flask, request, jsonify, send_file, render_template, url_for, flash, redirect
from werkzeug.utils import secure_filename
from TTS.api import TTS
from pydub import AudioSegment
import tempfile
from datetime import datetime

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

# --- Configuration ---
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
# IMPORTANT: Use a strong, environment-variable-based secret key in production
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_voicecloningsecretkey_change_me')

# --- Model Initialization (Lazy Loading) ---
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

# --- Helper Functions ---
def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_wav(input_file_path):
    """
    Converts an audio file to WAV format using pydub.
    Returns the path to the WAV file (original or converted).
    Manages temporary files.
    """
    _, file_ext = os.path.splitext(input_file_path)
    file_ext = file_ext.lower()

    if file_ext == '.wav':
        logger.info(f"File is already WAV: {os.path.basename(input_file_path)}")
        return input_file_path, None # Return path and None for temp file handle

    # Create a temporary file path for the WAV output
    try:
        # Suffix ensures correct extension, delete=False needed to use the path after closing
        temp_wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wav_path = temp_wav_file.name
        temp_wav_file.close() # Close the handle so pydub can write to it

        logger.info(f"Attempting to convert '{os.path.basename(input_file_path)}' ({file_ext}) to WAV...")
        audio = AudioSegment.from_file(input_file_path)
        audio.export(wav_path, format="wav")
        logger.info(f"Successfully converted to temporary WAV: {wav_path}")
        # Return the path to the new WAV file and the temp file object info for later cleanup
        return wav_path, wav_path # Return path twice to indicate it's a temp file path

    except Exception as e:
        logger.error(f"Error converting file '{os.path.basename(input_file_path)}' to WAV: {e}", exc_info=True)
        # If conversion fails, return the original path and None for temp file
        # The main function should probably handle this failure
        raise ValueError(f"Failed to convert audio file to WAV: {e}") from e


def split_hindi_text(text, max_chars=200):
    """Split Hindi text into smaller chunks that respect word boundaries."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        # Add 1 for the space between words
        if current_length + len(word) + 1 <= max_chars:
            current_chunk.append(word)
            current_length += len(word) + 1
        else:
            if current_chunk:  # If we have accumulated words, join them and add to chunks
                chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
    
    if current_chunk:  # Don't forget the last chunk
        chunks.append(' '.join(current_chunk))
    
    return chunks

def combine_audio_files(audio_paths, output_path):
    """Combine multiple audio files into a single file."""
    combined = AudioSegment.empty()
    for path in audio_paths:
        audio = AudioSegment.from_file(path)
        combined += audio
    combined.export(output_path, format="wav")
    return output_path

# --- Routes ---
@app.route('/')
def index():
    """Renders the main HTML page."""
    # Check model status on page load
    get_tts_model() # Trigger loading if not already loaded
    if model_init_error:
        flash(f"Voice Cloning System Error: {model_init_error}", "error")
    return render_template('index_simple.html', # Using a new template name
                           languages=get_supported_languages(),
                           model_error=model_init_error)

def get_supported_languages():
    # Define supported languages for the dropdown, mapping to XTTS codes
    # Add more as needed based on XTTS support
    return {
        'en': 'English',
        # 'es': 'Spanish',
        # 'fr': 'French',
        # 'de': 'German',
        # 'it': 'Italian',
        # 'pt': 'Portuguese',
        # 'pl': 'Polish',
        # 'tr': 'Turkish',
        # 'ru': 'Russian',
        # 'nl': 'Dutch',
        # 'cs': 'Czech',
        # 'ar': 'Arabic',
        # 'zh-cn': 'Chinese (Mandarin, Simplified)',
        # 'ja': 'Japanese', # Added Japanese
        # 'ko': 'Korean',  # Added Korean
        # 'hu': 'Hungarian',# Added Hungarian
        # 'sv': 'Swedish', # Added Swedish
        # # --- Focus Languages ---
        'hi': 'Hindi (Devanagari Script)',
        'hinglish': 'Hinglish (Roman Script)' # Special case handled in code
    }


@app.route('/clone_voice', methods=['POST'])
def clone_voice():
    """Handles voice cloning requests from the web form."""
    # Check if model is available first
    model = get_tts_model()
    if model is None or model_init_error:
        flash(f"Voice Cloning System Error: {model_init_error or 'Model not available.'}", "error")
        return redirect(url_for('index'))

    # --- Form Data Validation ---
    if 'text' not in request.form or not request.form['text'].strip():
        flash('Text input is required.', 'error')
        return redirect(url_for('index'))
    text = request.form['text'].strip()

    if 'voice_sample' not in request.files:
        flash('Voice sample file is required.', 'error')
        return redirect(url_for('index'))

    file = request.files['voice_sample']
    if file.filename == '':
        flash('No voice sample file selected.', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash(f'File type not allowed. Use one of: {", ".join(ALLOWED_EXTENSIONS)}', 'error')
        return redirect(url_for('index'))

    selected_language_option = request.form.get('language', 'en')

    # --- File Handling ---
    original_filename = secure_filename(file.filename)
    # Save with a unique name to avoid conflicts during processing
    temp_input_filename = f"input_{uuid.uuid4()}{os.path.splitext(original_filename)[1]}"
    original_input_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_input_filename)
    file.save(original_input_path)
    logger.info(f"Saved uploaded file temporarily as: {original_input_path}")

    converted_wav_path = None
    temp_wav_path_info = None # To track if conversion created a temp file

    try:
        # Convert uploaded file to WAV
        converted_wav_path, temp_wav_path_info = convert_to_wav(original_input_path)

        # Determine language code for TTS model
        # Special handling for 'hinglish' option
        if selected_language_option == 'hinglish':
            lang_code = 'en' # Use English mode for Roman script Hinglish with XTTS
            logger.info("Processing as Hinglish (using 'en' language code for Roman script).")
        elif selected_language_option == 'hi':
             lang_code = 'hi' # Use Hindi mode for Devanagari script
             logger.info("Processing as Hindi (using 'hi' language code).")
        else:
             lang_code = selected_language_option # Use selected code directly
             logger.info(f"Processing with language code: {lang_code}")


        # Generate unique output filename
        output_filename = f"output_{uuid.uuid4()}.wav"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # --- TTS Generation ---
        logger.info(f"Starting TTS generation for text: '{text[:50]}...'")
        start_time = datetime.now()

        if selected_language_option == 'hi' and len(text) > 200:
            logger.info("Long Hindi text detected. Processing in chunks...")
            # Split text into chunks
            text_chunks = split_hindi_text(text, max_chars=200)
            temp_audio_files = []
            
            try:
                # Process each chunk
                for i, chunk in enumerate(text_chunks):
                    temp_output = os.path.join(app.config['OUTPUT_FOLDER'], f"temp_chunk_{uuid.uuid4()}.wav")
                    logger.info(f"Processing chunk {i+1}/{len(text_chunks)}: {chunk[:30]}...")
                    model.tts_to_file(
                        text=chunk,
                        file_path=temp_output,
                        speaker_wav=converted_wav_path,
                        language=lang_code
                    )
                    temp_audio_files.append(temp_output)
                
                # Combine all chunks
                combine_audio_files(temp_audio_files, output_path)
            finally:
                # Clean up temporary chunk files
                for temp_file in temp_audio_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"Could not delete temporary chunk file {temp_file}: {e}")
        else:
            # Process normally for short text or non-Hindi languages
            model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=converted_wav_path,
                language=lang_code
            )
        
        end_time = datetime.now()
        logger.info(f"TTS generation successful. Output: {output_path}. Time: {end_time - start_time}")

        # Return JSON with file URL for preview and download
        return jsonify({
            'success': True,
            'message': 'Speech generated successfully.',
            'audio_url': url_for('download_file', filename=output_filename),
            'download_name': f"cloned_{selected_language_option}_{datetime.now():%Y%m%d_%H%M}.wav"
        })

    except ValueError as ve: # Catch specific conversion errors
        logger.error(f"Audio conversion failed: {ve}", exc_info=True)
        flash(f"Error processing audio file: {ve}", 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error during TTS generation: {e}", exc_info=True)
        flash(f"An error occurred during speech generation: {e}", 'error')
        return redirect(url_for('index'))

    finally:
        # --- Cleanup ---
        # Delete the original uploaded temp file
        if os.path.exists(original_input_path):
            try:
                os.remove(original_input_path)
                logger.info(f"Cleaned up temporary input file: {original_input_path}")
            except OSError as e:
                logger.warning(f"Could not delete temp input file {original_input_path}: {e}")

        # Delete the converted WAV file ONLY if it was temporary
        if temp_wav_path_info is not None and os.path.exists(temp_wav_path_info):
             try:
                 os.remove(temp_wav_path_info)
                 logger.info(f"Cleaned up temporary converted WAV file: {temp_wav_path_info}")
             except OSError as e:
                 logger.warning(f"Could not delete temp converted WAV file {temp_wav_path_info}: {e}")


@app.route('/api/clone_voice', methods=['POST'])
def api_clone_voice():
    """API endpoint for programmatic access."""
    # Check if model is available
    model = get_tts_model()
    if model is None or model_init_error:
        return jsonify({'error': f"TTS Model Error: {model_init_error or 'Not available'}"}), 503 # Service Unavailable

    # --- Request Validation ---
    if 'text' not in request.form or not request.form['text'].strip():
        return jsonify({'error': 'Missing required field: text'}), 400
    text = request.form['text'].strip()

    if 'voice_sample' not in request.files:
        return jsonify({'error': 'Missing required file: voice_sample'}), 400

    file = request.files['voice_sample']
    if file.filename == '':
        return jsonify({'error': 'Empty filename for voice_sample'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Use: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    selected_language_option = request.form.get('language', 'en') # Default to English

    # --- File Handling ---
    original_filename = secure_filename(file.filename)
    temp_input_filename = f"api_input_{uuid.uuid4()}{os.path.splitext(original_filename)[1]}"
    original_input_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_input_filename)
    file.save(original_input_path)
    logger.info(f"[API] Saved uploaded file temporarily as: {original_input_path}")

    converted_wav_path = None
    temp_wav_path_info = None

    try:
        # Convert to WAV
        converted_wav_path, temp_wav_path_info = convert_to_wav(original_input_path)

        # Determine language code
        if selected_language_option == 'hinglish':
            lang_code = 'en'
        elif selected_language_option == 'hi':
             lang_code = 'hi'
        elif selected_language_option in get_supported_languages(): # Check if valid code
             lang_code = selected_language_option
        else:
            logger.warning(f"[API] Invalid language '{selected_language_option}' received, defaulting to 'en'.")
            lang_code = 'en' # Default to English if invalid code provided

        logger.info(f"[API] Using language code: {lang_code}")

        # Generate output path
        output_filename = f"api_output_{uuid.uuid4()}.wav"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # --- TTS Generation ---
        logger.info(f"[API] Starting TTS generation for text: '{text[:50]}...'")
        if selected_language_option == 'hi' and len(text) > 200:
            logger.info("[API] Long Hindi text detected. Processing in chunks...")
            # Split text into chunks
            text_chunks = split_hindi_text(text, max_chars=200)
            temp_audio_files = []
            
            try:
                # Process each chunk
                for i, chunk in enumerate(text_chunks):
                    temp_output = os.path.join(app.config['OUTPUT_FOLDER'], f"temp_chunk_{uuid.uuid4()}.wav")
                    logger.info(f"[API] Processing chunk {i+1}/{len(text_chunks)}: {chunk[:30]}...")
                    model.tts_to_file(
                        text=chunk,
                        file_path=temp_output,
                        speaker_wav=converted_wav_path,
                        language=lang_code
                    )
                    temp_audio_files.append(temp_output)
                
                # Combine all chunks
                combine_audio_files(temp_audio_files, output_path)
            finally:
                # Clean up temporary chunk files
                for temp_file in temp_audio_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"[API] Could not delete temporary chunk file {temp_file}: {e}")
        else:
            # Process normally for short text or non-Hindi languages
            model.tts_to_file(
                text=text,
                file_path=output_path,
                speaker_wav=converted_wav_path,
                language=lang_code
            )
            
        logger.info(f"[API] TTS generation successful. Output: {output_path}")

        # Return success JSON with download URL
        download_url = url_for('download_file', filename=output_filename, _external=True)
        return jsonify({
            'success': True,
            'message': 'Speech generated successfully.',
            'output_filename': output_filename,
            'download_url': download_url
        })

    except ValueError as ve: # Catch specific conversion errors
        logger.error(f"[API] Audio conversion failed: {ve}", exc_info=True)
        return jsonify({'error': f'Audio processing failed: {ve}'}), 400
    except Exception as e:
        logger.error(f"[API] Error during TTS generation: {e}", exc_info=True)
        return jsonify({'error': f'Speech generation failed: {e}'}), 500

    finally:
        # --- Cleanup ---
        if os.path.exists(original_input_path):
            try: os.remove(original_input_path)
            except OSError as e: logger.warning(f"[API] Could not delete temp input file {original_input_path}: {e}")
        if temp_wav_path_info is not None and os.path.exists(temp_wav_path_info):
             try: os.remove(temp_wav_path_info)
             except OSError as e: logger.warning(f"[API] Could not delete temp converted WAV file {temp_wav_path_info}: {e}")


@app.route('/download/<filename>')
def download_file(filename):
    """Endpoint to download generated files safely."""
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    # Basic security check: ensure the file is within the output folder
    if not os.path.normpath(file_path).startswith(os.path.normpath(app.config['OUTPUT_FOLDER'])):
        logger.warning(f"Attempt to download file outside designated folder: {filename}")
        return "Forbidden", 403
    if not os.path.exists(file_path):
        logger.warning(f"Download request for non-existent file: {filename}")
        return "File not found", 404
    return send_file(
        file_path,
        mimetype="audio/wav",
        as_attachment=True,
        download_name=filename # Keep original generated name for download
    )

@app.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_status = "ok" if tts_model_instance else "loading_or_error"
    if model_init_error:
        model_status = f"error: {model_init_error}"
    return jsonify({'status': 'ok', 'tts_model_status': model_status, 'device': device})

@app.route('/model_info', methods=['GET'])
def get_model_info():
    """Return information about the loaded TTS model."""
    model = get_tts_model()
    if model is None:
         return jsonify({'error': model_init_error or "Model not loaded yet"}), 503

    model_info = {
        'model_name': getattr(model, 'model_name', 'N/A'),
        'languages': getattr(model, 'languages', []),
        'is_multi_lingual': getattr(model, 'is_multi_lingual', False),
        'speakers': getattr(model, 'speakers', []) # Might be empty for XTTS
    }
    return jsonify({'tts_model': model_info})


# --- Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 Not Found: {request.path}")
    return render_template('404.html'), 404 # Optional: Create a 404 template

@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning(f"File upload rejected: Too large (>{MAX_FILE_SIZE_MB}MB)")
    # For API requests
    if request.path.startswith('/api/'):
        return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.'}), 413
    # For web form requests
    flash(f'File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Internal Server Error: {e}", exc_info=True)
    # For API requests
    if request.path.startswith('/api/'):
        return jsonify({'error': 'An internal server error occurred.'}), 500
    # For web form requests
    flash('An unexpected internal server error occurred. Please try again later.', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("--- Starting Voice Cloning Service (XTTS v2) ---")
    get_tts_model() # Attempt to load model at startup
    app.run(host='0.0.0.0', port=5000, debug=False) # Disable debug for production/testing stability
    # Use debug=True only for active development