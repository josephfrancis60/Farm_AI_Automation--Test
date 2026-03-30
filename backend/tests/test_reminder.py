import os
import json
from alerts.reminder_manager import add_reminder, get_active_reminders, clear_reminders

def run_test():
    clear_reminders()
    print("Adding reminder...")
    rem = add_reminder("Test Reminder", "This is a test.")
    print(f"Returned from add_reminder: {rem}")
    
    print("\nReading active reminders file...")
    rems = get_active_reminders()
    print(f"File contents: {json.dumps(rems, indent=2)}")
    
    if len(rems) > 0 and rems[0]["title"] == "Test Reminder":
        print("\nSUCCESS! Reminder was saved to file.")
    else:
        print("\nFAILURE! Reminder was not saved.")

if __name__ == "__main__":
    run_test()
