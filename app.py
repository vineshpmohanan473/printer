from flask import Flask, jsonify, send_from_directory
import os
import time
from datetime import datetime
import threading
import queue
import subprocess
import shutil
from flasgger import Swagger

# --- Flask App Setup ---
app = Flask(__name__)
Swagger(app)

# --- Directory and Device Configuration ---
TXT_DIR = "/home/rasp/printer/txt"
PRINTER_DEVICE = "/dev/g_printer0"
PRINTS_DIR = "/home/rasp/printer/prints"
CHUNK_SIZE = 4096
JOB_COMPLETION_TIMEOUT = 3.0  # seconds

os.makedirs(PRINTS_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)

# --- Print Capture Logic (from capture_prints.py) ---
data_queue = queue.Queue()

def reader_thread(dev_path, q):
    """This function runs in a background thread and reads from the device."""
    print("[INFO] Reader thread started.")
    try:
        with open(dev_path, 'rb') as dev:
            while True:
                data = dev.read(CHUNK_SIZE)
                if not data:
                    print("[INFO] Reader thread received 0 bytes, exiting.")
                    break
                q.put(data)
    except Exception as e:
        print(f"[ERROR] Reader thread encountered an error: {e}")
    finally:
        q.put(None) # Signal that the reader is done.

def capture_prints_job():
    """Main logic to handle timeouts and save the buffer."""
    buffer = bytearray()
    last_data_time = None

    def save_buffer():
        nonlocal last_data_time
        if buffer:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{PRINTS_DIR}/print_{timestamp}.bin"
            with open(filename, "wb") as f:
                f.write(buffer)
            print(f"[INFO] Print job saved: {filename} ({len(buffer)} bytes)")
            buffer.clear()
        last_data_time = None
        print("\n[INFO] Ready for next print job...")

    # Start the reader thread
    thread = threading.Thread(target=reader_thread, args=(PRINTER_DEVICE, data_queue), daemon=True)
    thread.start()

    print("[INFO] Starting print capture...")
    print("[INFO] Ready for next print job...")

    while True:
        try:
            data = data_queue.get(timeout=1.0)
            if data is None: # Sentinel value means thread is done
                print("[INFO] Reader thread has finished.")
                if buffer: save_buffer()
                break # Exit main loop

            if not last_data_time:
                print("[INFO] Print job started.")
            buffer.extend(data)
            last_data_time = time.time()

        except queue.Empty:
            if last_data_time and (time.time() - last_data_time > JOB_COMPLETION_TIMEOUT):
                print(f"[INFO] Job completion timeout ({JOB_COMPLETION_TIMEOUT}s) reached.")
                save_buffer()

# --- Flask API Endpoints ---
@app.route('/files', methods=['GET'])
def list_files():
    """List all available TXT files.
    ---
    responses:
      200:
        description: A list of TXT files with their sizes.
        schema:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              size:
                type: integer
    """
    if not os.path.exists(TXT_DIR):
        return jsonify({"error": "TXT directory not found"}), 404
    try:
        files_with_sizes = []
        for f in os.listdir(TXT_DIR):
            if f.endswith('.txt'):
                file_path = os.path.join(TXT_DIR, f)
                size = os.path.getsize(file_path)
                files_with_sizes.append({"name": f, "size": size})
        return jsonify(files_with_sizes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>', methods=['GET'])
def download_file(filename):
    """Download a specific TXT file.
    ---
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: The name of the TXT file to download.
    responses:
      200:
        description: The requested TXT file.
      404:
        description: File not found.
    """
    return send_from_directory(TXT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    # Start the print capture job in a background thread
    print("[INFO] Starting background print capture thread.")
    capture_thread = threading.Thread(target=capture_prints_job, daemon=True)
    capture_thread.start()
    
    # Start the Flask server
    # Note: Disabling debug mode is recommended for stability when using threads.
    # The reloader can cause issues with background threads.
    app.run(host='0.0.0.0', port=5000, debug=False)
