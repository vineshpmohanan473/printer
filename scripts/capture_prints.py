#!/usr/bin/env python3
import os
import time
from datetime import datetime
import threading
import queue

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

def main():
    """Main logic to handle timeouts and save the buffer."""
    buffer = bytearray()
    last_data_time = None

    def save_buffer():
        nonlocal last_data_time
        if buffer:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{OUTPUT_DIR}/print_{timestamp}.bin"
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
            # Get data from the queue, with a timeout.
            data = data_queue.get(timeout=1.0)

            if data is None: # Sentinel value means thread is done
                print("[INFO] Reader thread has finished.")
                if buffer: save_buffer()
                break # Exit main loop

            # We got data, so extend the buffer and update the timestamp.
            if not last_data_time:
                print("[INFO] Print job started.")
            buffer.extend(data)
            last_data_time = time.time()
            print(f"[INFO] Read {len(data)} bytes, buffer size: {len(buffer)}")

        except queue.Empty:
            # This is our main timeout mechanism. No data was in the queue.
            if last_data_time and (time.time() - last_data_time > JOB_COMPLETION_TIMEOUT):
                print(f"[INFO] Job completion timeout ({JOB_COMPLETION_TIMEOUT}s) reached.")
                save_buffer()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping capture by user.")
