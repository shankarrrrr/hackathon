"""
Real-time feature processor that consumes transactions from Kafka
Computes features on-the-fly and triggers predictions
"""

import logging
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaConsumer
import json
import requests
import os
from dotenv import load_dotenv

from .kafka_config import CONSUMER_CONFIG, TOPICS, CONSUMER_GROUPS
from ..feature_engineering.features import BehavioralFeatureEngineering

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealTimeFeatureProcessor:
    """
    Consumes transaction events from Kafka, computes features in real-time,
    and triggers risk predictions via API
    """
    
    def __init__(self, api_url: str = None):
        """
        Initialize the feature processor
        
        Args:
            api_url: URL of the prediction API (default: http://localhost:8000)
        """
        self.api_url = api_url or os.getenv('API_URL', 'http://localhost:8000')
        self.feature_engineer = BehavioralFeatureEngineering()
        
        # Initialize Kafka consumer
        consumer_config = CONSUMER_CONFIG.copy()
        consumer_config['group_id'] = CONSUMER_GROUPS['FEATURE_PROCESSOR']
        consumer_config['value_deserializer'] = lambda m: json.loads(m.decode('utf-8'))
        consumer_config['auto_offset_reset'] = 'latest'  # Start from latest messages
        consumer_config['enable_auto_commit'] = True
        
        self.consumer = KafkaConsumer(
            TOPICS['TRANSACTIONS'],
            **consumer_config
        )
        
        # Track processed customers to avoid duplicate predictions
        self.processed_customers = set()
        self.transaction_count = 0
        
        logger.info(f"RealTimeFeatureProcessor initialized")
        logger.info(f"  Consuming from: {TOPICS['TRANSACTIONS']}")
        logger.info(f"  API endpoint: {self.api_url}")
    
    def process_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Process a single transaction event
        
        Args:
            transaction: Transaction event data
        
        Returns:
            bool: True if processing succeeded
        """
        try:
            customer_id = transaction.get('customer_id')
            
            if not customer_id:
                logger.warning("Transaction missing customer_id")
                return False
            
            self.transaction_count += 1
            
            # Log every 100 transactions
            if self.transaction_count % 100 == 0:
                logger.info(f"Processed {self.transaction_count} transactions")
            
            # Trigger prediction for high-value transactions or specific patterns
            should_predict = self._should_trigger_prediction(transaction)
            
            if should_predict:
                logger.info(f"Triggering prediction for customer: {customer_id}")
                self._trigger_prediction(customer_id)
                self.processed_customers.add(customer_id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return False
    
    def _should_trigger_prediction(self, transaction: Dict[str, Any]) -> bool:
        """
        Determine if this transaction should trigger a risk prediction
        
        Triggers on:
        - Large transactions (>10% of typical amount)
        - Failed transactions
        - ATM withdrawals
        - Every 10th transaction per customer
        - Customers not recently scored
        """
        customer_id = transaction.get('customer_id')
        amount = transaction.get('amount', 0)
        is_failed = transaction.get('is_failed', False)
        category = transaction.get('category', '')
        channel = transaction.get('channel', '')
        
        # Always trigger on failed transactions
        if is_failed:
            logger.debug(f"Trigger: Failed transaction for {customer_id}")
            return True
        
        # Trigger on large transactions (>5000)
        if amount > 5000:
            logger.debug(f"Trigger: Large transaction {amount} for {customer_id}")
            return True
        
        # Trigger on ATM withdrawals
        if channel == 'atm':
            logger.debug(f"Trigger: ATM withdrawal for {customer_id}")
            return True
        
        # Trigger on utility/rent payments (important signals)
        if category in ['utilities', 'rent', 'insurance']:
            logger.debug(f"Trigger: Important payment category {category} for {customer_id}")
            return True
        
        # Trigger every 10th transaction for each customer
        if self.transaction_count % 10 == 0:
            logger.debug(f"Trigger: Periodic check for {customer_id}")
            return True
        
        return False
    
    def _trigger_prediction(self, customer_id: str) -> bool:
        """
        Call the prediction API for a customer
        
        Args:
            customer_id: Customer UUID
        
        Returns:
            bool: True if prediction succeeded
        """
        try:
            response = requests.post(
                f"{self.api_url}/predict",
                json={
                    "customer_id": customer_id,
                    "observation_date": datetime.now().isoformat()
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                risk_score = result.get('risk_score', 0)
                risk_level = result.get('risk_level', 'UNKNOWN')
                
                logger.info(
                    f"  ✅ Prediction: customer={customer_id}, "
                    f"risk_score={risk_score:.4f}, risk_level={risk_level}"
                )
                return True
            else:
                logger.error(
                    f"  ❌ Prediction failed: {response.status_code} - {response.text}"
                )
                return False
        
        except requests.exceptions.Timeout:
            logger.error(f"  ❌ Prediction timeout for {customer_id}")
            return False
        except Exception as e:
            logger.error(f"  ❌ Prediction error: {e}")
            return False
    
    def start(self):
        """Start consuming and processing transactions"""
        logger.info("=" * 60)
        logger.info("REAL-TIME FEATURE PROCESSOR STARTED")
        logger.info("=" * 60)
        logger.info("Waiting for transaction events...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            for message in self.consumer:
                transaction = message.value
                
                logger.debug(
                    f"Received: customer={transaction.get('customer_id')}, "
                    f"amount={transaction.get('amount')}, "
                    f"category={transaction.get('category')}"
                )
                
                self.process_transaction(transaction)
        
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("SHUTTING DOWN")
            logger.info("=" * 60)
            logger.info(f"Total transactions processed: {self.transaction_count}")
            logger.info(f"Unique customers scored: {len(self.processed_customers)}")
        
        finally:
            self.close()
    
    def close(self):
        """Close the consumer"""
        self.consumer.close()
        logger.info("Feature processor closed")


if __name__ == "__main__":
    processor = RealTimeFeatureProcessor()
    processor.start()
