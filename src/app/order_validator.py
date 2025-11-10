'''
# Order Validation and Enrichment Service
- Reads from 'orders' topic, validates, enriches
- Routes enriched messages to appropriate topics
- All logs output to stdout/stderr for Docker logs
'''

from kafka import KafkaConsumer, KafkaProducer # Kafka client libraries
from kafka.errors import KafkaError # For Kafka error handling
import json # For JSON serialization/deserialization
import sys # For sys.exit and stdout/stderr access
import os # For environment variable access
import logging # For logging configuration and usage
from datetime import datetime, timedelta # For deserialising UNIX timestamps

#############################################################
# INITIAL SETTINGS
#############################################################

# Configure logging to output to stdout (Docker logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Output to stdout for Docker logs
    ]
)
logger = logging.getLogger(__name__)

# Kafka Configuration from environment variables
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092").split(",")
ORDERS_TOPIC = os.getenv("ORDERS_TOPIC", "orders")
INVALID_ORDERS_TOPIC = os.getenv("INVALID_ORDERS_TOPIC", "invalid_orders")
ENRICHED_ORDERS_TOPIC = os.getenv("ENRICHED_ORDERS_TOPIC", "enriched_orders")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "order-validator") # Note necessary for a single consumer, but added for conceptual clarity
# NOTE: These environment variables have been declared and initialised during the running of Docker Compose

# Required fields for validation
REQUIRED_FIELDS = [
    "order_id",
    "product_name",
    "quantity",
    "price",
    "order_date"
]

#############################################################
# FUNCTION DEFINTIONS FOR:
# - Consumer creation
# - Producer creation
# - Message validation
# - Message processing after validation (including rerouting to relevant topics)
# - Main loop definition (including information logging and graceful shutdown logic)
#############################################################

# HELPER FOR `create_consumer`
def safe_deserializer(m):
        if m is None:
            return None
        try:
            if isinstance(m, bytes):
                return json.loads(m.decode("utf-8"))
            elif isinstance(m, str):
                return json.loads(m)
            else:
                return m
        except Exception as e:
            logger.error(f"Error deserializing message: {e}, raw message: {m}")
            return None

def create_consumer() -> KafkaConsumer:
    '''
    Create and configure Kafka consumer.
    
    ---

    RETURNS:
    - (KafkaConsumer): KafkaConsumer instance
    '''
    
    return KafkaConsumer(
        ORDERS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,  # Consumer group for offset management
        auto_offset_reset="earliest",
        enable_auto_commit=False,  # Manual commit for idempotency
        value_deserializer=safe_deserializer,
        max_poll_records=10,  # Process in small batches
        session_timeout_ms=30000,  # 30 seconds
        heartbeat_interval_ms=10000  # 10 seconds
    )

#================================================
# HELPER FOR `create_producer`
def create_schema_message(payload: dict) -> dict:
    '''
    Wrap payload with JSON schema for Kafka Connect compatibility.
    
    ---
    
    PARAMETERS:
    - `payload` (dict): The actual message data
    
    RETURNS:
    - (dict): Message with embedded schema
    '''

    return {
        "schema": {
            "type": "struct",
            "fields": [
                {"type": "string", "optional": True, "field": "order_id"},
                {"type": "string", "optional": True, "field": "product_name"},
                {"type": "double", "optional": True, "field": "quantity"},
                {"type": "double", "optional": True, "field": "price"},
                {"type": "string", "optional": True, "field": "order_date"},
                {"type": "double", "optional": True, "field": "total_price"}
            ],
            "optional": False,
            "name": "enriched_order"
        },
        "payload": payload
    }

def create_producer():
    '''
    Create and configure Kafka producer with reliability settings.
    
    ---

    RETURNS:
    - (KafkaProducer): KafkaProducer instance
    '''

    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(create_schema_message(v)).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        acks='all',
        retries=3,
        max_in_flight_requests_per_connection=1
    )

