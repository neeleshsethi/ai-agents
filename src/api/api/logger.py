import logging
import sys

# Configure logger
logger = logging.getLogger(__name__)
formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Set up handlers
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)

# Configure logger
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)    


