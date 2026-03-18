from apscheduler.schedulers.background import BackgroundScheduler
from services.weather_monitor import monitor_weather
from monitoring.farm_monitor import check_farm_status
from services.report_service import ReportService
from datetime import datetime, timedelta
import time
import os
from database.db_connection import get_connection

def update_heartbeat():
    """Updates the SystemState LastRunTime to act as a heartbeat."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Update LastHeartbeat to act as a granular heartbeat
            cursor.execute("UPDATE SystemState SET LastHeartbeat = ? WHERE Id = 1", (datetime.now(),))
            conn.commit()
        finally:
            conn.close()

def start_scheduler():
    """
    Initializes and starts the background scheduler for farm tasks.
    """
    scheduler = BackgroundScheduler()

    # Weather checks every 30 minutes
    scheduler.add_job(monitor_weather, 'interval', minutes=30, id='weather_check')
    
    # Farm monitoring every 30 minutes (Updated from 10)
    scheduler.add_job(check_farm_status, 'interval', minutes=30, id='farm_monitor')
    
    # Heartbeat every 1 minute
    scheduler.add_job(update_heartbeat, 'interval', minutes=1, id='system_heartbeat')

    # Daily Report at 17:00 (5:00 PM)
    scheduler.add_job(ReportService.generate_daily_report, 'cron', hour=17, minute=0, id='daily_report')

    # Initial Run (Bypass throttle to detect downtime immediately)
    print("DEBUG: Starting initial monitoring run...")
    monitor_weather()
    check_farm_status(skip_throttle=True)
    
    # Check for missed reports
    check_for_missed_reports()

    scheduler.start()
    print("DEBUG: Background Scheduler started successfully.")
    return scheduler

def check_for_missed_reports():
    """
    Checks the last 3 days for missing report files and generates them.
    Sends SMS only for today's report if missed and it's past 17:00.
    """
    print("DEBUG: Checking for missed daily reports...")
    report_dir = r"c:\Users\joseph.francis\My Projects\Farm-AI-agent\reports\daily_reports"
    now = datetime.now()
    
    for i in range(3): # Check last 3 days
        target_date = now - timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        report_file = os.path.join(report_dir, f"report_{date_str}.txt")
        
        if not os.path.exists(report_file):
            # Skip today's report if it's before 17:00
            is_today = (i == 0)
            if is_today and now.hour < 17:
                print(f"DEBUG: Skipping today's report ({date_str}) as it's not yet 17:00.")
                continue

            print(f"DEBUG: Missed report found for {date_str}. Generating...")
            
            # Should we send SMS? 
            # Only if it's today (i=0) and it's past 17:00.
            is_past_reporting_time = (now.hour >= 17)
            should_send_sms = is_today and is_past_reporting_time
            
            try:
                ReportService.generate_daily_report(target_date=target_date, should_send_sms=should_send_sms)
            except Exception as e:
                print(f"Error generating missed report for {date_str}: {e}")
        else:
            print(f"DEBUG: Report for {date_str} already exists.")

if __name__ == "__main__":
    # Keep the script running if executed directly
    sched = start_scheduler()
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()
