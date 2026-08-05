import os
import time
import cv2
from PIL import Image

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates


from detection import detect

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def generate_frames(filename: str):
    video_path = os.path.join("uploaded_videos", filename)
    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_delay = 1.0 / fps
    
    # Calculate how many frames make up 0.2 seconds
    frames_per_interval = max(1, int(fps * 0.2)) 

    frame_count = 0
    max_prob_so_far = 0.0  

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
            
            crash_prob = probs[0] if probs.ndim == 1 else probs[0][0]
            current_prob_percent = crash_prob * 100.0

            if current_prob_percent > max_prob_so_far:
                max_prob_so_far = current_prob_percent


        if max_prob_so_far > 75.0:
            text = f"ACCIDENT DETECTED! ({max_prob_so_far:.1f}%)"
            color = (0, 0, 255)
        elif max_prob_so_far > 0:
            text = f"Max Prob: {max_prob_so_far:.1f}%"
            color = (0, 255, 0)
        else:
            text = "Analyzing..."
            color = (255, 255, 255)

        cv2.putText(frame, text, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', frame)
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
    videos = []
    if os.path.exists(videos_dir):
        videos = [f for f in os.listdir(videos_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "videos": sorted(videos)}
    )

@app.get("/video_feed/{filename}")
async def video_feed(filename: str):
    return StreamingResponse(
        generate_frames(filename),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    import uvicorn
    os.makedirs("uploaded_videos", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
