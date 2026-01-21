"""
Consumer Script - Processes messages from RabbitMQ

Concept: CONSUMER
- This script runs separately (like a background worker)
- It listens to the queue and processes messages
- Like a person checking their mailbox every few seconds
"""
from app.helpers.helper import get_rmq_instance, get_db_instance, db_mapper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_user_onboarding(message):
    """
    This function processes each message
    
    Concept: Callback Function
    - Called automatically when a message arrives
    - Does the actual work (save to DB, send email, etc.)
    - Returns True if successful, False if failed
    """
    try:
        logger.info("Processing user onboarding...")
        
        data = db_mapper(message)
        
        database = get_db_instance()
        user = database.get_table_class("users")
        with database.get_db() as sess:
            sess.add(user(**data))
            sess.commit()
        
        logger.info(f"User {message.get('user_id')} processed successfully!, verification state: {message.get('verification')}")
        
        return True  # Success - message will be deleted
        
    except Exception as e:
        logger.error(f"Error processing user: {e}")
        return False  # Failure - message goes to DLQ

if __name__ == "__main__":

    rmq = get_rmq_instance()

    if not rmq.channel or rmq.channel.is_closed:
        rmq.connect()

    # Start consuming (this runs forever until you stop it)
    try:
        logger.info("Starting consumer...")
        rmq.consume_messages("user_onboarding_queue", process_user_onboarding)
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
        rmq.close()
    except Exception as e:
        raise