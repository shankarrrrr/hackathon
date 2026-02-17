"""
Quick test script for retraining functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.models.auto_retrain import AutoRetrainer
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def test_retraining():
    """Test the retraining system"""
    
    print("="*60)
    print("TESTING RETRAINING SYSTEM")
    print("="*60)
    
    try:
        # Initialize retrainer
        print("\n1️⃣ Initializing retrainer...")
        retrainer = AutoRetrainer()
        print("   ✅ Retrainer initialized")
        
        # Check tables exist
        print("\n2️⃣ Checking database tables...")
        engine = create_engine(os.getenv('DATABASE_URL'))
        
        with engine.connect() as conn:
            # Check model_retraining_log
            result = conn.execute(text("SELECT COUNT(*) FROM model_retraining_log"))
            log_count = result.scalar()
            print(f"   ✅ model_retraining_log exists ({log_count} records)")
            
            # Check customer_training_status
            result = conn.execute(text("SELECT COUNT(*) FROM customer_training_status"))
            status_count = result.scalar()
            print(f"   ✅ customer_training_status exists ({status_count} records)")
        
        # Check new customers
        print("\n3️⃣ Checking new customers...")
        new_count = retrainer.check_new_customers()
        print(f"   📊 New customers not in training: {new_count}")
        
        # Check if retraining needed
        print("\n4️⃣ Checking retraining threshold...")
        should_retrain, reason = retrainer.should_retrain(new_customer_threshold=50)
        
        if should_retrain:
            print(f"   ✅ Retraining needed: {reason}")
            print("\n   💡 To trigger retraining, run:")
            print("      python check_and_retrain.py")
        else:
            print(f"   ℹ️ Retraining not needed yet")
            print(f"   📊 Need {50 - new_count} more customers to reach threshold")
        
        # Show history
        print("\n5️⃣ Checking retraining history...")
        history = retrainer.get_retraining_history(limit=5)
        
        if len(history) > 0:
            print(f"   📊 Found {len(history)} retraining events:")
            for _, row in history.iterrows():
                print(f"      • {row['retrain_date']}: {row['customers_trained']} customers, AUC={row['auc_score']:.4f}")
        else:
            print("   ℹ️ No retraining history yet (this is normal for first run)")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        
        print("\n📝 Next Steps:")
        print("   1. Run: python check_and_retrain.py")
        print("   2. Or check via API: curl http://localhost:8000/retraining/status")
        print("   3. View docs: cat RETRAINING.md")
        
        return True
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_retraining()
    sys.exit(0 if success else 1)
