import os
import json
from datetime import datetime, timezone

ALERTS_FILE = "alerts/active_alerts.json"

def add_alert(title, message, category="INFO"):
    """
    Adds a new alert to the system.
    Categories: INFO, WARNING, SUCCESS, ERROR
    """
    now_utc = datetime.now(timezone.utc)
    alert = {
        "id": now_utc.strftime("%Y%m%d%H%M%S%f"),
        "timestamp": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": title,
        "message": message,
        "category": category,
        "is_read": False
    }

    # Print to console for instant feedback
    print(f"\n[ALERT - {category}] {title}: {message}")

    # Save to JSON for Streamlit UI
    alerts = []
    if os.path.exists(ALERTS_FILE):
        try:
            with open(ALERTS_FILE, "r") as f:
                alerts = json.load(f)
        except:
            alerts = []

    # Deduplication logic for "System Catch-up"
    if "System Catch-up" in title:
        alerts = [a for a in alerts if "System Catch-up" not in a.get("title", "")]

    # Keep only the last 50 alerts
    alerts.insert(0, alert)
    alerts = alerts[:50]

    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=4)

    return alert

def get_active_alerts():
    """Returns all active alerts."""
    if not os.path.exists(ALERTS_FILE):
        return []
    
    try:
        with open(ALERTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def clear_alerts():
    """Clears all alerts."""
    if os.path.exists(ALERTS_FILE):
        try:
            os.remove(ALERTS_FILE)
            return True
        except:
            return False
    return True

def remove_alert(alert_id):
    """Removes a specific alert by its ID."""
    if not os.path.exists(ALERTS_FILE):
        return False
    
    try:
        with open(ALERTS_FILE, "r") as f:
            alerts = json.load(f)
        
        new_alerts = [a for a in alerts if a["id"] != alert_id]
        
        if len(new_alerts) < len(alerts):
            with open(ALERTS_FILE, "w") as f:
                json.dump(new_alerts, f, indent=4)
            return True
    except:
        pass
    return False
