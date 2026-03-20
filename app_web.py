from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import os
import json
from datetime import datetime
from agents.run_agent import run_agent
from alerts.alert_manager import get_active_alerts, remove_alert, clear_alerts
from scheduler.farm_scheduler import start_scheduler
from alerts.reminder_manager import get_active_reminders, add_reminder, remove_reminder, clear_reminders

from contextlib import asynccontextmanager
from services.logger_service import log_agent_action

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log_agent_action("=== Agent Backend Server Started ===")
    app.state.scheduler = start_scheduler()
    yield
    # Shutdown
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown()
    log_agent_action("=== Agent Backend Server Shutdown ===")

app = FastAPI(lifespan=lifespan)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ReminderRequest(BaseModel):
    title: str
    message: str

@app.get("/health")
def health():
    return {"status": "online"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        reply = run_agent(request.message)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
def alerts():
    # Reuse filtering logic from the Tkinter UI
    all_alerts = get_active_alerts()
    today_str = datetime.now().strftime("%Y-%m-%d")
    filtered = []
    for a in all_alerts:
        ts = a.get("timestamp", "")
        if ts.startswith(today_str):
            filtered.append(a)
        else:
            title = a.get("title", "").lower()
            if "catch-up" not in title and "downtime" not in title:
                filtered.append(a)
    return filtered[:20]

@app.delete("/alerts/{alert_id}")
def delete_alert(alert_id: str):
    success = remove_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "success"}

@app.delete("/alerts")
def delete_all_alerts():
    clear_alerts()
    return {"status": "success"}

@app.get("/reminders")
def reminders():
    return get_active_reminders()

@app.post("/reminders")
def create_reminder(request: ReminderRequest):
    reminder = add_reminder(request.title, request.message)
    return reminder

@app.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: str):
    success = remove_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success"}

@app.delete("/reminders")
def delete_all_reminders():
    clear_reminders()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
