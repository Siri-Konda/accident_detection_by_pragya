from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
import json

app = FastAPI()

UPLOAD_DIR = "uploaded_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    camera_id: str = Form(...),
    camera_location: str = Form(...)
):
    if not video.filename:
        raise HTTPException(status_code=400, detail="No video file provided.")


    os.makedirs(UPLOAD_DIR, exist_ok=True)


    _, ext = os.path.splitext(video.filename)
    

    new_video_filename = f"{camera_id}{ext}"
    video_path = os.path.join(UPLOAD_DIR, new_video_filename)


    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)


    metadata = {
        "camera_id": camera_id,
        "camera_location": camera_location,
        "original_filename": video.filename,
        "video_filename": new_video_filename
    }


    json_path = os.path.join(UPLOAD_DIR, f"{camera_id}.json")
    
    with open(json_path, "w") as json_file:
        json.dump(metadata, json_file, indent=4)

    return JSONResponse({
        "message": "Upload successful",
        "metadata": metadata
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
