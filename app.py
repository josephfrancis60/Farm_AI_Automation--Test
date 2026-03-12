from ui.chat_interface import start_ui
from scheduler.farm_scheduler import start_scheduler
import os

if __name__ == "__main__":
    # Ensure necessary directories exist
    for folder in ["alerts", "agent_logs"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        
    # Start Background Scheduler
    start_scheduler()

    # Launch Streamlit UI
    start_ui()