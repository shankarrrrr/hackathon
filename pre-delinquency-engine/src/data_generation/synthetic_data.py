"""
Synthetic Data Generator for Pre-Delinquency Intervention Engine
Generates realistic banking transaction data with behavioral patterns
"""

import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple
import uuid

import pandas as pd
import numpy as np
from faker import Faker
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)


class SyntheticDataGenerator:
    """Generate synthetic banking data with realistic behavioral patterns"""
    
    def __init__(self, n_customers: int = 10000):
        self.n_customers = n_customers
        self.start_date = datetime.now() - timedelta(days=365)
        self.end_date = datetime.now()
        
        # Transaction categories
        self.debit_categories = [
            'groceries', 'utilities', 'rent', 'entertainment', 'shopping',
            'dining', 'transport', 'healthcare', 'education', 'insurance'
        ]
        self.credit_categories = ['salary', 'transfer', 'refund', 'interest']
        
        # Channels
        self.channels = ['atm', 'online', 'mobile', 'branch', 'pos']
        
        # Payment types
        self.payment_types = ['loan_emi', 'credit_card', 'utility_bill', 'insurance']
        
    def generate_customers(self) -> pd.DataFrame:
        """Generate customer master data"""
        print(f"Generating {self.n_customers} customers...")
        
        customers = []
        for _ in range(self.n_customers):
            # Income brackets with realistic distributions
            income_bracket = random.choices(
                ['low', 'medium', 'high', 'very_high'],
                weights=[0.3, 0.4, 0.2, 0.1]
            )[0]
            
            # Income based on bracket
            income_ranges = {
                'low': (20000, 40000),
                'medium': (40000, 80000),
                'high': (80000, 150000),
                'very_high': (150000, 500000)
            }
            monthly_income = random.uniform(*income_ranges[income_bracket])
            
            # Salary day (most common: 1st, 5th, 15th, 25th, 30th)
            salary_day = random.choices(
                [1, 5, 15, 25, 30] + list(range(2, 29)),
                weights=[0.2, 0.15, 0.15, 0.1, 0.1] + [0.01] * 27
            )[0]
            
            # Account age (older accounts are more stable)
            account_age_days = random.randint(30, 3650)
            
            account_type = random.choices(
                ['savings', 'current', 'salary'],
                weights=[0.6, 0.2, 0.2]
            )[0]
            
            customers.append({
                'customer_id': str(uuid.uuid4()),
                'salary_day': salary_day,
                'monthly_income': round(monthly_income, 2),
                'income_bracket': income_bracket,
                'account_age_days': account_age_days,
                'account_type': account_type
            })
        
        return pd.DataFrame(customers)
    
    def generate_transactions(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generate realistic transaction patterns"""
        print("Generating transactions...")
        
        all_transactions = []
        
        for _, customer in customers_df.iterrows():
            customer_id = customer['customer_id']
            monthly_income = customer['monthly_income']
            salary_day = customer['salary_day']
            
            # Determine if customer will become delinquent (20% probability)
            will_default = random.random() < 0.2
            
            # Generate transactions for each month
            current_date = self.start_date
            balance = monthly_income * random.uniform(0.5, 2.0)  # Starting balance
            
            while current_date < self.end_date:
                month_start = current_date
                month_end = min(month_start + timedelta(days=30), self.end_date)
                
                # Salary credit on salary day
                salary_date = month_start.replace(day=min(salary_day, 28))
                if month_start <= salary_date <= month_end:
                    all_transactions.append({
                        'customer_id': customer_id,
                        'txn_time': salary_date + timedelta(hours=random.randint(0, 23)),
                        'amount': monthly_income,
                        'txn_type': 'credit',
                        'category': 'salary',
                        'channel': 'transfer',
                        'merchant_id': f'EMPLOYER_{random.randint(1000, 9999)}',
                        'is_failed': False
                    })
                    balance += monthly_income
                
                # Generate daily transactions
                days_in_month = (month_end - month_start).days
                
                # Spending pattern based on default risk
                if will_default:
                    # Risky behavior: more spending, irregular patterns
                    daily_txn_count = random.randint(3, 8)
                    spending_ratio = random.uniform(1.1, 1.5)  # Overspending
                else:
                    # Healthy behavior: moderate spending
                    daily_txn_count = random.randint(2, 5)
                    spending_ratio = random.uniform(0.7, 0.95)  # Within means
                
                for day in range(days_in_month):
                    txn_date = month_start + timedelta(days=day)
                    
                    for _ in range(daily_txn_count):
                        # Debit transaction
                        category = random.choice(self.debit_categories)
                        
                        # Amount based on category and income
                        amount_ranges = {
                            'groceries': (0.01, 0.05),
                            'utilities': (0.02, 0.08),
                            'rent': (0.25, 0.40),
                            'entertainment': (0.01, 0.10),
                            'shopping': (0.02, 0.15),
                            'dining': (0.01, 0.05),
                            'transport': (0.01, 0.05),
                            'healthcare': (0.02, 0.10),
                            'education': (0.05, 0.20),
                            'insurance': (0.03, 0.10)
                        }
                        
                        amount_ratio = random.uniform(*amount_ranges.get(category, (0.01, 0.10)))
                        amount = monthly_income * amount_ratio * spending_ratio
                        
                        # Failed transactions for risky customers
                        is_failed = will_default and random.random() < 0.05
                        
                        if not is_failed:
                            balance -= amount
                        
                        all_transactions.append({
                            'customer_id': customer_id,
                            'txn_time': txn_date + timedelta(
                                hours=random.randint(6, 23),
                                minutes=random.randint(0, 59)
                            ),
                            'amount': round(amount, 2),
                            'txn_type': 'debit',
                            'category': category,
                            'channel': random.choice(self.channels),
                            'merchant_id': f'{category.upper()}_{random.randint(1000, 9999)}',
                            'is_failed': is_failed
                        })
                
                current_date = month_end
        
        return pd.DataFrame(all_transactions).sort_values('txn_time')
    
    def generate_payments(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Generate payment obligations and history"""
        print("Generating payment records...")
        
        all_payments = []
        
        for _, customer in customers_df.iterrows():
            customer_id = customer['customer_id']
            monthly_income = customer['monthly_income']
            
            # Determine if customer will have payment issues
            will_default = random.random() < 0.2
            
            # Generate monthly payments for past 12 months
            for month_offset in range(12):
                due_date = self.end_date - timedelta(days=30 * month_offset)
                
                # Generate 2-4 payment obligations per month
                for payment_type in random.sample(self.payment_types, k=random.randint(2, 4)):
                    amount_ratios = {
                        'loan_emi': (0.15, 0.30),
                        'credit_card': (0.05, 0.20),
                        'utility_bill': (0.02, 0.05),
                        'insurance': (0.03, 0.08)
                    }
                    
                    amount = monthly_income * random.uniform(*amount_ratios[payment_type])
                    
                    # Payment behavior
                    if will_default and month_offset < 3:  # Recent defaults
                        # High chance of missed/late payments
                        status_choice = random.choices(
                            ['paid', 'late', 'missed', 'partial'],
                            weights=[0.2, 0.3, 0.3, 0.2]
                        )[0]
                    else:
                        # Mostly on-time payments
                        status_choice = random.choices(
                            ['paid', 'late', 'missed'],
                            weights=[0.85, 0.10, 0.05]
                        )[0]
                    
                    # Calculate paid date and amount
                    if status_choice == 'paid':
                        paid_date = due_date + timedelta(days=random.randint(-2, 2))
                        paid_amount = amount
                        days_late = max(0, (paid_date - due_date).days)
                    elif status_choice == 'late':
                        days_late = random.randint(1, 30)
                        paid_date = due_date + timedelta(days=days_late)
                        paid_amount = amount
                    elif status_choice == 'partial':
                        paid_date = due_date + timedelta(days=random.randint(0, 15))
                        paid_amount = amount * random.uniform(0.3, 0.8)
                        days_late = max(0, (paid_date - due_date).days)
                    else:  # missed
                        paid_date = None
                        paid_amount = None
                        days_late = (datetime.now().date() - due_date).days
                    
                    all_payments.append({
                        'payment_id': str(uuid.uuid4()),
                        'customer_id': customer_id,
                        'payment_type': payment_type,
                        'due_date': due_date,
                        'amount': round(amount, 2),
                        'paid_date': paid_date,
                        'paid_amount': round(paid_amount, 2) if paid_amount else None,
                        'status': status_choice,
                        'days_late': days_late
                    })
        
        return pd.DataFrame(all_payments)
    
    def generate_labels(self, customers_df: pd.DataFrame, payments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate labels for ML training"""
        print("Generating labels...")
        
        labels = []
        
        for _, customer in customers_df.iterrows():
            customer_id = customer['customer_id']
            
            # Get customer's payment history
            customer_payments = payments_df[payments_df['customer_id'] == customer_id]
            
            # Check for defaults in next 14-30 days window
            recent_payments = customer_payments[
                customer_payments['due_date'] >= (self.end_date - timedelta(days=30))
            ]
            
            # Label as 1 if any missed/late payments in the window
            has_default = any(
                recent_payments['status'].isin(['missed', 'late']) &
                (recent_payments['days_late'] > 7)
            )
            
            if has_default:
                default_payment = recent_payments[
                    recent_payments['status'].isin(['missed', 'late'])
                ].iloc[0]
                default_date = default_payment['due_date']
                days_to_default = (default_date - (self.end_date - timedelta(days=30))).days
                default_amount = default_payment['amount']
            else:
                default_date = None
                days_to_default = None
                default_amount = None
            
            labels.append({
                'customer_id': customer_id,
                'observation_date': self.end_date - timedelta(days=30),
                'label': 1 if has_default else 0,
                'days_to_default': days_to_default,
                'default_date': default_date,
                'default_amount': default_amount
            })
        
        return pd.DataFrame(labels)
    
    def save_to_database(self, customers_df, transactions_df, payments_df, labels_df):
        """Save generated data to PostgreSQL"""
        print("Connecting to database...")
        
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        try:
            # Insert customers
            print(f"Inserting {len(customers_df)} customers...")
            customer_records = customers_df.to_dict('records')
            execute_batch(
                cur,
                """
                INSERT INTO customers (customer_id, salary_day, monthly_income, income_bracket, 
                                     account_age_days, account_type)
                VALUES (%(customer_id)s, %(salary_day)s, %(monthly_income)s, %(income_bracket)s,
                       %(account_age_days)s, %(account_type)s)
                ON CONFLICT (customer_id) DO NOTHING
                """,
                customer_records
            )
            
            # Insert transactions
            print(f"Inserting {len(transactions_df)} transactions...")
            txn_records = transactions_df.to_dict('records')
            execute_batch(
                cur,
                """
                INSERT INTO transactions (customer_id, txn_time, amount, txn_type, category,
                                        channel, merchant_id, is_failed)
                VALUES (%(customer_id)s, %(txn_time)s, %(amount)s, %(txn_type)s, %(category)s,
                       %(channel)s, %(merchant_id)s, %(is_failed)s)
                """,
                txn_records,
                page_size=1000
            )
            
            # Insert payments
            print(f"Inserting {len(payments_df)} payments...")
            payment_records = payments_df.to_dict('records')
            execute_batch(
                cur,
                """
                INSERT INTO payments (payment_id, customer_id, payment_type, due_date, amount,
                                    paid_date, paid_amount, status, days_late)
                VALUES (%(payment_id)s, %(customer_id)s, %(payment_type)s, %(due_date)s, %(amount)s,
                       %(paid_date)s, %(paid_amount)s, %(status)s, %(days_late)s)
                ON CONFLICT (payment_id) DO NOTHING
                """,
                payment_records
            )
            
            # Insert labels
            print(f"Inserting {len(labels_df)} labels...")
            label_records = labels_df.to_dict('records')
            execute_batch(
                cur,
                """
                INSERT INTO labels (customer_id, observation_date, label, days_to_default,
                                  default_date, default_amount)
                VALUES (%(customer_id)s, %(observation_date)s, %(label)s, %(days_to_default)s,
                       %(default_date)s, %(default_amount)s)
                ON CONFLICT (customer_id, observation_date) DO NOTHING
                """,
                label_records
            )
            
            conn.commit()
            print("✅ Data successfully saved to database!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error saving to database: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def save_to_csv(self, customers_df, transactions_df, payments_df, labels_df):
        """Save generated data to CSV files"""
        print("Saving to CSV files...")
        
        os.makedirs('data/raw', exist_ok=True)
        
        customers_df.to_csv('data/raw/customers.csv', index=False)
        transactions_df.to_csv('data/raw/transactions.csv', index=False)
        payments_df.to_csv('data/raw/payments.csv', index=False)
        labels_df.to_csv('data/raw/labels.csv', index=False)
        
        print("✅ CSV files saved to data/raw/")
    
    def generate_all(self, save_to_db: bool = True, save_to_csv: bool = True):
        """Generate all synthetic data"""
        print("=" * 60)
        print("SYNTHETIC DATA GENERATION")
        print("=" * 60)
        
        # Generate data
        customers_df = self.generate_customers()
        transactions_df = self.generate_transactions(customers_df)
        payments_df = self.generate_payments(customers_df)
        labels_df = self.generate_labels(customers_df, payments_df)
        
        # Print statistics
        print("\n" + "=" * 60)
        print("GENERATION SUMMARY")
        print("=" * 60)
        print(f"Customers: {len(customers_df):,}")
        print(f"Transactions: {len(transactions_df):,}")
        print(f"Payments: {len(payments_df):,}")
        print(f"Labels: {len(labels_df):,}")
        print(f"Default rate: {labels_df['label'].mean():.1%}")
        print("=" * 60)
        
        # Save data
        if save_to_csv:
            self.save_to_csv(customers_df, transactions_df, payments_df, labels_df)
        
        if save_to_db:
            self.save_to_database(customers_df, transactions_df, payments_df, labels_df)
        
        return customers_df, transactions_df, payments_df, labels_df


def main():
    """Main execution"""
    generator = SyntheticDataGenerator(n_customers=10000)
    generator.generate_all(save_to_db=True, save_to_csv=True)


if __name__ == "__main__":
    main()