#================================================
# HELPER FOR `validate_and_enrich_message`
def is_valid_number(value:str) -> bool:
    '''
    Small helper to check if the string is a valid number.

    ---

    PARAMETERS:
    - `value` (str): Value to check

    RETURNS:
    - (bool): True if valid number, False otherwise
    '''

    try:
        float(value)
        return True
    except:
        return False

def validate_and_enrich_message(message:dict) -> tuple[dict, bool, str]:
    '''
    Validate and enrich an order message.
    
    ---

    PARAMETERS:
    - `message` (dict): JSON message as a dictionary object

    RETURNS:
    - (Dict): Enriched message (if valid) or original message (if invalid)
    - (bool): Is valid
    - (str): Error message
    '''

    # Fix: Initialize return_value correctly
    is_valid = True
    error_messages = []
    
    try:
        # Check for required fields
        missing_fields = [field for field in REQUIRED_FIELDS if field not in message]
        if missing_fields:
            return message, False, f"Missing required fields: {', '.join(missing_fields)}"

        # Validate price
        if not is_valid_number(message["price"]):
            is_valid = False
            error_messages.append(f"Field 'price' should be a number, but is of value: {message['quantity']}")
        else:
            message["price"] = float(message["price"])
            if message["price"] < 0: # Check negative price
                is_valid = False
                error_messages.append("Field 'price' should be non-negative")
        
        # Validate quantity
        if not is_valid_number(message["quantity"]):
            is_valid = False
            error_messages.append(f"Field 'quantity' should be a number, but is of value: {message['quantity']}")
        else:
            message["quantity"] = float(message["quantity"])
            if message["quantity"] < 0: # Check negative quantity
                is_valid = False
                error_messages.append("Field 'quantity' should be non-negative")
        
        # If validation failed, return errors
        if not is_valid:
            return message, False, '; '.join(error_messages)
        
        # Enrich the message
        message["total_price"] = round(message["quantity"] * message["price"], 2)
        
        return message, True, "Validated and enriched successfully"
    
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        return message, False, f"Validation error: {str(e)}"

#================================================
# HELPER FOR `process_message` to deserialise UNIX timestamps
def epoch_days_to_date_string(days: int) -> str:
    '''Convert Kafka Date (days since epoch) to YYYY-MM-DD string.
    
    ---

    PARAMETERS:
    - `days` (int): Number of days since epoch (1970-01-01)

    RETURNS:
    - (str): Date string in 'YYYY-MM-DD' format
    '''

    epoch = datetime(1970, 1, 1)
    date_obj = epoch + timedelta(days=days)
    return date_obj.strftime('%Y-%m-%d')

def process_message(message_value:dict, producer:KafkaProducer) -> bool:
    '''
    Process a single message: validate, enrich, and send to appropriate topic.
    
    ---

    PARAMETERS:
    - `message_value` (dict): JSON message as a dictionary object
    - `producer` (KafkaProducer): Kafka producer instance

    RETURNS:
    - (bool): True if message was successfully processed and sent
    '''
    try:
        # Validate and enrich
        enriched_message, is_valid, status_message = validate_and_enrich_message(message_value)

        # Deserialise UNIX timestamp if present
        if str(enriched_message["order_date"]).isdigit():
            enriched_message["order_date"] = epoch_days_to_date_string(int(enriched_message["order_date"]))
        epoch_days_to_date_string

        # Determine target topic
        target_topic = ENRICHED_ORDERS_TOPIC if is_valid else INVALID_ORDERS_TOPIC
        validity_status = "VALID" if is_valid else "INVALID"
                
        # Extract order_id to use as message key for partition distribution
        order_id = message_value.get("order_id", "unknown")
        message_key = str(order_id)
        
        # Log processing result
        logger.info(
            f"{validity_status} Order {order_id}: {status_message} "
            f"-> {target_topic}"
        )
        
        # Send with key for proper partition distribution
        # NOTE: This is not essential here but good practice
        future = producer.send(
            target_topic, 
            key=message_key, # Add key: same order_id -> same partition
            value=enriched_message
        )
        
        # Wait for acknowledgment from Kafka topic partitions
        record_metadata = future.get(timeout=10)
        
        logger.info(
            f"Sent to {record_metadata.topic} "
            f"[partition={record_metadata.partition}, offset={record_metadata.offset}]"
        )

        return True

    except KafkaError as e:
        logger.error(f"Kafka error processing message: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error processing message: {str(e)}", exc_info=True)
        return False

