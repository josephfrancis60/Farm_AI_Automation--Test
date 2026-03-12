from scheduler.farm_scheduler import start_scheduler
from alerts.alert_manager import get_active_alerts
from agents.run_agent import run_agent
import time
import os

def verify_all():
    print("--- Proactive Farm Agent Verification ---")
    
    # 1. Start Scheduler (Initial run handles weather and monitor)
    print("\n1. Testing Scheduler and Services...")
    sched = start_scheduler()
    time.sleep(10) # Wait for initial runs to finish
    
    # 2. Check Alerts
    print("\n2. Checking Generated Alerts...")
    alerts = get_active_alerts()
    if alerts:
        print(f"Found {len(alerts)} alerts:")
        for a in alerts[:3]:
            print(f"- [{a['category']}] {a['title']}: {a['message']}")
    else:
        print("No alerts found. This might mean conditions are normal.")

    # 3. Test Agent Reasoning
    print("\n3. Testing Agent Reasoning Loop...")
    prompt = "Sam, how are the crops doing? Any harvests soon?"
    print(f"User: {prompt}")
    response = run_agent(prompt)
    print(f"Agent: {response}")

    # 4. Check Agent Logs
    print("\n4. Checking Agent Logs...")
    if os.path.exists("agent_logs"):
        log_files = os.listdir("agent_logs")
        print(f"Found {len(log_files)} agent log files.")
    else:
        print("agent_logs folder not found!")

    # 5. Test Alert Removal
    print("\n5. Testing Alert Removal...")
    alerts = get_active_alerts()
    if alerts:
        aid = alerts[0]["id"]
        from alerts.alert_manager import remove_alert
        if remove_alert(aid):
            print(f"Successfully removed alert {aid}")
        else:
            print(f"Failed to remove alert {aid}")

    # Shutdown
    sched.shutdown()
    print("\n--- Verification Completed ---")

if __name__ == "__main__":
    verify_all()
