import os
import json
from datetime import datetime, timezone

REMINDERS_FILE = "alerts/active_reminders.json"

def add_reminder(title, message, due_time=None):
    """Adds a new reminder to the system."""
    now_utc = datetime.now(timezone.utc)
    reminder = {
        "id": now_utc.strftime("%Y%m%d%H%M%S%f"),
        "timestamp": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "due_time": due_time or now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": title,
        "message": message,
        "is_read": False
    }

    reminders = []
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, "r") as f:
                reminders = json.load(f)
        except:
            reminders = []

    reminders.insert(0, reminder)
    reminders = reminders[:20]

    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=4)

    return reminder

def get_active_reminders():
    """Returns all active reminders."""
    if not os.path.exists(REMINDERS_FILE):
        return []
    
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def clear_reminders():
    """Clears all reminders."""
    if os.path.exists(REMINDERS_FILE):
        os.remove(REMINDERS_FILE)

def remove_reminder(reminder_id):
    """Removes a specific reminder by its ID."""
    if not os.path.exists(REMINDERS_FILE):
        return False
    
    try:
        with open(REMINDERS_FILE, "r") as f:
            reminders = json.load(f)
        
        new_reminders = [r for r in reminders if r["id"] != reminder_id]
        
        if len(new_reminders) < len(reminders):
            with open(REMINDERS_FILE, "w") as f:
                json.dump(new_reminders, f, indent=4)
            return True
    except:
        pass
    return False
