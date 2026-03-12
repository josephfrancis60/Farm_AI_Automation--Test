from apscheduler.schedulers.background import BackgroundScheduler
from services.weather_monitor import monitor_weather
from monitoring.farm_monitor import check_farm_status
import time

def start_scheduler():
    """
    Initializes and starts the background scheduler for farm tasks.
    """
    scheduler = BackgroundScheduler()

    # Weather checks every 30 minutes
    scheduler.add_job(monitor_weather, 'interval', minutes=30, id='weather_check')
    
    # Farm monitoring every 10 minutes
    scheduler.add_job(check_farm_status, 'interval', minutes=10, id='farm_monitor')

    # Initial Run (optional, but good for instant feedback)
    print("DEBUG: Starting initial monitoring run...")
    monitor_weather()
    check_farm_status()

    scheduler.start()
    print("DEBUG: Background Scheduler started successfully.")
    return scheduler

if __name__ == "__main__":
    # Keep the script running if executed directly
    sched = start_scheduler()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()
