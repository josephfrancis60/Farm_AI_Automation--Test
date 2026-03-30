import logging
import os
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler

def get_logger(log_dir="logs"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # File name based on date: logs/YYYY-MM-DD.log (UTC)
    log_file = os.path.join(log_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log")

    # Use a unique name for each log directory to avoid handler overlap
    logger_name = f"FarmAIAgent_{log_dir.replace('/', '_')}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if get_logger is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()

        file_handler = TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d" 

        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def log_agent_action(message, status="INFO", details=None):
    """Logs autonomous agent actions in agent_logs/ folder."""
    logger = get_logger("agent_logs")
    log_msg = f"[AGENT] {message}"
    if details:
        log_msg += f"\nDetails: {details}"
    
    if status == "WARNING":
        logger.warning(log_msg)
    elif status == "ERROR":
        logger.error(log_msg)
    else:
        logger.info(log_msg)

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

# Human-readable names for each tool, used in logs
TOOL_DISPLAY_NAMES = {
    "check_irrigation_status": "Irrigation Schedule & Weather Check",
    "irrigation":              "Irrigation Activation (Sprinkler)",
    "crops":                   "Crop List Lookup",
    "add_new_crop":            "Add New Crop",
    "update_existing_field":   "Update Crop Field",
    "delete_crop_field":       "Delete Crop Field",
    "weather":                 "Weather Forecast",
    "fertilizer":              "Fertilizer Recommendation",
    "inventory":               "Fertilizer Inventory Check",
    "add_inventory_item":      "Add Inventory Item",
    "update_inventory_stock":  "Update Inventory Stock",
    "remove_from_inventory":   "Remove Inventory Item",
}

def log_full_state(human_input, agent_output, tool_calls=None, tool_outputs=None, tokens=None):
    logger = get_logger()
    
    separator = "-" * 50
    header = f"\n{separator}\nNEW INTERACTION\n{separator}"
    logger.info(header)
    
    # 1. User input
    logger.info(f"USER INPUT  : {human_input}")
    
    # 2. Tool steps (calls + responses interleaved)
    if tool_calls:
        tool_outputs = tool_outputs or {}
        
        for i, tc in enumerate(tool_calls, start=1):
            tool_name = tc.get('name', 'unknown')
            tool_args = tc.get('args', {})
            tool_id   = tc.get('id', '')
            display   = TOOL_DISPLAY_NAMES.get(tool_name, tool_name)
            
            # Log tool call
            logger.info(f"TOOL [{i}] CALLED  : {display}")
            logger.info(f"       PARAMETERS : {tool_args}")
            
            # Log tool response
            output = tool_outputs.get(tool_id)
            if output is not None:
                # Indent multi-line outputs for readability
                formatted = str(output).replace('\n', '\n              ')
                logger.info(f"       RESPONSE  : {formatted}")
    
    # 3. Final agent response
    logger.info(f"AGENT REPLY : {agent_output}")
    
    # 4. Token usage (clean, short)
    if tokens:
        prompt_t     = tokens.get('prompt_tokens', '?')
        completion_t = tokens.get('completion_tokens', '?')
        total_t      = tokens.get('total_tokens', '?')
        total_time   = round(tokens.get('total_time', 0), 3)
        logger.info(
            f"TOKENS      : prompt={prompt_t} | completion={completion_t} | "
            f"total={total_t} | time={total_time}s"
        )
    
    logger.info(f"{separator}\n")
