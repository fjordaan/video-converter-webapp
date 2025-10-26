
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
from pathlib import Path
import subprocess
import json

UPLOAD_DIR = Path("./uploads")
OUTPUT_DIR = Path("./outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Video Converter")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR.resolve())), name="outputs")

def run_ffmpeg_convert(input_path: Path, output_path: Path) -> None:
    try:
        cmd_probe = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", 
                     "stream=r_frame_rate", "-of", "json", str(input_path)]
        result = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
        fps_info = json.loads(result.stdout)
        r_frame_rate = fps_info['streams'][0]['r_frame_rate']
        num, denom = map(int, r_frame_rate.split('/'))
        framerate = num / denom
    except Exception:
        framerate = None

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-vf", "format=yuv420p",
    ]
    if framerate:
        cmd += ["-r", str(framerate)]
    cmd += [
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    uid = uuid.uuid4().hex
    local_in = UPLOAD_DIR / f"{uid}_{file.filename}"

    with local_in.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    out_name = f"{Path(file.filename).stem}_{uid}.mp4"
    local_out = OUTPUT_DIR / out_name

    try:
        run_ffmpeg_convert(local_in, local_out)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")

    download_url = f"/outputs/{out_name}"
    return JSONResponse({"status": "done", "download_url": download_url})

@app.get("/health")
async def health():
    return {"ok": True}
