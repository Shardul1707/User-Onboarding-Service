import pika
import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path="app/configs/.env")


class RabbitMQHelper:
    """
    Simple RabbitMQ Helper Class
    
    Concepts explained:
    - Connection: Like a phone line to RabbitMQ server
    - Channel: Like a conversation on that phone line (lighter than connection)
    - Exchange: The router that decides which queue gets the message
    - Queue: The mailbox that holds messages
    - Binding: The rule that connects exchange to queue
    """
    
    def __init__(self):
        # Connection details (like phone number and password)
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USERNAME", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
        
        self.connection = None
        self.channel = None
    
    def connect(self):
        """
        Step 1: Connect to RabbitMQ
        
        Concept: Connection
        - Like dialing a phone number
        - Establishes communication with RabbitMQ server
        - Can have multiple channels on one connection
        """
        try:
            # Create credentials (username/password)
            credentials = pika.PlainCredentials(self.username, self.password)
            
            # Connection parameters (where to connect)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,  # Keep connection alive (10 minutes)
                blocked_connection_timeout=300,  # Timeout for blocked connections
                connection_attempts=3,  # Retry connection attempts
                retry_delay=2  # Delay between retries
            )
            
            # Actually connect (dial the phone)
            self.connection = pika.BlockingConnection(parameters)
            
            # Create a channel (start a conversation)
            self.channel = self.connection.channel()
            
            logger.info("Connected to RabbitMQ!")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def setup_queue(self, queue_name="user_onboarding_queue"):
        """
        Step 2: Create a Queue
        
        Concept: Queue
        - Like a mailbox that holds messages
        - Messages wait here until someone picks them up
        - Can be durable (survives server restart) or not
        
        Concept: Queue Arguments (Advanced Settings)
        - x-message-ttl: Messages expire after this time (like milk expiration date)
        - x-dead-letter-exchange: Where failed messages go (like a dead letter office)
        - x-dead-letter-routing-key: Which DLQ queue to use
        """
        # Ensure connection is open
        self._ensure_connection()
        
        # Declare the queue (create the mailbox)
        # durable=True means: "Keep this mailbox even if server restarts"
        self.channel.queue_declare(
            queue=queue_name,
            durable=True,  # Queue survives server restart
            arguments={
                # TTL: Time To Live - messages expire after 1 hour
                # Like: "This message is only valid for 1 hour"
                'x-message-ttl': 3600000,  # 1 hour in milliseconds
                
                # DLQ: Dead Letter Queue - where failed messages go
                # Like: "If message can't be delivered, put it in the 'failed' mailbox"
                'x-dead-letter-exchange': '',  # Empty = default exchange
                'x-dead-letter-routing-key': f'{queue_name}_dlq',  # DLQ name
            }
        )
        
        # Also create the Dead Letter Queue (the "failed messages" mailbox)
        self.channel.queue_declare(
            queue=f'{queue_name}_dlq',
            durable=True,
            arguments={
                'x-message-ttl': 86400000,  # Keep failed messages for 24 hours
            }
        )
        
        logger.info(f"Queue '{queue_name}' created with DLQ: '{queue_name}_dlq'")
    
    def _ensure_connection(self):
        """Ensure connection and channel are open, reconnect if needed"""
        try:
            # Check if connection is closed or doesn't exist
            if not self.connection or self.connection.is_closed:
                logger.warning("Connection closed, reconnecting...")
                self.connect()
            # Check if channel is closed or doesn't exist
            elif not self.channel or self.channel.is_closed:
                logger.warning("Channel closed, recreating...")
                self.channel = self.connection.channel()
        except Exception as e:
            logger.error(f"Error ensuring connection: {e}")
            # Force reconnect
            self.connection = None
            self.channel = None
            self.connect()
    
    def publish_message(self, queue_name, message_data):
        """
        Step 3: Publish a Message
        
        Concept: Publishing
        - Sending a message to a queue
        - Like putting a letter in a mailbox
        
        Concept: Exchange (Default)
        - We're using default exchange (empty string '')
        - Default exchange routes directly to queue by name
        - Like: "Put this in mailbox named 'user_onboarding_queue'"
        
        Concept: Routing Key
        - In default exchange, routing_key = queue name
        - Like: "The address on the envelope"
        """
        # Ensure connection is open before publishing
        self._ensure_connection()
        
        # Convert message to JSON string
        message_json = json.dumps(message_data)
        
        try:
            # Publish the message
            # exchange='' means: "Use default exchange"
            # routing_key=queue_name means: "Send to this queue"
            # properties: Message settings (like "mark as important")
            self.channel.basic_publish(
                exchange='',  # Default exchange (simplest - routes directly to queue)
                routing_key=queue_name,  # Which queue to send to
                body=message_json,  # The actual message
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent (survives server restart)
                    content_type='application/json',  # Message format
                )
            )
            logger.info(f"Message published to '{queue_name}': {message_data.get('user_id', 'N/A')}")
        except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed, BrokenPipeError) as e:
            logger.warning(f"Connection/channel error during publish: {e}, reconnecting...")
            # Reconnect and retry once
            self._ensure_connection()
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                )
            )
            logger.info(f"Message published to '{queue_name}' after reconnect: {message_data.get('user_id', 'N/A')}")
    
    def consume_messages(self, queue_name, callback_function):
        """
        Step 4: Consume Messages
        
        Concept: Consuming
        - Reading messages from a queue
        - Like checking your mailbox and reading letters
        
        Concept: Callback
        - Function that processes each message
        - Like: "When you get a letter, do this with it"
        
        Concept: Acknowledgment (ACK)
        - Telling RabbitMQ: "I got the message, you can delete it"
        - If you don't ACK, message stays in queue (for retry)
        """
        if not self.channel:
            self.connect()
        
        # Define what to do when a message arrives
        def on_message_received(ch, method, properties, body):
            try:
                # Parse the message
                message = json.loads(body)
                logger.info(f"Received message: {message.get('user_id', 'N/A')}")
                
                # Process the message using your callback function
                success = callback_function(message)
                
                if success:
                    # Acknowledge: "Message processed successfully, you can delete it"
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info("Message processed and acknowledged")
                else:
                    # Negative Acknowledge: "Message failed, don't delete it yet"
                    # requeue=False means: "Don't put it back, send to DLQ"
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    logger.warning("Message processing failed, sent to DLQ")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Send to DLQ on error
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        # Start consuming (start checking the mailbox)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message_received,
            auto_ack=False  # Manual acknowledgment (we control when to ACK)
        )
        
        logger.info(f"Listening for messages on '{queue_name}'...")
        logger.info("Press CTRL+C to stop")
        
        # Start consuming (this blocks and waits for messages)
        self.channel.start_consuming()
    
    def close(self):
        """Close the connection (hang up the phone)"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Connection closed")