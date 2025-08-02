import threading
import time
import subprocess
import os
from flask import Flask

app = Flask(__name__)

# Health check route (required by Render)
@app.route('/health')
def health():
    return "OK", 200

# Start Streamlit in a background thread
def run_streamlit():
    time.sleep(5)  # Wait a bit for Flask to start
    cmd = [
        "streamlit", "run", "main.py",
        "--server.port=8080",
        "--server.address=0.0.0.0",
        "--browser.gatherUsageStats=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]
    subprocess.run(cmd)

# Optional: redirect root to Streamlit
@app.route("/")
def home():
    return "<h3>Starting Streamlit app...</h3><p>Go to <a href='/streamlit'>/streamlit</a></p>"

if __name__ == '__main__':
    # Start the Streamlit thread before Flask runs
    thread = threading.Thread(target=run_streamlit, daemon=True)
    thread.start()

    app.run(port=int(os.environ.get("PORT", 8080)))
