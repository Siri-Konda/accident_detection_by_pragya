import os
import time
import cv2
import json
import threading
import numpy as np
from datetime import datetime

from PIL import Image
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from clip_utils.detection import detect
from sms.test import send_email  

app = FastAPI()

templates = Jinja2Templates(directory="../frontend/dashboard")

def trigger_email_alert(recipient_email: str, subject: str, message_body: str, image_bytes: bytes = None):
    """Wrapper to run send_email asynchronously with an image attachment."""
    send_email(recipient_email, subject, message_body, image_bytes=image_bytes)

def print_msg(a,b):
    print(f"SMS triggered")

MAX_BLANK_DURATION = 250

LOG_FILE = "event_logs.json"
log_lock = threading.Lock()

def append_log(camera_id: str, location: str, event_type: str, details: str):
    """Thread-safe function to append an event to the JSON log file."""
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "camera_id": camera_id,
        "location": location,
        "event_type": event_type,
        "details": details
    }
    
    with log_lock:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        logs.insert(0, log_entry)
        
        logs = logs[:100]
        
        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=4)


def generate_frames(filename: str, camera_id: str, camera_location: str):
    video_path = os.path.join("uploaded_videos", filename)
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_delay = 1.0 / fps
    frames_per_interval = max(1, int(fps * 0.1)) 

    frame_count = 0
    max_prob_so_far = 0.0  
    current_prob_percent = 0.0 # Track this outside the interval loop for the text display
    MAX_DIFFERENCE = 300
    previous_working_frame = 0
     
    sms_sent = False 
    fire_sent = False
    blank_sent = False

    # --- NEW VARIABLES FOR CONSECUTIVE CHECK ---
    accident_consecutive_count = 0
    REQUIRED_ACCIDENT_FRAMES = 2
    accident_confirmed = False
    # -------------------------------------------

    target_w, target_h = 640, 360

    while cap.isOpened():
        start_time = time.time()
        ret, frame = cap.read()
        
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_count = 0
            max_prob_so_far = 0.0  
            accident_consecutive_count = 0 # Reset on loop
            continue

        frame_count += 1

        if frame_count % frames_per_interval == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            probs = detect([pil_img])
            
            crash_prob = probs[0] if probs.ndim == 1 else probs[0][0]
            current_prob_percent = crash_prob * 100.0

            fire_prob = probs[3] if probs.ndim == 1 else probs[0][3]
            fire_prob_percent = fire_prob * 100.0

            blank_prob = probs[2] if probs.ndim == 1 else probs[0][2]
            blank_prob_percent = blank_prob * 100.0

            if current_prob_percent > max_prob_so_far:
                max_prob_so_far = current_prob_percent

            if current_prob_percent > 65:
                accident_consecutive_count += 1
            else:
                accident_consecutive_count = 0 # Reset counter if prob drops below 80%

            if accident_consecutive_count >= REQUIRED_ACCIDENT_FRAMES and not sms_sent:
                accident_confirmed = True
                subject = f"URGENT: Accident Detected at {camera_location}"
                message = f"URGENT: Accident detected at {camera_location} (Camera ID: {camera_id}). Immediate assistance required!"
                target_email = "sinchumail24@gmail.com"
                
                # Convert current frame to JPEG bytes for email attachment
                _, frame_img_buffer = cv2.imencode('.jpg', frame)
                image_bytes = frame_img_buffer.tobytes()

                threading.Thread(
                    target=trigger_email_alert, 
                    args=(target_email, subject, message, image_bytes)
                ).start()
                
                print(f"Email with snapshot triggered for {camera_id} at {camera_location} to ambulance services")
                append_log(camera_id, camera_location, "ACCIDENT", f"Accident detected with {current_prob_percent:.1f}% confidence")
                
            if fire_prob_percent > 45 and not fire_sent:
                fire_sent = True
                message = f"URGENT: Fire invloved in accident detected at {camera_location} (Camera ID: {camera_id}). Immediate assistance required!"
                target_number = "7892632753"
                threading.Thread(target=print_msg, args=(target_number,message)).start()
                print(f"SMS triggered for fire emergency")
                append_log(camera_id, camera_location, "FIRE", f"Fire detected with {fire_prob_percent:.1f}% confidence")
                
            if blank_prob_percent > 50.0:
                if frame_count - previous_working_frame > MAX_BLANK_DURATION and not blank_sent: 
                    blank_sent = True
                    print(f"{camera_id} at {camera_location} may not be working")
                    append_log(camera_id, camera_location, "OFFLINE", "Camera feed went blank")
            else: 
                previous_working_frame = frame_count
         
        h, w = frame.shape[:2]
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized_frame = cv2.resize(frame, (new_w, new_h))
        display_frame = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        
        display_frame[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_frame

        # --- MODIFIED DISPLAY LOGIC ---
        if frame_count - previous_working_frame > MAX_BLANK_DURATION:
            text = "Video footage is blank"
            color = (0, 0, 255)
        elif accident_confirmed:
            text = f"ACCIDENT DETECTED! ({current_prob_percent:.1f}%)"
            color = (0, 0, 255)
        elif max_prob_so_far > 0:  # We just use this to know if initial frame has processed
            # Display current probability and consecutive count if warning
            if accident_consecutive_count > 0:
                text = f"Detecting... ({accident_consecutive_count}/{REQUIRED_ACCIDENT_FRAMES}) [{current_prob_percent:.1f}%]"
                color = (0, 165, 255) # Orange for warning
            else:
                text = f"Prob: {current_prob_percent:.1f}%"
                color = (0, 255, 0)
        else:
            text = "Analyzing..."
            color = (255, 255, 255)
        # ------------------------------

        cv2.putText(display_frame, text, (15, 35),
                    cv2.FONT_HERSHEY_COMPLEX, 0.8, color, 2, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', display_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        elapsed = time.time() - start_time
        if elapsed < frame_delay:
            time.sleep(frame_delay - elapsed)

    cap.release()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    videos_dir = "uploaded_videos"
    videos_data = []
    
    if os.path.exists(videos_dir):
        video_files = [f for f in os.listdir(videos_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
        
        for v_file in video_files:
            base_name = os.path.splitext(v_file)[0]
            json_path = os.path.join(videos_dir, f"{base_name}.json")
            
            video_info = {
                "video_filename": v_file,
                "camera_id": "Unknown",
                "camera_location": "Unknown Location"
            }
            
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    video_info.update(data)
            
            videos_data.append(video_info)
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "videos": videos_data}
    )

@app.get("/video_feed/{filename}")
async def video_feed(filename: str):
    base_name = os.path.splitext(filename)[0]
    json_path = os.path.join("uploaded_videos", f"{base_name}.json")
    
    camera_id = "Unknown"
    camera_location = "Unknown Location"
    
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            camera_id = data.get("camera_id", camera_id)
            camera_location = data.get("camera_location", camera_location)

    return StreamingResponse(
        generate_frames(filename, camera_id, camera_location),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/logs")
async def get_logs():

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

if __name__ == "__main__":
    import uvicorn
    os.makedirs("uploaded_videos", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
            
    uvicorn.run(app, host="0.0.0.0", port=8000)