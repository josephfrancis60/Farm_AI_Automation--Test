from services.report_service import ReportService
from dotenv import load_dotenv
import os

def test_report_generation():
    print("--- Testing Report Generation ---")
    load_dotenv()
    
    # Mock some env vars if missing for the test
    if not os.environ.get('TWILIO_ACCOUNT_SID'):
        os.environ['TWILIO_ACCOUNT_SID'] = 'test_sid'
        os.environ['TWILIO_AUTH_TOKEN'] = 'test_token'
        os.environ['TWILIO_PHONE_NUMBER'] = '+1234567890'
        os.environ['TARGET_PHONE_NUMBER'] = '+0987654321'

    detailed, sms = ReportService.generate_daily_report()
    
    print("\n[DETAILED REPORT CONTENT]")
    print(detailed)
    
    print("\n[SMS SUMMARY CONTENT]")
    print(sms)
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_report_generation()
