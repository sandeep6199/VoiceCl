# 🎤 VoxLite: Build Your AI Voice Cloning System (Step-by-Step)

Welcome to the **VoxLite Project**! This guide is designed for students to build a professional-grade AI Voice Cloning application using Python, Flask, and the advanced **Coqui XTTS v2** model.

---

## 🏗️ Project Overview
VoxLite allows you to upload a short 10-second audio clip of any person and then generate new speech that sounds exactly like them in multiple languages.

### 🛠️ Prerequisites (System Setup)
Before starting, ensure your PC is ready:
1.  **Python 3.10**: Best for AI libraries.
2.  **FFmpeg**: [Download](https://www.gyan.dev/ffmpeg/builds/) and add to your System PATH.
3.  **C++ Build Tools**: Install "Desktop development with C++" via Visual Studio Installer.

**Install Required Libraries:**
```bash
pip install flask flask-sqlalchemy flask-bcrypt pydub TTS torch==2.1.2 transformers==4.33.0
```

---

## 📂 Module 1: The Project Skeleton
**Goal:** Create the folder structure and a basic Flask server.

1. Create a folder named `VoxLite`.
2. Inside it, create these folders: `static`, `templates`, `uploads`, `outputs`.
3. Create `app.py` and write this code:

```python
from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = "secret_key_123"

@app.route('/')
def index():
    return "<h1>Module 1: Server is Live!</h1>"

if __name__ == '__main__':
    app.run(debug=True)
```
**Test:** Run `python app.py` and visit `http://127.0.0.1:5000`.

---

## 🔐 Module 2: User Authentication & DB
**Goal:** Secure the app with a login system.

Update your `app.py`:
- Add `Flask-SQLAlchemy` for the database.
- Add `Flask-Bcrypt` for password encryption.

```python
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

with app.app_context():
    db.create_all()
# Note: Add Register/Login routes here
```

---

## 🎨 Module 3: The Cloning UI
**Goal:** Create the user interface for uploading voices.

Create `templates/voice_clone.html`:
- Use HTML5 for the form.
- Use JavaScript (Fetch API) to send data to the server without refreshing the page.

*(Refer to the full `voice_clone.html` code provided in our session for the premium design!)*

---

## 🧠 Module 4: The AI "Brain" (XTTS v2)
**Goal:** Integrate the Voice Cloning AI.

In `app.py`, we add the logic to process audio:

```python
import torch
from TTS.api import TTS

# This loads the 2.2GB AI model into memory
# It might take 5-10 minutes the first time!
def get_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

@app.route('/clone_voice', methods=['POST'])
def clone_voice():
    # 1. Get Text & Voice File from user
    # 2. Save file temporarily in /uploads
    # 3. Use model.tts_to_file() to create clone
    # 4. Save result in /outputs
    # 5. Send result back to Frontend
    return {"success": True, "audio_url": "/path/to/result.wav"}
```

---

## 🚀 How to Run the Final Project
1.  Open your terminal in the `VoxLite` folder.
2.  Run `python app.py`.
3.  **Wait** for the model to download (only happens once).
4.  Open `http://127.0.0.1:5000/voice_clone`.
5.  Upload a clear **WAV** file (10 seconds), type some text, and click **Generate**.

---

## 💡 Learning Outcomes for Students
- **Backend:** How Flask handles file uploads and API requests.
- **Frontend:** Building interactive Dashboards with Tailwind/CSS.
- **AI/ML:** Understanding how zero-shot voice cloning (XTTS) works.
- **Data:** Practical usage of SQLite and encryption.

---
© 2025 VoxLite Education Series
