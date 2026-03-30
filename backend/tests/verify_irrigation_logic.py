import unittest
from unittest.mock import patch, MagicMock
import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.agent_tools import check_irrigation_status

class TestIrrigationLogic(unittest.TestCase):

    @patch('tools.agent_tools.get_irrigation_schedule')
    @patch('tools.agent_tools.get_weather')
    @patch('tools.agent_tools.get_field_id_by_crop')
    @patch('tools.agent_tools.datetime')
    def test_irrigation_needed_no_rain(self, mock_datetime, mock_field_id, mock_weather, mock_schedule):
        # Setup mock data
        fixed_now = datetime.datetime(2026, 3, 10, 6, 0)
        mock_datetime.now.return_value = fixed_now
        # Also mock strftime if needed, but the real datetime object has it
        
        mock_schedule.return_value = [
            {'crop': 'Tomato', 'day': 'Tuesday', 'time': '06:00', 'duration': 20}
        ]
        mock_weather.return_value = {
            "current": {"condition": "clear sky"},
            "forecast": [{"time": "2026-03-10 09:00", "condition": "clear sky"}]
        }
        mock_field_id.return_value = 1
        
        # Call tool logic
        func = getattr(check_irrigation_status, 'func', check_irrigation_status)
        result = func("Sample City")
        
        self.assertIn("Recommendation: PROCEED with irrigation", result)
        self.assertIn("Tomato (Field ID: 1)", result)

    @patch('tools.agent_tools.get_irrigation_schedule')
    @patch('tools.agent_tools.get_weather')
    @patch('tools.agent_tools.get_field_id_by_crop')
    @patch('tools.agent_tools.datetime')
    def test_irrigation_skipped_due_to_rain(self, mock_datetime, mock_field_id, mock_weather, mock_schedule):
        # Setup mock data
        fixed_now = datetime.datetime(2026, 3, 10, 6, 0)
        mock_datetime.now.return_value = fixed_now
        
        mock_schedule.return_value = [
            {'crop': 'Tomato', 'day': 'Tuesday', 'time': '06:00', 'duration': 20}
        ]
        mock_weather.return_value = {
            "current": {"condition": "clear sky"},
            "forecast": [{"time": "2026-03-10 09:00", "condition": "light rain"}]
        }
        mock_field_id.return_value = 1
        
        func = getattr(check_irrigation_status, 'func', check_irrigation_status)
        result = func("Sample City")
        
        self.assertIn("Recommendation: SKIP irrigation", result)
        self.assertIn("Rain (light rain) is forecasted", result)

    @patch('tools.agent_tools.get_irrigation_schedule')
    @patch('tools.agent_tools.datetime')
    def test_no_schedule(self, mock_datetime, mock_schedule):
        fixed_now = datetime.datetime(2026, 3, 10, 6, 0)
        mock_datetime.now.return_value = fixed_now
        mock_schedule.return_value = []
        
        func = getattr(check_irrigation_status, 'func', check_irrigation_status)
        result = func("Sample City")
        self.assertIn("No irrigation is scheduled for today", result)

if __name__ == '__main__':
    unittest.main()
