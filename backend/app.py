import sys
import os

# Add the project root and frontend to sys.path to find ui modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")))

from ui.chat_interface import start_ui          # Streamlit UI (original)
from ui.chat_interface_2 import start_ui_jarvis  # JARVIS CustomTkinter UI (new)
from scheduler.farm_scheduler import start_scheduler

if __name__ == "__main__":
    # Ensure necessary directories exist
    for folder in ["alerts", "agent_logs"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        
    # Start Background Scheduler
    start_scheduler()

    # ── UI Selection ────────────────────────────────────────────────────────
    # Comment/uncomment to switch between the two UIs:

    # start_ui()         # Original Streamlit UI  RUN SCRIPT: streamlit run app.py
    start_ui_jarvis()    # JARVIS HUD UI (CustomTkinter) RUN SCRIPT: python app.py
