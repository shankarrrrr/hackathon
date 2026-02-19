"""
Simulate real-time transaction stream to Kafka
"""

import time
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv
from .producers import TransactionProducer

load_dotenv()


class TransactionSimulator:
    """Simulate streaming transactions from database to Kafka"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.engine = create_engine(self.db_url)
        self.producer = TransactionProducer()
    
    def stream_historical_transactions(self, limit: int = 1000, delay_ms: int = 100):
        """
        Stream historical transactions from database to Kafka
        
        Args:
            limit: Number of transactions to stream
            delay_ms: Delay between messages in milliseconds
        """
        print(f">> Starting transaction stream (limit={limit}, delay={delay_ms}ms)...")
        
        # Get transactions from database
        query = f"""
        SELECT 
            customer_id,
            txn_time,
            amount,
            txn_type,
            category,
            channel,
            merchant_id
        FROM transactions
        ORDER BY txn_time DESC
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, self.engine)
        print(f"  Loaded {len(df)} transactions from database")
        
        # Stream to Kafka
        success_count = 0
        
        for idx, row in df.iterrows():
            transaction = {
                'customer_id': str(row['customer_id']),
                'txn_time': row['txn_time'].isoformat(),
                'amount': float(row['amount']),
                'txn_type': row['txn_type'],
                'category': row['category'],
                'channel': row['channel'],
                'merchant_id': row['merchant_id']
            }
            
            if self.producer.send_transaction(transaction):
                success_count += 1
            
            if (idx + 1) % 100 == 0:
                print(f"  Progress: {idx + 1}/{len(df)} ({success_count} successful)")
            
            # Delay to simulate real-time stream
            time.sleep(delay_ms / 1000.0)
        
        print(f"\n>> Stream complete: {success_count}/{len(df)} transactions sent")
    
    def stream_live_transactions(self, rate_per_second: int = 10):
        """
        Generate and stream synthetic transactions in real-time
        
        Args:
            rate_per_second: Number of transactions per second
        """
        print(f">> Starting live transaction stream ({rate_per_second} txn/sec)...")
        
        # Get sample customers
        query = "SELECT customer_id FROM customers LIMIT 100"
        customers = pd.read_sql(query, self.engine)['customer_id'].tolist()
        
        categories = ['groceries', 'dining', 'shopping', 'utilities', 'entertainment', 'transport']
        channels = ['pos', 'online', 'atm', 'mobile']
        
        delay = 1.0 / rate_per_second
        count = 0
        
        try:
            while True:
                transaction = {
                    'customer_id': str(random.choice(customers)),
                    'txn_time': datetime.now().isoformat(),
                    'amount': round(random.uniform(10, 500), 2),
                    'txn_type': random.choice(['debit', 'credit']),
                    'category': random.choice(categories),
                    'channel': random.choice(channels),
                    'merchant_id': f'MERCH_{random.randint(1000, 9999)}'
                }
                
                if self.producer.send_transaction(transaction):
                    count += 1
                    if count % 100 == 0:
                        print(f"  Sent {count} transactions...")
                
                time.sleep(delay)
        
        except KeyboardInterrupt:
            print(f"\n>> Stream stopped. Total sent: {count} transactions")
    
    def close(self):
        """Close connections"""
        self.producer.close()
        self.engine.dispose()


if __name__ == "__main__":
    import sys
    
    simulator = TransactionSimulator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # Live streaming mode
        rate = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        simulator.stream_live_transactions(rate_per_second=rate)
    else:
        # Historical streaming mode
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
        delay = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        simulator.stream_historical_transactions(limit=limit, delay_ms=delay)
    
    simulator.close()
