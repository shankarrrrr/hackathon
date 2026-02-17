"""
Simple script to check if retraining is needed and execute it
Run this periodically (e.g., daily via cron or scheduler)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.auto_retrain import AutoRetrainer


def main():
    print("="*60)
    print("MODEL RETRAINING CHECK")
    print("="*60)
    
    retrainer = AutoRetrainer()
    
    # Check if retraining needed (threshold: 50 new customers)
    should_retrain, reason = retrainer.should_retrain(new_customer_threshold=50)
    
    if should_retrain:
        print(f"\n🔔 Retraining triggered: {reason}")
        print("   Starting automatic retraining...")
        
        result = retrainer.retrain_model(max_customers=200)
        
        if result['success']:
            print(f"\n✅ SUCCESS!")
            print(f"   Customers trained: {result['customers_trained']}")
            print(f"   Samples: {result['samples_trained']}")
            print(f"   AUC: {result['auc']:.4f}")
            print(f"   Model version: {result['model_version']}")
            print("\n💡 Restart the API to load the new model:")
            print("   python -m uvicorn src.serving.api:app --reload")
        else:
            print("\n❌ Retraining failed")
            return 1
    else:
        print("\n✅ No retraining needed")
        print("   Current model is up to date")
        
        # Show history
        print("\n📊 Recent retraining history:")
        history = retrainer.get_retraining_history(limit=5)
        
        if len(history) > 0:
            for _, row in history.iterrows():
                print(f"   {row['retrain_date']}: {row['customers_trained']} customers, AUC={row['auc_score']:.4f}")
        else:
            print("   No retraining history yet")
    
    print("\n" + "="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
