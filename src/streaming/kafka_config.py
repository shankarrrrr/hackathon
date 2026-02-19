"""
Kafka configuration and topic definitions
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Kafka connection settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_CLIENT_ID = 'delinquency-engine'

# Topic names
TOPICS = {
    'TRANSACTIONS': 'transactions-stream',
    'PREDICTIONS': 'predictions-stream',
    'INTERVENTIONS': 'interventions-stream',
    'CUSTOMER_UPDATES': 'customer-updates',
    'DASHBOARD_UPDATES': 'dashboard-updates',
}

# Topic configurations
TOPIC_CONFIGS = {
    'transactions-stream': {
        'num_partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': 604800000,  # 7 days
            'cleanup.policy': 'delete',
        }
    },
    'predictions-stream': {
        'num_partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': 2592000000,  # 30 days
            'cleanup.policy': 'delete',
        }
    },
    'interventions-stream': {
        'num_partitions': 2,
        'replication_factor': 1,
        'config': {
            'retention.ms': 7776000000,  # 90 days
            'cleanup.policy': 'delete',
        }
    },
    'customer-updates': {
        'num_partitions': 2,
        'replication_factor': 1,
        'config': {
            'retention.ms': 2592000000,  # 30 days
            'cleanup.policy': 'compact',
        }
    },
    'dashboard-updates': {
        'num_partitions': 1,
        'replication_factor': 1,
        'config': {
            'retention.ms': 86400000,  # 1 day
            'cleanup.policy': 'delete',
        }
    },
}

# Consumer group IDs
CONSUMER_GROUPS = {
    'PREDICTION_SERVICE': 'prediction-service-group',
    'INTERVENTION_SERVICE': 'intervention-service-group',
    'DASHBOARD_SERVICE': 'dashboard-service-group',
    'FEATURE_PROCESSOR': 'feature-processor-group',
}

# Producer configurations
PRODUCER_CONFIG = {
    'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
    'client_id': KAFKA_CLIENT_ID,
    'acks': 'all',
    'retries': 3,
    'max_in_flight_requests_per_connection': 5,
    'compression_type': 'gzip',  # Changed from snappy to gzip (no extra library needed)
}

# Consumer configurations
CONSUMER_CONFIG = {
    'bootstrap_servers': KAFKA_BOOTSTRAP_SERVERS,
    'client_id': KAFKA_CLIENT_ID,
    'auto_offset_reset': 'earliest',
    'enable_auto_commit': True,
    'auto_commit_interval_ms': 5000,
    'session_timeout_ms': 30000,
    'max_poll_records': 500,
}
