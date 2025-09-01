#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
import threading
import queue
import subprocess
from pathlib import Path

PRINTER_DEVICE = "/dev/g_printer0"
OUTPUT_DIR = "/home/rasp/printer/prints"
CHUNK_SIZE = 4096
# How long to wait for new data before considering the job finished.
JOB_COMPLETION_TIMEOUT = 3.0  # seconds

os.makedirs(OUTPUT_DIR, exist_ok=True)

# A queue to safely pass data from the reader thread to the main thread
data_queue = queue.Queue()

def reader_thread(dev_path, q):
    """This function runs in a background thread and reads from the device."""
    print("[INFO] Reader thread started.")
    try:
        with open(dev_path, 'rb') as dev:
            while True:
                data = dev.read(CHUNK_SIZE)
                if not data:
                    # This might indicate the host closed the connection.
                    print("[INFO] Reader thread received 0 bytes, exiting.")
                    break
                q.put(data)
    except Exception as e:
        print(f"[ERROR] Reader thread encountered an error: {e}")
    finally:
        # Signal that the reader is done.
        q.put(None)

def save_buffer(buffer):
    """Save the buffer to a file and process it."""
    if not buffer:
        print("[DEBUG] Empty buffer, nothing to save")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(OUTPUT_DIR, f"print_{timestamp}.bin")
    
    try:
        # Save the raw buffer to file
        print(f"[DEBUG] Saving buffer to {filename}")
        with open(filename, "wb") as f:
            f.write(buffer)
        print(f"[INFO] Print job saved: {filename} ({len(buffer)} bytes)")
        
        # Call extract_string.py to process the file
        extract_script = Path(__file__).parent.absolute() / 'extract_string.py'
        if not extract_script.exists():
            print(f"[ERROR] extract_string.py not found at {extract_script}")
            return
            
        # Print current working directory and script path for debugging
        print(f"[DEBUG] Current working directory: {os.getcwd()}")
        print(f"[DEBUG] Using extract script: {extract_script}")
        
        # Build absolute path to the binary file
        abs_filename = os.path.abspath(filename)
        print(f"[DEBUG] Processing file: {abs_filename}")
        
        # Run the script with full paths
        cmd = [sys.executable, str(extract_script), abs_filename]
        print(f"[DEBUG] Executing: {' '.join(cmd)}")
        
        # Run with Popen to capture all output in real-time
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream the output in real-time
            print("\n=== EXTRACTION STARTED ===")
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # Get any remaining output after process ends
            stdout, stderr = process.communicate()
            
            if stdout:
                print("\n=== EXTRACTED CONTENT ===")
                print(stdout.strip())
                print("=========================\n")
                
            if stderr:
                print("\n=== ERRORS ===")
                print(stderr.strip())
                print("==============\n")
                
            if process.returncode != 0:
                print(f"[ERROR] Script failed with return code {process.returncode}")
            
        except Exception as e:
            print(f"[ERROR] Failed to execute extract_string.py: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"[ERROR] Error processing print job: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Verify the file was created and has content
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"[DEBUG] File {filename} exists, size: {size} bytes")
        else:
            print(f"[ERROR] File {filename} was not created")

def main():
    """Main logic to handle timeouts and save the buffer."""
    buffer = bytearray()
    last_data_time = None
    
    # Start the reader thread
    thread = threading.Thread(target=reader_thread, args=(PRINTER_DEVICE, data_queue), daemon=True)
    thread.start()

    print("[INFO] Starting print capture...")
    print("[INFO] Ready for next print job...")

    while True:
        try:
            # Get data from the queue, with a timeout.
            data = data_queue.get(timeout=1.0)

            if data is None:  # Sentinel value means thread is done
                print("[INFO] Reader thread has finished.")
                if buffer:
                    save_buffer(buffer)
                break
                
            # We got data, so extend the buffer and update the timestamp
            if not last_data_time:
                print("[INFO] Print job started.")
            buffer.extend(data)
            last_data_time = time.time()
            print(f"[INFO] Read {len(data)} bytes, buffer size: {len(buffer)}")
            
        except queue.Empty:
            # Check for job completion timeout
            if buffer and last_data_time and (time.time() - last_data_time > JOB_COMPLETION_TIMEOUT):
                print("\n[INFO] Job completion timeout reached.")
                save_buffer(buffer)
                buffer = bytearray()
                last_data_time = None
                print("\n[INFO] Ready for next print job...")
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
            if buffer:
                save_buffer(buffer)
            break
            
        except Exception as e:
            print(f"[ERROR] Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)  # Prevent tight loop on error

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping capture by user.")
