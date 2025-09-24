import os
import logging


def setup_logger() -> logging.Logger:
    """Function to setup a logger ; creates a logger that writes to a file and the console.
    Extract file name from env variable LOG_FILE.
    Check LOG_LEVEL env variable for log level: (0 means silent, 1 means informational messages, 2 means debug messages)
    Default log level is 0.

    Returns:
        logging.Logger: Configured logger instance.
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_file = os.getenv('LOG_FILE')
    if not log_file:
        raise ValueError("Environment variable 'LOG_FILE' is not set.")
    
    try:
        log_level = int(os.getenv("LOG_LEVEL", "0"))
    except ValueError:
        log_level = 0  # default if invalid
    
    # Map numeric levels to logging levels
    if log_level == 0:
        logging.disable(logging.CRITICAL)  # silence everything
        level = logging.NOTSET # won't be used
    elif log_level == 1:
        level = logging.INFO
    elif log_level == 2:
        level = logging.DEBUG

    logger = logging.getLogger('cli_logger')
    logger.setLevel(level)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger