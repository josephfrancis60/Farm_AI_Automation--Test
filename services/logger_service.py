import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

def get_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File name based on date: logs/YYYY-MM-DD.log
    # However, TimedRotatingFileHandler handles rotation. 
    # To get the exact "logs/2026-03-09.log" format initially:
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

    logger = logging.getLogger("FarmAIAgent")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if get_logger is called multiple times
    if not logger.handlers:
        # Create a custom formatter
        # Format: datetime - status - human/agent - message
        # We'll use a simple format here and do manual formatting in the service
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Timed hould handle the "one file per day" requirement
        # whenInterval=1, interval=1, backupCount=30
        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d" # This adds date suffix on rotation

        logger.addHandler(file_handler)
        
        # Also log to console for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def log_interaction(role, message, status="INFO", details=None):
    logger = get_logger()
    
    log_msg = f"[{role.upper()}] {message}"
    if details:
        log_msg += f"\nDetails: {details}"
    
    if status == "WARNING":
        logger.warning(log_msg)
    elif status == "ERROR":
        logger.error(log_msg)
    else:
        logger.info(log_msg)

def log_full_state(human_input, agent_output, tool_calls=None, tokens=None):
    logger = get_logger()
    
    separator = "-" * 50
    header = f"\n{separator}\nNEW INTERACTION\n{separator}"
    logger.info(header)
    
    logger.info(f"HUMAN: {human_input}")
    
    if tool_calls:
        for tc in tool_calls:
            logger.info(f"AGENT TOOL DECISION: {tc.get('name')} | PARAMETERS: {tc.get('args')}")
            
    logger.info(f"AGENT REPLY: {agent_output}")
    
    if tokens:
        logger.info(f"TOKEN USAGE: {tokens}")
    
    logger.info(f"{separator}\n")
