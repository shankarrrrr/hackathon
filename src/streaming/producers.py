"""
Kafka producers for streaming events
"""

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .kafka_config import PRODUCER_CONFIG, TOPICS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionProducer:
    """Producer for transaction events"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            **PRODUCER_CONFIG,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        self.topic = TOPICS['TRANSACTIONS']
        logger.info(f"TransactionProducer initialized for topic: {self.topic}")
    
    def send_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Send a transaction event to Kafka
        
        Args:
            transaction: Transaction data dict with keys:
                - customer_id
                - txn_time
                - amount
                - txn_type
                - category
                - channel
                - merchant_id
        
        Returns:
            bool: True if sent successfully
        """
        try:
            # Use customer_id as partition key for ordering
            key = transaction.get('customer_id')
            
            # Add metadata
            event = {
                **transaction,
                'event_time': datetime.now().isoformat(),
                'event_type': 'transaction'
            }
            
            # Send to Kafka
            future = self.producer.send(
                self.topic,
                key=key,
                value=event
            )
            
            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"Transaction sent: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, "
                f"offset={record_metadata.offset}"
            )
            
            return True
        
        except KafkaError as e:
            logger.error(f"Failed to send transaction: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending transaction: {e}")
            return False
    
    def send_batch(self, transactions: list) -> int:
        """
        Send multiple transactions in batch
        
        Returns:
            int: Number of successfully sent transactions
        """
        success_count = 0
        
        for txn in transactions:
            if self.send_transaction(txn):
                success_count += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        logger.info(f"Batch sent: {success_count}/{len(transactions)} successful")
        return success_count
    
    def close(self):
        """Close the producer"""
        self.producer.close()
        logger.info("TransactionProducer closed")


class PredictionProducer:
    """Producer for prediction events"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            **PRODUCER_CONFIG,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        self.topic = TOPICS['PREDICTIONS']
        logger.info(f"PredictionProducer initialized for topic: {self.topic}")
    
    def send_prediction(self, prediction: Dict[str, Any]) -> bool:
        """
        Send a prediction event to Kafka
        
        Args:
            prediction: Prediction data dict with keys:
                - customer_id
                - risk_score
                - risk_level
                - top_features
                - timestamp
        
        Returns:
            bool: True if sent successfully
        """
        try:
            key = prediction.get('customer_id')
            
            event = {
                **prediction,
                'event_time': datetime.now().isoformat(),
                'event_type': 'prediction'
            }
            
            future = self.producer.send(
                self.topic,
                key=key,
                value=event
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"Prediction sent: customer={key}, "
                f"risk_score={prediction.get('risk_score'):.4f}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send prediction: {e}")
            return False
    
    def close(self):
        """Close the producer"""
        self.producer.close()
        logger.info("PredictionProducer closed")


class InterventionProducer:
    """Producer for intervention events"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            **PRODUCER_CONFIG,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        self.topic = TOPICS['INTERVENTIONS']
        logger.info(f"InterventionProducer initialized for topic: {self.topic}")
    
    def send_intervention(self, intervention: Dict[str, Any]) -> bool:
        """
        Send an intervention event to Kafka
        
        Args:
            intervention: Intervention data dict with keys:
                - customer_id
                - intervention_type
                - risk_score
                - message
                - timestamp
        
        Returns:
            bool: True if sent successfully
        """
        try:
            key = intervention.get('customer_id')
            
            event = {
                **intervention,
                'event_time': datetime.now().isoformat(),
                'event_type': 'intervention'
            }
            
            future = self.producer.send(
                self.topic,
                key=key,
                value=event
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Intervention sent: customer={key}, "
                f"type={intervention.get('intervention_type')}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send intervention: {e}")
            return False
    
    def close(self):
        """Close the producer"""
        self.producer.close()
        logger.info("InterventionProducer closed")


class DashboardProducer:
    """Producer for dashboard update events"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            **PRODUCER_CONFIG,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        self.topic = TOPICS['DASHBOARD_UPDATES']
        logger.info(f"DashboardProducer initialized for topic: {self.topic}")
    
    def send_update(self, update: Dict[str, Any]) -> bool:
        """
        Send a dashboard update event
        
        Args:
            update: Update data dict
        
        Returns:
            bool: True if sent successfully
        """
        try:
            event = {
                **update,
                'event_time': datetime.now().isoformat()
            }
            
            future = self.producer.send(self.topic, value=event)
            future.get(timeout=10)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send dashboard update: {e}")
            return False
    
    def close(self):
        """Close the producer"""
        self.producer.close()
        logger.info("DashboardProducer closed")
