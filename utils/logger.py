import os
import logging
import sys

def setup_logger() -> logging.Logger:
    """
    Function to setup a logger ; creates a logger that writes to a file.
    Extract file name from env variable LOG_FILE.
    Check LOG_LEVEL env variable for log level: (0 means silent, 1 means informational messages, 2 means debug messages)
    Default log level is 0.

    Returns:
        logging.Logger: Configured logger instance.
    """
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    log_file = os.getenv('LOG_FILE')
    if not log_file:
        sys.exit(1)
    
    try:
        log_level = int(os.getenv("LOG_LEVEL", "0"))
    except ValueError:
        log_level = 0  # default if invalid
    
    # Map numeric levels to logging levels
    if log_level == 0:
        logging.disable(logging.CRITICAL)  # silence everything
        level = logging.NOTSET  # won't actually be used
    elif log_level == 1:
        logging.disable(logging.NOTSET)  # enable logging
        level = logging.INFO
    elif log_level == 2:
        logging.disable(logging.NOTSET)  # enable logging
        level = logging.DEBUG
    else:
        logging.disable(logging.CRITICAL)
        level = logging.NOTSET
    
    logger = logging.getLogger('cli_logger')
    logger.setLevel(level)

    if log_file and not logger.hasHandlers():
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        # Console handler (only ERROR and above)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.ERROR)
        logger.addHandler(console_handler)

    return logger