import logging
import time
from app.db_conn import Database
from app.rmq_adapter import RabbitMQHelper
from datetime import datetime
from base64 import b64encode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry(func, name="operation", max_retries=3):
    """Retry function with exponential backoff"""
    delay = 2
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries:
                logger.warning(f"{name} failed (attempt {attempt}/{max_retries}), retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, 10)  # Exponential backoff, max 10s
            else:
                logger.error(f"{name} failed after {max_retries} attempts: {e}")
                raise

# Import global db instance (lazy import to avoid circular dependencies)
def get_db_instance():
    """Get global db instance from main, or create new one if not available"""
    try:
        from app.main import db
        return db if db else Database()
    except (ImportError, AttributeError):
        # If main hasn't initialized db yet, create a new instance
        return Database()

def get_rmq_instance():
    try:
        from app.main import rmq
        return rmq if rmq else RabbitMQHelper()
    except (ImportError, AttributeError):
        # If main hasn't initialized rmq yet, create a new instance
        return RabbitMQHelper()

def db_mapper(data: dict):
    temp = {}

    temp['email'] = data['email']
    temp['first_name'] = data['first_name']
    temp['last_name'] = data['last_name']
    temp['password'] = b64encode(data['password'].encode()).decode()
    temp['user_id'] = data['user_id']
    temp['verification_state'] = data['verification']
    temp['created_on'] = datetime.now()

    return temp