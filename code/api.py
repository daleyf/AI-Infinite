from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DASHBOARD_PATH = Path(__file__).parent / "dashboard_state.json"

@app.get("/iterations/meta")
def get_meta():
    if not DASHBOARD_PATH.exists():
        raise HTTPException(status_code=404, detail="Dashboard file not found")
    try:
        data = json.loads(DASHBOARD_PATH.read_text())
        return {"total_pages": len(data.get("all_outputs", []))}
    except Exception:
        raise HTTPException(status_code=500, detail="Could not read dashboard state")

@app.get("/iteration/{iteration_id}")
def get_iteration(iteration_id: int):
    if not DASHBOARD_PATH.exists():
        raise HTTPException(status_code=404, detail="Dashboard file not found")
    try:
        data = json.loads(DASHBOARD_PATH.read_text())
        all_outputs = data.get("all_outputs", [])
        if iteration_id < 1 or iteration_id > len(all_outputs):
            raise HTTPException(status_code=400, detail="Invalid iteration ID")
        return all_outputs[iteration_id - 1]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
