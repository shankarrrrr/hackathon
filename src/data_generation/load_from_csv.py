"""
Fast CSV to Database Loader using PostgreSQL COPY
Loads existing CSV files into database much faster than INSERT
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def load_csv_to_db():
    """Load CSV files to database using fast COPY command"""
    
    print("Connecting to database...")
    conn = psycopg2.connect(
        os.getenv('DATABASE_URL'),
        connect_timeout=10
    )
    conn.set_session(autocommit=False)
    cur = conn.cursor()
    
    try:
        # Clear existing data first
        print("Clearing existing data...")
        cur.execute("TRUNCATE TABLE labels, payments, transactions, customers CASCADE")
        conn.commit()
        print("✅ Tables cleared\n")
        
        print("Loading customers...")
        with open('data/raw/customers.csv', 'r') as f:
            cur.copy_expert(
                """
                COPY customers (customer_id, salary_day, monthly_income, income_bracket, 
                              account_age_days, account_type)
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
                """,
                f
            )
        print(f"✅ Customers loaded")
        
        print("Loading transactions (this will be much faster)...")
        with open('data/raw/transactions.csv', 'r') as f:
            cur.copy_expert(
                """
                COPY transactions (customer_id, txn_time, amount, txn_type, category,
                                 channel, merchant_id, is_failed)
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
                """,
                f
            )
        print(f"✅ Transactions loaded")
        
        print("Loading payments...")
        with open('data/raw/payments.csv', 'r') as f:
            cur.copy_expert(
                """
                COPY payments (payment_id, customer_id, payment_type, due_date, amount,
                             paid_date, paid_amount, status, days_late)
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
                """,
                f
            )
        print(f"✅ Payments loaded")
        
        print("Loading labels...")
        with open('data/raw/labels.csv', 'r') as f:
            cur.copy_expert(
                """
                COPY labels (customer_id, observation_date, label, days_to_default,
                           default_date, default_amount)
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
                """,
                f
            )
        print(f"✅ Labels loaded")
        
        conn.commit()
        print("\n✅ All data loaded successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load_csv_to_db()
