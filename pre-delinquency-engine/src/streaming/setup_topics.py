"""
Setup Kafka topics with proper configurations
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import logging
from .kafka_config import KAFKA_BOOTSTRAP_SERVERS, TOPIC_CONFIGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_topics():
    """Create all required Kafka topics"""
    
    logger.info(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
    
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            client_id='topic-setup'
        )
        
        logger.info("Connected to Kafka successfully")
        
        # Create topics
        topics_to_create = []
        
        for topic_name, config in TOPIC_CONFIGS.items():
            topic = NewTopic(
                name=topic_name,
                num_partitions=config['num_partitions'],
                replication_factor=config['replication_factor'],
                topic_configs=config.get('config', {})
            )
            topics_to_create.append(topic)
        
        logger.info(f"Creating {len(topics_to_create)} topics...")
        
        try:
            admin_client.create_topics(
                new_topics=topics_to_create,
                validate_only=False
            )
            logger.info("✅ All topics created successfully!")
        
        except TopicAlreadyExistsError:
            logger.info("⚠️ Some topics already exist, skipping...")
        
        # List all topics
        logger.info("\nExisting topics:")
        topics = admin_client.list_topics()
        for topic in sorted(topics):
            logger.info(f"  - {topic}")
        
        admin_client.close()
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to create topics: {e}")
        return False


if __name__ == "__main__":
    create_topics()
