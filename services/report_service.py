import os
from datetime import datetime, timezone
from twilio.rest import Client
from database.db_connection import get_connection
from services.logger_service import log_interaction

class ReportService:
    @staticmethod
    def generate_daily_report(target_date=None, should_send_sms=True):
        """
        Gathers data from the database and generates a daily report for a specific date.
        Saves the detailed report to a file and optionally sends an SMS summary.
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc)
            
        date_str = target_date.strftime('%Y-%m-%d')
        report_dir = r"c:\Users\joseph.francis\My Projects\Farm-AI-agent\reports\daily_reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        report_file = os.path.join(report_dir, f"report_{date_str}.txt")
        
        # 1. Gather Data
        detailed_content = f"--- DAILY FARM REPORT: {date_str} ---\n\n"
        sms_summary = f"Farm Report {date_str}:\n"
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # A. Crops Summary (Always current state, or we could historicalize if we had snapshots)
            cursor.execute("SELECT Crop, SoilType, Area FROM Fields")
            crops = cursor.fetchall()
            detailed_content += "1. CROP FIELDS SUMMARY:\n"
            if crops:
                for row in crops:
                    detailed_content += f"- {row.Crop}: {row.Area} acres, {row.SoilType} soil\n"
                sms_summary += f"- {len(crops)} crops active.\n"
            else:
                detailed_content += "- No crops found.\n"
            detailed_content += "\n"
            
            # B. Irrigation History for the target date
            cursor.execute("""
                SELECT f.Crop, ih.DurationMinutes, ih.ActivatedAt 
                FROM IrrigationHistory ih
                JOIN Fields f ON ih.FieldId = f.FieldId
                WHERE CAST(ih.ActivatedAt AS DATE) = ?
            """, (date_str,))
            irrigation = cursor.fetchall()
            detailed_content += "2. IRRIGATION ACTIVITIES TODAY:\n"
            if irrigation:
                for row in irrigation:
                    time_str = row.ActivatedAt.strftime('%H:%M')
                    detailed_content += f"- {row.Crop}: {row.DurationMinutes} mins at {time_str}\n"
                sms_summary += f"- {len(irrigation)} fields irrigated.\n"
            else:
                detailed_content += "- No irrigation recorded today.\n"
            detailed_content += "\n"
            
            # C. Fertilizer Inventory (Current state)
            cursor.execute("SELECT FertilizerName, StockKg FROM FertilizerInventory")
            inventory = cursor.fetchall()
            detailed_content += "3. FERTILIZER INVENTORY & RECOMMENDATIONS:\n"
            restock_list = []
            if inventory:
                for row in inventory:
                    status = "OK"
                    recommendation = ""
                    if row.StockKg < 10:
                        recomm_qty = 50 - row.StockKg
                        status = "LOW"
                        recommendation = f" -> RECO: Restock {recomm_qty}kg"
                        restock_list.append(f"{row.FertilizerName}({recomm_qty}kg)")
                    
                    detailed_content += f"- {row.FertilizerName}: {row.StockKg}kg [{status}]{recommendation}\n"
            else:
                detailed_content += "- Inventory is empty.\n"
            
            if restock_list:
                sms_summary += f"- Need: {', '.join(restock_list)}\n"
            detailed_content += "\n"
            
            # D. Weather History (Latest entry BEFORE or ON target date)
            cursor.execute("""
                SELECT TOP 1 Temperature, Rain, Humidity FROM WeatherHistory 
                WHERE CAST(Timestamp AS DATE) <= ?
                ORDER BY Timestamp DESC
            """, (date_str,))
            weather = cursor.fetchone()
            detailed_content += "4. LATEST WEATHER UPDATE:\n"
            if weather:
                detailed_content += f"- Temp: {weather.Temperature}°C, Condition: {weather.Rain}, Humidity: {weather.Humidity}%\n"
                # Keep SMS weather very short
                weather_short = "Rainy" if "rain" in weather.Rain.lower() else weather.Rain
                sms_summary += f"- Weather: {weather_short}, {int(weather.Temperature)}C\n"
            else:
                detailed_content += "- No weather data available.\n"
                
        except Exception as e:
            detailed_content += f"\nERROR GATHERING DATA: {e}\n"
            log_interaction("SYSTEM", f"Report Generation Error: {e}", status="ERROR")
        finally:
            conn.close()
            
        # 2. Save Detailed Report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(detailed_content)
            
        # 3. Send SMS Summary (Only if requested and it's for today)
        if should_send_sms:
            ReportService.send_sms(sms_summary)
        
        return detailed_content, sms_summary

    @staticmethod
    def send_sms(body):
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        target_phone = os.environ.get('TARGET_PHONE_NUMBER')

        if account_sid and auth_token and account_sid != "your_account_sid_here":
            try:
                client = Client(account_sid, auth_token)
                client.messages.create(
                    body=body,
                    from_=twilio_phone,
                    to=target_phone
                )
                log_interaction("SYSTEM", f"SMS summary sent to {target_phone}.")
            except Exception as e:
                log_interaction("SYSTEM", f"Failed to send SMS summary: {str(e)}", status="ERROR")
        else:
            log_interaction("SYSTEM", "Twilio credentials not configured. SMS summary skipped.", status="WARNING")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ReportService.generate_daily_report()
