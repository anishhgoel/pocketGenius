import logging
import sys

def setup_logging():
    """
    Basic logging config that formats logs with timestamp, level, and message.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )