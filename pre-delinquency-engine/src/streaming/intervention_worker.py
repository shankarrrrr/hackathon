"""
Intervention worker that consumes predictions and triggers interventions
"""

import logging
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaConsumer
import json
from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

from .kafka_config import CONSUMER_CONFIG, TOPICS, CONSUMER_GROUPS
from .producers import InterventionProducer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterventionWorker:
    """
    Consumes prediction events and triggers appropriate interventions
    based on risk levels
    """
    
    def __init__(self):
        """Initialize the intervention worker"""
        
        # Initialize Kafka consumer
        consumer_config = CONSUMER_CONFIG.copy()
        consumer_config['group_id'] = CONSUMER_GROUPS['INTERVENTION_SERVICE']
        consumer_config['value_deserializer'] = lambda m: json.loads(m.decode('utf-8'))
        consumer_config['auto_offset_reset'] = 'latest'
        consumer_config['enable_auto_commit'] = True
        
        self.consumer = KafkaConsumer(
            TOPICS['PREDICTIONS'],
            **consumer_config
        )
        
        # Initialize intervention producer
        self.intervention_producer = InterventionProducer()
        
        # Database connection for storing interventions
        self.db_engine = create_engine(os.getenv('DATABASE_URL'))
        
        # Intervention thresholds
        self.thresholds = {
            'CRITICAL': 0.7,
            'HIGH': 0.5,
            'MEDIUM': 0.3
        }
        
        # Intervention strategies
        self.intervention_strategies = {
            'CRITICAL': {
                'type': 'urgent_outreach',
                'message': 'Urgent: High risk of payment default detected. Please contact us immediately.',
                'channel': 'phone_call',
                'priority': 1
            },
            'HIGH': {
                'type': 'proactive_support',
                'message': 'We noticed changes in your account activity. Would you like to discuss payment options?',
                'channel': 'sms',
                'priority': 2
            },
            'MEDIUM': {
                'type': 'gentle_reminder',
                'message': 'Reminder: Upcoming payments due. Let us know if you need assistance.',
                'channel': 'email',
                'priority': 3
            }
        }
        
        self.intervention_count = 0
        
        logger.info("InterventionWorker initialized")
        logger.info(f"  Consuming from: {TOPICS['PREDICTIONS']}")
        logger.info(f"  Publishing to: {TOPICS['INTERVENTIONS']}")
    
    def process_prediction(self, prediction: Dict[str, Any]) -> bool:
        """
        Process a prediction event and trigger intervention if needed
        
        Args:
            prediction: Prediction event data
        
        Returns:
            bool: True if processing succeeded
        """
        try:
            customer_id = prediction.get('customer_id')
            risk_score = prediction.get('risk_score', 0)
            risk_level = prediction.get('risk_level', 'LOW')
            
            logger.info(
                f"Processing prediction: customer={customer_id}, "
                f"risk_score={risk_score:.4f}, risk_level={risk_level}"
            )
            
            # Trigger intervention for HIGH and CRITICAL risks
            if risk_level in ['HIGH', 'CRITICAL']:
                self._trigger_intervention(prediction)
                self.intervention_count += 1
            else:
                logger.debug(f"  No intervention needed for {risk_level} risk")
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing prediction: {e}")
            return False
    
    def _trigger_intervention(self, prediction: Dict[str, Any]) -> bool:
        """
        Trigger an intervention based on risk level
        
        Args:
            prediction: Prediction data
        
        Returns:
            bool: True if intervention triggered successfully
        """
        try:
            customer_id = prediction.get('customer_id')
            risk_score = prediction.get('risk_score')
            risk_level = prediction.get('risk_level')
            top_features = prediction.get('top_features', [])
            
            # Get intervention strategy
            strategy = self.intervention_strategies.get(risk_level)
            
            if not strategy:
                logger.warning(f"No strategy defined for risk level: {risk_level}")
                return False
            
            # Create intervention event
            intervention = {
                'intervention_id': f"INT_{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'customer_id': customer_id,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'intervention_type': strategy['type'],
                'message': strategy['message'],
                'channel': strategy['channel'],
                'priority': strategy['priority'],
                'top_risk_factors': [f['feature'] for f in top_features[:3]],
                'timestamp': datetime.now().isoformat(),
                'status': 'triggered'
            }
            
            # Publish to Kafka
            success = self.intervention_producer.send_intervention(intervention)
            
            if success:
                logger.info(
                    f"  ✅ Intervention triggered: type={strategy['type']}, "
                    f"channel={strategy['channel']}, priority={strategy['priority']}"
                )
                
                # Store in database
                self._store_intervention(intervention)
            else:
                logger.error(f"  ❌ Failed to publish intervention")
            
            return success
        
        except Exception as e:
            logger.error(f"Error triggering intervention: {e}")
            return False
    
    def _store_intervention(self, intervention: Dict[str, Any]):
        """Store intervention in database for tracking"""
        try:
            # Create interventions table if not exists
            with self.db_engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS interventions (
                        intervention_id VARCHAR(255) PRIMARY KEY,
                        customer_id VARCHAR(255) NOT NULL,
                        risk_score FLOAT,
                        risk_level VARCHAR(50),
                        intervention_type VARCHAR(100),
                        message TEXT,
                        channel VARCHAR(50),
                        priority INTEGER,
                        timestamp TIMESTAMP,
                        status VARCHAR(50),
                        outcome VARCHAR(50),
                        outcome_date TIMESTAMP
                    )
                """))
                conn.commit()
            
            # Insert intervention
            df = pd.DataFrame([{
                'intervention_id': intervention['intervention_id'],
                'customer_id': intervention['customer_id'],
                'risk_score': intervention['risk_score'],
                'risk_level': intervention['risk_level'],
                'intervention_type': intervention['intervention_type'],
                'message': intervention['message'],
                'channel': intervention['channel'],
                'priority': intervention['priority'],
                'timestamp': intervention['timestamp'],
                'status': intervention['status'],
                'outcome': None,
                'outcome_date': None
            }])
            
            df.to_sql('interventions', self.db_engine, if_exists='append', index=False)
            logger.debug(f"  Intervention stored in database")
        
        except Exception as e:
            logger.error(f"Failed to store intervention: {e}")
    
    def start(self):
        """Start consuming and processing predictions"""
        logger.info("=" * 60)
        logger.info("INTERVENTION WORKER STARTED")
        logger.info("=" * 60)
        logger.info("Waiting for prediction events...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            for message in self.consumer:
                prediction = message.value
                self.process_prediction(prediction)
        
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("SHUTTING DOWN")
            logger.info("=" * 60)
            logger.info(f"Total interventions triggered: {self.intervention_count}")
        
        finally:
            self.close()
    
    def close(self):
        """Close connections"""
        self.consumer.close()
        self.intervention_producer.close()
        self.db_engine.dispose()
        logger.info("Intervention worker closed")


if __name__ == "__main__":
    worker = InterventionWorker()
    worker.start()
