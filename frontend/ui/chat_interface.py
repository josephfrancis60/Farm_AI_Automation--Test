import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from agents.run_agent import run_agent
from alerts.alert_manager import get_active_alerts, clear_alerts, remove_alert
from streamlit_autorefresh import st_autorefresh
from database.db_connection import get_connection
from services.logger_service import log_agent_action

def start_ui():
    st.set_page_config(page_title="Farm AI Agent", page_icon="🌱", layout="wide")
    
    # Auto-refresh every 30 minutes
    st_autorefresh(interval=30 * 60 * 1000, key="farm_refresh")
    
    # Log UI refresh
    log_agent_action("Streamlit UI refreshed/reloaded.")

    st.title("Farm AI Agent 🌱")

    # --- SIDEBAR DASHBOARD ---
    with st.sidebar:
        st.header("🚜 Farm Status Dashboard")
        
        # Display City Name
        city = os.getenv("FARM_CITY", "Kanija Bhavan")
        st.write(f"📍 **Location:** {city}")
        
        # st.divider()
        
        # 1. Latest Metrics
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Weather
            cursor.execute("SELECT TOP 1 Temperature, Rain, Humidity FROM WeatherHistory ORDER BY Timestamp DESC")
            weather_row = cursor.fetchone()
            if weather_row:
                col1, col2 = st.columns(2)
                col1.metric("Temp", f"{weather_row.Temperature}°C")
                col2.metric("Humidity", f"{weather_row.Humidity}%")
                st.write(f"**Condition:** {weather_row.Rain}")
            
            st.divider()

            # Fields Overview
            # st.subheader("🌾 Fields Status")
            # cursor.execute("SELECT Crop, SoilType FROM Fields")
            # fields = cursor.fetchall()
            # for f in fields:
            #     st.write(f"- **{f.Crop}:** {f.SoilType} soil")

            # conn.close()

        # st.divider()

        # 2. Alerts Header and Clear All Button
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.subheader("🔔 Recent Alerts")
        with col_b:
            if st.button("Clear", key="clear_all_alerts", help="Clear all alerts"):
                clear_alerts()
                log_agent_action("User cleared all alerts from UI.")
                st.rerun()

        alerts = get_active_alerts()
        if not alerts:
            st.info("No active alerts.")
        else:
            for alert in alerts[:8]:
                with st.expander(f"{alert['title']} ({alert['timestamp']})"):
                    st.write(alert['message'])
                    
                    # Action Trigger Button
                    col1, col2 = st.columns([4, 1])
                    with col2:
                        if st.button("⚡", key=f"act_{alert['id']}", help="Trigger action for this alert"):
                            trigger_alert_action(alert)
                            remove_alert(alert["id"])
                            st.rerun()
                    
                    if alert['category'] == "WARNING":
                        st.warning("Action suggested")
                    elif alert['category'] == "SUCCESS":
                        st.success("Milestone achieved")

    # --- CHAT INTERFACE ---
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "time" in message:
                st.markdown(f"{message['content']} <div style='text-align: right; color: gray; font-size: 0.8em;'>{message['time']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your farm..."):
        now = datetime.now().strftime("%I:%M %p")
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt, "time": now})
        with st.chat_message("user"):
            st.markdown(f"{prompt} <div style='text-align: right; color: gray; font-size: 0.8em;'>{now}</div>", unsafe_allow_html=True)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_agent(prompt)
                resp_time = datetime.now().strftime("%I:%M %p")
                st.markdown(f"{response} <div style='text-align: right; color: gray; font-size: 0.8em;'>{resp_time}</div>", unsafe_allow_html=True)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response, "time": resp_time})

def trigger_alert_action(alert):
    """
    Handles autonomous actions triggered by User from an alert.
    """
    title = alert["title"].lower()
    msg = alert["message"]
    log_agent_action(f"User triggered action from alert: {alert['title']}", details=msg)
    
    # Construct a message for the agent to process the action
    if "irrigation" in title or "watering" in title or "water" in msg.lower():
        prompt = f"System Context: The user wants to proceed with the recommendation in this alert: '{msg}'. Please check the current irrigation status first, and if it still makes sense, activate the sprinkler. If it was already watered or conditions changed, explain that instead."
        if "messages" in st.session_state:
            now = datetime.now().strftime("%I:%M %p")
            st.session_state.messages.append({"role": "user", "content": f"[Action Requested]: {alert['title']}", "time": now})
            response = run_agent(prompt)
            resp_time = datetime.now().strftime("%I:%M %p")
            st.session_state.messages.append({"role": "assistant", "content": response, "time": resp_time})
        else:
            run_agent(prompt)
    else:
        # Generic ack for other alerts
        run_agent(f"System Log: User acknowledged alert '{alert['title']}': {msg}. No further action needed.")