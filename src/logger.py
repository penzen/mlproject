import logging
import os
from datetime import datetime


# Create a log file name based on the current date and time.
# Example: 06_12_2026_14_30_10.log
LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"


# Create a folder path where all log files will be stored.
# This will create a folder called "logs" in your current project directory.
logs_path = os.path.join(os.getcwd(), "logs")


# Create the logs folder if it does not already exist.
# exist_ok=True means Python will not throw an error if the folder already exists.
os.makedirs(logs_path, exist_ok=True)


# Create the full path for the log file.
# Example: C:/Users/penze/Desktop/project/logs/06_12_2026_14_30_10.log
LOG_FILE_PATH = os.path.join(logs_path, LOG_FILE)


# Configure how logging should work in the whole project.
logging.basicConfig(
    filename=LOG_FILE_PATH,  # Where the log messages will be saved
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,  # This means INFO, WARNING, ERROR, CRITICAL logs will be saved
)

if __name__ == "__main__":
    logging.info("Logging has been configured successfully.")