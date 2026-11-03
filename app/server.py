"""FastAPI inference server + drawing UI.

    S2I_CHECKPOINT=runs/pix2pix/checkpoints/best.pt uvicorn app.server:app --port 8000
Then open http://localhost:8000
"""
import io
import os
import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image

from s2i.inference import SketchToImage

ROOT = Path(__file__).resolve().parent
CHECKPOINT = os.environ.get("S2I_CHECKPOINT", "runs/pix2pix/checkpoints/best.pt")

app = FastAPI(title="Sketch-to-Image Generator")
model = SketchToImage(CHECKPOINT) if Path(CHECKPOINT).exists() else None


@app.get("/api/health")
def health():
    return {
        "model_loaded": model is not None,
        "checkpoint": CHECKPOINT,
        "device": str(model.device) if model else None,
        "epoch": model.epoch + 1 if model and model.epoch is not None else None,
        "image_size": model.image_size if model else None,
    }


@app.post("/api/generate")
async def generate(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(503, f"No checkpoint at {CHECKPOINT}. Train first or set S2I_CHECKPOINT.")
    try:
        sketch = Image.open(io.BytesIO(await file.read()))
    except Exception:
        raise HTTPException(400, "could not decode image")
    t0 = time.perf_counter()
    out = model(sketch)
    ms = (time.perf_counter() - t0) * 1000
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png", headers={"X-Inference-Ms": f"{ms:.1f}"})


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
