import logging
import sys

logger = logging.getLogger()

console_handler = logging.StreamHandler(stream=sys.stdout)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(console_handler)
logger.setLevel(logging.INFO)
