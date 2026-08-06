import os
import time
import cv2
import json
import threading
import numpy as np
from PIL import Image
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from detection import detect
from notifier import send_sms  

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def print_msg(a,b):
    print(f"SMS triggered")


def generate_frames(filename: str, camera_id: str, camera_location: str):
    video_path = os.path.join("uploaded_videos", filename)
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_delay = 1.0 / fps
    frames_per_interval = max(1, int(fps * 0.2)) 

    frame_count = 0
    max_prob_so_far = 0.0  
    
     
    sms_sent = False 

    target_w, target_h = 640, 360

    while cap.isOpened():
        start_time = time.time()
        ret, frame = cap.read()
        
        if not ret:
             
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_count = 0
            max_prob_so_far = 0.0  
            continue

        frame_count += 1

        if frame_count % frames_per_interval == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)

            probs = detect([pil_img])
            print(probs)
            
            crash_prob = probs[0] if probs.ndim == 1 else probs[0][0]
            current_prob_percent = crash_prob * 100.0

            no_crash_prob = probs[1] if probs.ndim == 1 else probs[0][1]
            no_crash_prob_percent = no_crash_prob * 100

            fire_prob = probs[3] if probs.ndim ==1 else probs[0][3]
            fire_prob_percent = fire_prob * 100.0

            if current_prob_percent > max_prob_so_far:
                max_prob_so_far = current_prob_percent

             
            if max_prob_so_far > 75.0 and not sms_sent:
                sms_sent = True  
                
                message = f"🚨 URGENT: Accident detected at {camera_location} (Camera ID: {camera_id}). Immediate assistance required!"
                target_number = "8618011899"  
                
                 
                threading.Thread(target=print_msg, args=(target_number, message)).start()
                print(f"SMS triggered for {camera_id} at {camera_location} to ambulance")
                if fire_prob_percent>75.0:
                    message = f"URGENT: Fire invloved in accident detected at {camera_location} (Camera ID: {camera_id}). Immediate assistance required!"
                    target_number = "7892632753"
                    threading.Thread(target=print_msg, args=(target_number,message)).start()
                    print(f"SMS triggered for fire emergency")


         
        h, w = frame.shape[:2]
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        resized_frame = cv2.resize(frame, (new_w, new_h))
        display_frame = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        
        display_frame[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_frame

         
        if max_prob_so_far > 75.0:
            text = f"ACCIDENT DETECTED! ({max_prob_so_far:.1f}%)"
            color = (0, 0, 255)
        elif max_prob_so_far > 0:
            text = f"Max Prob: {max_prob_so_far:.1f}%"
            color = (0, 255, 0)
        else:
            text = "Analyzing..."
            color = (255, 255, 255)

        cv2.putText(display_frame, text, (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

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

if __name__ == "__main__":
    import uvicorn
    os.makedirs("uploaded_videos", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