#================================================
def main():
    '''Main processing loop'''

    consumer = None
    producer = None

    try:
        # Log startup information
        logger.info("=" * 48)
        logger.info("ORDER VALIDATOR SERVICE STARTING")
        logger.info("=" * 48)
        logger.info(f"Kafka Bootstrap Servers: {BOOTSTRAP_SERVERS}")
        logger.info(f"Source Topic: {ORDERS_TOPIC}")
        logger.info(f"Valid Orders Topic: {ENRICHED_ORDERS_TOPIC}")
        logger.info(f"Invalid Orders Topic: {INVALID_ORDERS_TOPIC}")
        logger.info(f"Consumer Group: {CONSUMER_GROUP}")
        logger.info("=" * 48)

        # Create Kafka clients
        logger.info("Initializing Kafka consumer and producer...")
        consumer = create_consumer()
        producer = create_producer()

        logger.info("Successfully connected to Kafka")
        logger.info(f"Consuming from topic: {ORDERS_TOPIC}")
        logger.info(f"Consumer group: {CONSUMER_GROUP}")
        logger.info("Ready to process messages...")
        logger.info("=" * 48)

        # Message counter for logging
        messages_processed = 0
        messages_valid = 0
        messages_invalid = 0

        # Message processing loop with manual commit
        while True:
            for message in consumer:
                try:
                    message_value = message.value
                    logger.info(f"MESSAGE_VALUE = {message_value}")

                    messages_processed += 1
                    
                    # Log incoming message
                    logger.info(
                        f"[{messages_processed}] Received message from "
                        f"partition={message.partition} offset={message.offset} "
                        f"order_id={message_value.get('order_id', 'unknown')}"
                    )
                    
                    # Process the message
                    success = process_message(message_value, producer)
                    
                    if success:
                        # Flush producer to ensure message is sent
                        producer.flush()
                        
                        # Commit offset only after successful processing
                        consumer.commit()

                        # Update stats
                        if "total_price" in message_value:
                            messages_valid += 1
                        else:
                            messages_invalid += 1
                        
                        logger.info(
                            f"[{messages_processed}] Committed offset {message.offset} "
                            f"| Stats: Valid={messages_valid} Invalid={messages_invalid}"
                        )
                    else:
                        logger.error(f"[{messages_processed}] Failed to process message at offset {message.offset}")
                        # Do not commit, as message will be reprocessed
                except KeyboardInterrupt:
                    logger.info("Shutdown signal received (Ctrl+C)")
                    return
                except Exception as e:
                    logger.error(f"Error in processing loop: {str(e)}", exc_info=True)
                    # Continue processing other messages
                    continue

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup resources
        logger.info("=" * 48)
        logger.info("SHUTTING DOWN ORDER VALIDATOR")
        logger.info("=" * 48)

        if producer:
            logger.info("Flushing producer...")
            producer.flush()
            producer.close()
            logger.info("Producer closed")

        if consumer:
            logger.info("Closing consumer...")
            consumer.close()
            logger.info("Consumer closed")

        logger.info("=" * 48)
        logger.info("SHUTDOWN COMPLETE")
        logger.info("=" * 48)

#############################################################
# RUNNING THE `main` FUNCTION IF THIS FILE IS RUN DIRECTLY
#############################################################

if __name__ == "__main__":
    main()