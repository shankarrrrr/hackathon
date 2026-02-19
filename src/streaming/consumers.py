"""
Kafka consumers for processing events
"""

from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from typing import Callable, Dict, Any
from .kafka_config import CONSUMER_CONFIG, TOPICS, CONSUMER_GROUPS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionConsumer:
    """Consumer for transaction events"""
    
    def __init__(self, callback: Callable[[Dict], None]):
        """
        Initialize consumer with callback function
        
        Args:
            callback: Function to process each transaction event
        """
        self.callback = callback
        self.consumer = KafkaConsumer(
            TOPICS['TRANSACTIONS'],
            **CONSUMER_CONFIG,
            group_id=CONSUMER_GROUPS['FEATURE_PROCESSOR'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        logger.info(f"TransactionConsumer initialized for topic: {TOPICS['TRANSACTIONS']}")
    
    def start(self):
        """Start consuming messages"""
        logger.info("Starting transaction consumer...")
        
        try:
            for message in self.consumer:
                try:
                    transaction = message.value
                    logger.debug(f"Received transaction: {transaction.get('customer_id')}")
                    
                    # Process transaction
                    self.callback(transaction)
                
                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.close()
    
    def close(self):
        """Close the consumer"""
        self.consumer.close()
        logger.info("TransactionConsumer closed")


class PredictionConsumer:
    """Consumer for prediction events"""
    
    def __init__(self, callback: Callable[[Dict], None]):
        """
        Initialize consumer with callback function
        
        Args:
            callback: Function to process each prediction event
        """
        self.callback = callback
        self.consumer = KafkaConsumer(
            TOPICS['PREDICTIONS'],
            **CONSUMER_CONFIG,
            group_id=CONSUMER_GROUPS['INTERVENTION_SERVICE'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        logger.info(f"PredictionConsumer initialized for topic: {TOPICS['PREDICTIONS']}")
    
    def start(self):
        """Start consuming messages"""
        logger.info("Starting prediction consumer...")
        
        try:
            for message in self.consumer:
                try:
                    prediction = message.value
                    logger.debug(
                        f"Received prediction: customer={prediction.get('customer_id')}, "
                        f"risk_score={prediction.get('risk_score')}"
                    )
                    
                    # Process prediction
                    self.callback(prediction)
                
                except Exception as e:
                    logger.error(f"Error processing prediction: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.close()
    
    def close(self):
        """Close the consumer"""
        self.consumer.close()
        logger.info("PredictionConsumer closed")


class DashboardConsumer:
    """Consumer for dashboard updates"""
    
    def __init__(self, callback: Callable[[Dict], None]):
        """
        Initialize consumer with callback function
        
        Args:
            callback: Function to process each dashboard update
        """
        self.callback = callback
        self.consumer = KafkaConsumer(
            TOPICS['DASHBOARD_UPDATES'],
            **CONSUMER_CONFIG,
            group_id=CONSUMER_GROUPS['DASHBOARD_SERVICE'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        logger.info(f"DashboardConsumer initialized for topic: {TOPICS['DASHBOARD_UPDATES']}")
    
    def start(self):
        """Start consuming messages"""
        logger.info("Starting dashboard consumer...")
        
        try:
            for message in self.consumer:
                try:
                    update = message.value
                    logger.debug(f"Received dashboard update: {update.get('event_type')}")
                    
                    # Process update
                    self.callback(update)
                
                except Exception as e:
                    logger.error(f"Error processing dashboard update: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        finally:
            self.close()
    
    def close(self):
        """Close the consumer"""
        self.consumer.close()
        logger.info("DashboardConsumer closed")
